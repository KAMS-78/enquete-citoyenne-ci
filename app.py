# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, Respondent, RespondentActivity, Problem, generate_token
from config import Config
from questionnaire_data import ACTIVITIES, COMMUNES, AGE_RANGES, EDUCATION_LEVELS, FREQUENCIES
from datetime import datetime
from functools import wraps
from collections import Counter

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


# ============================================
# DECORATEUR : PROTECTION DE L'ESPACE ADMIN
# ============================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ROUTES PUBLIQUES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/questionnaire')
def questionnaire():
    return render_template(
        'questionnaire.html',
        activities=ACTIVITIES,
        communes=COMMUNES,
        age_ranges=AGE_RANGES,
        education_levels=EDUCATION_LEVELS,
        frequencies=FREQUENCIES
    )


@app.route('/api/start', methods=['POST'])
def start_questionnaire():
    respondent = Respondent(token=generate_token())
    db.session.add(respondent)
    db.session.commit()

    resume_url = f"{request.host_url}questionnaire?token={respondent.token}"

    return jsonify({
        'token': respondent.token,
        'resume_url': resume_url
    })


@app.route('/api/save', methods=['POST'])
def save_response():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'error': 'Jeton manquant'}), 400

    respondent = Respondent.query.filter_by(token=token).first()
    if not respondent:
        return jsonify({'error': 'Jeton invalide'}), 404

    step = data.get('step')
    answers = data.get('answers', {})

    if step == 'profil':
        respondent.age = answers.get('age')
        respondent.commune = answers.get('commune')
        respondent.education = answers.get('education')
        respondent.smartphone = answers.get('smartphone') == 'oui'
        respondent.started = True

        RespondentActivity.query.filter_by(respondent_id=respondent.id).delete()
        for activity in answers.get('activities', []):
            db.session.add(RespondentActivity(
                respondent_id=respondent.id,
                activity=activity
            ))

    elif step == 'probleme':
        problem = Problem.query.filter_by(respondent_id=respondent.id).first()
        if not problem:
            problem = Problem(respondent_id=respondent.id)
            db.session.add(problem)

        problem.description = answers.get('description')
        problem.situation = answers.get('situation')
        problem.current_solution = answers.get('current_solution')

    elif step == 'importance':
        problem = Problem.query.filter_by(respondent_id=respondent.id).first()
        if problem:
            problem.frequency = answers.get('frequency')
            problem.severity = int(answers.get('severity', 3))

    elif step == 'complete':
        respondent.completed = True

    db.session.commit()
    return jsonify({'success': True, 'completed': respondent.completed})


@app.route('/api/resume')
def resume_questionnaire():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Jeton manquant'}), 400

    respondent = Respondent.query.filter_by(token=token).first()
    if not respondent:
        return jsonify({'error': 'Questionnaire introuvable'}), 404

    data = {
        'token': respondent.token,
        'completed': respondent.completed,
        'profil': {
            'age': respondent.age,
            'commune': respondent.commune,
            'education': respondent.education,
            'smartphone': 'oui' if respondent.smartphone else 'non',
            'activities': [a.activity for a in respondent.activities]
        }
    }

    problem = Problem.query.filter_by(respondent_id=respondent.id).first()
    if problem:
        data['probleme'] = {
            'description': problem.description,
            'situation': problem.situation,
            'current_solution': problem.current_solution,
            'frequency': problem.frequency,
            'severity': problem.severity
        }

    if not respondent.started:
        data['current_step'] = 'profil'
    elif not problem or not problem.description:
        data['current_step'] = 'probleme'
    elif not problem.frequency:
        data['current_step'] = 'importance'
    else:
        data['current_step'] = 'complete'

    return jsonify(data)


@app.route('/merci')
def merci():
    return render_template('merci.html')


# ============================================
# ESPACE ADMINISTRATEUR - ROOT SPACE
# ============================================

ADMIN_PATH = app.config['ADMIN_URL_PATH']
ADMIN_PASSWORD = app.config['ADMIN_PASSWORD']

