// ============================================
// GESTION DU THÈME (sombre par défaut)
// ============================================

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
}

document.addEventListener('DOMContentLoaded', function() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(currentTheme);
});

// ============================================
// ZONE "EN SAVOIR PLUS"
// ============================================

function toggleLearnMore() {
    const learnMore = document.getElementById('learn-more');
    const arrow = document.getElementById('learn-more-arrow');
    const text = document.getElementById('learn-more-text');
    
    if (!learnMore) return;
    
    learnMore.classList.toggle('open');
    if (arrow) arrow.classList.toggle('open');
    
    if (text) {
        text.textContent = learnMore.classList.contains('open') 
            ? 'Masquer les détails' 
            : 'En savoir plus';
    }
}

// ============================================
// TRANSITION ENTRE ÉTAPES DU QUESTIONNAIRE
// ============================================

// Délai en millisecondes entre chaque étape.
const TRANSITION_DELAY = 2000;

function showTransitionOverlay(message, callback) {
    let overlay = document.getElementById('transition-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'transition-overlay';
        overlay.className = 'transition-overlay';
        overlay.innerHTML = `
            <div class="transition-spinner"></div>
            <div class="transition-text">${message}</div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.transition-text').textContent = message;
    }
    
    overlay.classList.add('active');
    
    setTimeout(() => {
        if (callback) callback();
        setTimeout(() => {
            overlay.classList.remove('active');
        }, 300);
    }, TRANSITION_DELAY);
}

// ============================================
// GESTION DU QUESTIONNAIRE
// ============================================

let currentStep = 'profil';
let respondentToken = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('step-profil')) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        respondentToken = token;
        loadResumeData(token);
    } else {
        startNewQuestionnaire();
    }
});

async function startNewQuestionnaire() {
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();
        respondentToken = data.token;
        showResumeLink(data.resume_url);
        showStep('profil');
        updateProgress(0);
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue. Veuillez réessayer.');
    }
}

async function loadResumeData(token) {
    try {
        const response = await fetch('/api/resume?token=' + token);
        const data = await response.json();
        
        if (data.completed) {
            window.location.href = '/merci';
            return;
        }
        
        if (data.profil) {
            document.getElementById('age').value = data.profil.age || '';
            document.getElementById('commune').value = data.profil.commune || '';
            document.getElementById('education').value = data.profil.education || '';
            
            if (data.profil.smartphone === 'oui') {
                document.querySelector('input[name="smartphone"][value="oui"]').checked = true;
            } else if (data.profil.smartphone === 'non') {
                document.querySelector('input[name="smartphone"][value="non"]').checked = true;
            }
            
            document.querySelectorAll('input[name="activities"]').forEach(checkbox => {
                checkbox.checked = data.profil.activities.includes(checkbox.value);
            });
        }
        
        if (data.probleme) {
            const descField = document.getElementById('description');
            const solutionField = document.getElementById('current_solution');
            
            // La description peut contenir des problèmes cochés fusionnés + texte libre
            // On restitue simplement dans le champ texte si présent
            if (data.probleme.description) {
                // Si la description contient " | Autre : ", on sépare
                const desc = data.probleme.description;
                if (desc.includes(' | Autre : ')) {
                    const parts = desc.split(' | Autre : ');
                    const codes = parts[0].split(', ').map(s => s.trim());
                    document.querySelectorAll('input[name="problems"]').forEach(cb => {
                        cb.checked = codes.includes(cb.value);
                    });
                    descField.value = parts[1] || '';
                } else if (desc.includes(', ')) {
                    // Plusieurs codes sans texte libre
                    const codes = desc.split(', ').map(s => s.trim());
                    document.querySelectorAll('input[name="problems"]').forEach(cb => {
                        cb.checked = codes.includes(cb.value);
                    });
                    descField.value = '';
                } else {
                    // Peut être soit un code seul, soit du texte libre
                    const matchingCheckbox = Array.from(document.querySelectorAll('input[name="problems"]'))
                        .find(cb => cb.value === desc);
                    if (matchingCheckbox) {
                        matchingCheckbox.checked = true;
                        descField.value = '';
                    } else {
                        descField.value = desc;
                    }
                }
            }
            
            document.getElementById('situation').value = data.probleme.situation || '';
            
            // Même logique pour la solution
            if (data.probleme.current_solution) {
                const sol = data.probleme.current_solution;
                if (sol.includes(' | Autre : ')) {
                    const parts = sol.split(' | Autre : ');
                    const codes = parts[0].split(', ').map(s => s.trim());
                    document.querySelectorAll('input[name="solutions"]').forEach(cb => {
                        cb.checked = codes.includes(cb.value);
                    });
                    solutionField.value = parts[1] || '';
                } else if (sol.includes(', ')) {
                    const codes = sol.split(', ').map(s => s.trim());
                    document.querySelectorAll('input[name="solutions"]').forEach(cb => {
                        cb.checked = codes.includes(cb.value);
                    });
                    solutionField.value = '';
                } else {
                    const matchingCheckbox = Array.from(document.querySelectorAll('input[name="solutions"]'))
                        .find(cb => cb.value === sol);
                    if (matchingCheckbox) {
                        matchingCheckbox.checked = true;
                        solutionField.value = '';
                    } else {
                        solutionField.value = sol;
                    }
                }
            }
            
            document.getElementById('frequency').value = data.probleme.frequency || '';
            
            if (data.probleme.severity) {
                const sevInput = document.querySelector(`input[name="severity"][value="${data.probleme.severity}"]`);
                if (sevInput) sevInput.checked = true;
            }
        }
        
        showStep(data.current_step);
        updateProgress(getProgressForStep(data.current_step));
        
        const resumeUrl = window.location.origin + '/questionnaire?token=' + token;
        showResumeLink(resumeUrl);
    } catch (error) {
        console.error('Erreur:', error);
        startNewQuestionnaire();
    }
}

function showResumeLink(url) {
    const resumeLink = document.getElementById('resumeLink');
    if (resumeLink) {
        resumeLink.style.display = 'block';
        document.getElementById('resumeUrl').value = url;
    }
}

function copyResumeLink() {
    const resumeUrl = document.getElementById('resumeUrl');
    resumeUrl.select();
    document.execCommand('copy');
    alert('Lien copié ! Conservez-le pour reprendre plus tard.');
}

function showStep(step) {
    document.querySelectorAll('.step').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(`step-${step}`);
    if (target) target.classList.add('active');
    currentStep = step;
    updateProgressSteps(step);
}

function updateProgress(percentage) {
    const bar = document.getElementById('progressBar');
    const text = document.getElementById('progressText');
    if (bar) bar.style.width = percentage + '%';
    if (text) text.textContent = percentage + '%';
}

function updateProgressSteps(step) {
    const stepOrder = ['profil', 'probleme', 'importance'];
    const currentIndex = stepOrder.indexOf(step);
    
    document.querySelectorAll('.progress-step').forEach((el, index) => {
        el.classList.remove('active', 'completed');
        if (index < currentIndex) el.classList.add('completed');
        if (index === currentIndex) el.classList.add('active');
    });
}

function getProgressForStep(step) {
    const steps = {'profil': 0, 'probleme': 40, 'importance': 70, 'complete': 100};
    return steps[step] || 0;
}

async function saveProfil() {
    const age = document.getElementById('age').value;
    const commune = document.getElementById('commune').value;
    const education = document.getElementById('education').value;
    const smartphone = document.querySelector('input[name="smartphone"]:checked');
    const activities = Array.from(document.querySelectorAll('input[name="activities"]:checked')).map(cb => cb.value);
    
    if (!age || !commune || !education || !smartphone || activities.length === 0) {
        alert('Veuillez remplir toutes les informations avant de continuer.');
        return;
    }
    
    const data = {
        token: respondentToken,
        step: 'profil',
        answers: { age, commune, education, smartphone: smartphone.value, activities }
    };
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showTransitionOverlay('Enregistrement de vos informations...', () => {
                showStep('probleme');
                updateProgress(40);
                window.scrollTo(0, 0);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de la sauvegarde.');
    }
}

async function saveProbleme() {
    const description = document.getElementById('description').value;
    const situation = document.getElementById('situation').value;
    const currentSolution = document.getElementById('current_solution').value;
    
    const checkedProblems = Array.from(document.querySelectorAll('input[name="problems"]:checked'))
        .map(cb => cb.value);
    const checkedSolutions = Array.from(document.querySelectorAll('input[name="solutions"]:checked'))
        .map(cb => cb.value);
    
    // Validation : au moins une case cochée OU un texte libre pour les problèmes
    if (checkedProblems.length === 0 && !description.trim()) {
        alert('Veuillez cocher au moins un problème ou décrire votre propre problème.');
        return;
    }
    
    // Fusionner : problèmes cochés + problème libre
    const problemSummary = checkedProblems.length > 0 
        ? checkedProblems.join(', ') + (description.trim() ? ' | Autre : ' + description : '')
        : description;
    
    // Fusionner : solutions cochées + solution libre
    const solutionSummary = checkedSolutions.length > 0 
        ? checkedSolutions.join(', ') + (currentSolution.trim() ? ' | Autre : ' + currentSolution : '')
        : currentSolution;
    
    const data = {
        token: respondentToken,
        step: 'probleme',
        answers: { 
            description: problemSummary, 
            situation: situation, 
            current_solution: solutionSummary 
        }
    };
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showTransitionOverlay('Analyse de vos réponses...', () => {
                showStep('importance');
                updateProgress(70);
                window.scrollTo(0, 0);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de la sauvegarde.');
    }
}

async function saveImportance() {
    const frequency = document.getElementById('frequency').value;
    const severity = document.querySelector('input[name="severity"]:checked');
    
    if (!frequency || !severity) {
        alert('Veuillez répondre à toutes les questions avant de terminer.');
        return;
    }
    
    const data = {
        token: respondentToken,
        step: 'importance',
        answers: { frequency, severity: severity.value }
    };
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ token: respondentToken, step: 'complete', answers: {} })
            });
            
            showTransitionOverlay('Merci pour votre participation !', () => {
                window.location.href = '/merci';
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de la sauvegarde.');
    }
}