PROBLEM_LABELS = {
    'embouteillages': 'Embouteillages',
    'cout_transport': 'Cout du transport',
    'routes_mauvaises': 'Routes en mauvais etat',
    'manque_argent': 'Manque d argent',
    'chomage': 'Chomage',
    'prix_hausse': 'Hausse des prix',
    'sante_couteuse': 'Sante couteuse',
    'pas_medecin': 'Pas de medecin',
    'medicaments': 'Medicaments chers',
    'administration': 'Administration complexe',
    'coupures_electricite': 'Coupures d electricite',
    'coupures_eau': 'Coupures d eau',
    'internet_lent': 'Internet lent',
    'services_publics': 'Services publics',
    'frais_scolarite': 'Frais de scolarite',
    'ecole_loin': 'Ecole eloignee',
    'temps_famille': 'Manque de temps famille',
    'vendre_produits': 'Difficulte a vendre',
    'acces_marche': 'Pas d acces au marche',
    'prix_instables': 'Prix instables',
}

SOLUTION_LABELS = {
    'aide_famille': 'Aide de la famille',
    'aide_connaissance': 'Aide d une connaissance',
    'payer_aide': 'Payer quelqu un',
    'payer_plus_cher': 'Payer plus cher',
    'debrouille': 'Se debrouiller',
    'attendre': 'Attendre',
    'alternative': 'Trouver une alternative',
    'subir': 'Subir',
    'abandonner': 'Abandonner',
    'ne_sais_pas': 'Ne pas savoir',
    'recherche_internet': 'Recherche Internet',
    'demander_plusieurs': 'Demander a plusieurs',
    'essayer_plusieurs': 'Essayer plusieurs choses',
    'arreter': 'Arreter',
    'changer_projets': 'Changer ses projets',
}

ACTIVITY_LABELS = {a['id']: a['label'] for a in ACTIVITIES}


@app.route(f'/{ADMIN_PATH}', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Mot de passe incorrect.'

    return render_template('admin_login.html', error=error)


@app.route(f'/{ADMIN_PATH}/dashboard')
@admin_required
def admin_dashboard():
    filter_commune = request.args.get('commune', '')
    filter_age = request.args.get('age', '')
    filter_education = request.args.get('education', '')

        # Requête de base sans filtre "completed" (pour Pages ouvertes)
    base_query = Respondent.query
    if filter_commune:
        base_query = base_query.filter_by(commune=filter_commune)
    if filter_age:
        base_query = base_query.filter_by(age=filter_age)
    if filter_education:
        base_query = base_query.filter_by(education=filter_education)

    total_respondents = base_query.count()

    # Comptage des "commencés" avec les mêmes filtres
    started_query = Respondent.query.filter_by(started=True)
    if filter_commune:
        started_query = started_query.filter_by(commune=filter_commune)
    if filter_age:
        started_query = started_query.filter_by(age=filter_age)
    if filter_education:
        started_query = started_query.filter_by(education=filter_education)

    total_started = started_query.count()

    # Comptage des "complétés" avec les mêmes filtres
    completed_query = Respondent.query.filter_by(completed=True)
    if filter_commune:
        completed_query = completed_query.filter_by(commune=filter_commune)
    if filter_age:
        completed_query = completed_query.filter_by(age=filter_age)
    if filter_education:
        completed_query = completed_query.filter_by(education=filter_education)

    respondents = completed_query.all()
    total_completed = len(respondents)
    completion_rate = round((total_completed / total_started * 100), 1) if total_started > 0 else 0
    
    ages = Counter([r.age for r in respondents if r.age])
    communes = Counter([r.commune for r in respondents if r.commune])
    educations = Counter([r.education for r in respondents if r.education])

    all_activities = []
    for r in respondents:
        all_activities.extend([a.activity for a in r.activities])
    activities_counter = Counter(all_activities)

    problems_counter = Counter()
    solutions_counter = Counter()
    severity_values = []
    frequency_values = []

    for r in respondents:
        problem = Problem.query.filter_by(respondent_id=r.id).first()
        if problem:
            if problem.description:
                parts = problem.description.split(' | Autre : ')
                codes_part = parts[0] if len(parts) > 0 else ''
                codes = [c.strip() for c in codes_part.split(',') if c.strip()]
                for code in codes:
                    problems_counter[code] += 1

            if problem.current_solution:
                parts = problem.current_solution.split(' | Autre : ')
                codes_part = parts[0] if len(parts) > 0 else ''
                codes = [c.strip() for c in codes_part.split(',') if c.strip()]
                for code in codes:
                    solutions_counter[code] += 1

            if problem.severity:
                severity_values.append(problem.severity)
            if problem.frequency:
                frequency_values.append(problem.frequency)

    avg_severity = round(sum(severity_values) / len(severity_values), 2) if severity_values else 0
    frequency_counter = Counter(frequency_values)

    def safe_percent(count, total):
        if total <= 0:
            return 0
        return round(count * 100 / total, 1)

    top_problems = []
    for code, count in problems_counter.most_common(10):
        top_problems.append({
            'code': code,
            'label': PROBLEM_LABELS.get(code, code),
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    top_solutions = []
    for code, count in solutions_counter.most_common(10):
        top_solutions.append({
            'code': code,
            'label': SOLUTION_LABELS.get(code, code),
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    ages_data = []
    for age, count in ages.most_common():
        ages_data.append({
            'label': age + ' ans',
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    educations_data = []
    for edu, count in educations.most_common():
        educations_data.append({
            'label': edu,
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    communes_data = []
    for commune, count in communes.most_common(10):
        communes_data.append({
            'label': commune,
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    activities_data = []
    for activity, count in activities_counter.most_common():
        activities_data.append({
            'label': ACTIVITY_LABELS.get(activity, activity),
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    frequencies_data = []
    for freq, count in frequency_counter.most_common():
        frequencies_data.append({
            'label': freq,
            'count': count,
            'percent': safe_percent(count, total_completed)
        })

    free_problems = []
    for r in respondents:
        problem = Problem.query.filter_by(respondent_id=r.id).first()
        if problem and problem.description:
            parts = problem.description.split(' | Autre : ')
            if len(parts) > 1 and parts[1].strip():
                free_problems.append({
                    'commune': r.commune or 'Non precise',
                    'age': r.age or '?',
                    'text': parts[1].strip()
                })

    free_solutions = []
    for r in respondents:
        problem = Problem.query.filter_by(respondent_id=r.id).first()
        if problem and problem.current_solution:
            parts = problem.current_solution.split(' | Autre : ')
            if len(parts) > 1 and parts[1].strip():
                free_solutions.append({
                    'commune': r.commune or 'Non precise',
                    'age': r.age or '?',
                    'text': parts[1].strip()
                })

    free_situations = []
    for r in respondents:
        problem = Problem.query.filter_by(respondent_id=r.id).first()
        if problem and problem.situation:
            free_situations.append({
                'commune': r.commune or 'Non precise',
                'age': r.age or '?',
                'text': problem.situation
            })

    return render_template(
        'admin_dashboard.html',
        total_respondents=total_respondents,
        total_started=total_started,
        total_completed=total_completed,
        completion_rate=completion_rate,
        avg_severity=avg_severity,
        top_problems=top_problems,
        top_solutions=top_solutions,
        ages_data=ages_data,
        educations_data=educations_data,
        communes_data=communes_data,
        activities_data=activities_data,
        frequencies_data=frequencies_data,
        free_problems=free_problems,
        free_solutions=free_solutions,
        free_situations=free_situations,
        filter_commune=filter_commune,
        filter_age=filter_age,
        filter_education=filter_education,
        all_communes=COMMUNES,
        all_ages=AGE_RANGES,
        all_educations=EDUCATION_LEVELS
    )


@app.route(f'/{ADMIN_PATH}/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)