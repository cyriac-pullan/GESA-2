// Gaming-style JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize progress bars
    initializeProgressBars();
    
    // Initialize charts if on analytics page
    if (document.getElementById('skillRadarChart')) {
        initializeCharts();
    }
    
    // Initialize assessment timer
    if (document.querySelector('.assessment-form')) {
        initializeAssessmentTimer();
    }
    
    // Add click effects to buttons
    addButtonEffects();
    
    // Initialize notification system
    initializeNotifications();
});

function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.game-card, .achievement-badge, .leaderboard-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    });
    
    cards.forEach(card => {
        observer.observe(card);
    });
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.transition = 'width 1.5s ease-in-out';
            bar.style.width = targetWidth;
        }, 200);
    });
}

function initializeCharts() {
    // Skill Radar Chart
    const radarCtx = document.getElementById('skillRadarChart');
    if (radarCtx) {
        const skillData = JSON.parse(radarCtx.getAttribute('data-skills') || '{}');
        
        const labels = Object.keys(skillData);
        const scores = labels.map(label => {
            const assessments = skillData[label];
            if (assessments.length > 0) {
                return assessments[assessments.length - 1].score; // Latest score
            }
            return 0;
        });
        
        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Skill Scores',
                    data: scores,
                    backgroundColor: 'rgba(108, 92, 231, 0.2)',
                    borderColor: 'rgba(108, 92, 231, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(108, 92, 231, 1)',
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Progress Chart
    const progressCtx = document.getElementById('progressChart');
    if (progressCtx) {
        const skillData = JSON.parse(progressCtx.getAttribute('data-skills') || '{}');
        
        const datasets = [];
        const colors = [
            'rgba(108, 92, 231, 1)',
            'rgba(0, 184, 148, 1)',
            'rgba(253, 121, 168, 1)',
            'rgba(253, 203, 110, 1)'
        ];
        
        let colorIndex = 0;
        Object.keys(skillData).forEach(skill => {
            const assessments = skillData[skill];
            datasets.push({
                label: skill,
                data: assessments.map(a => ({ x: a.date, y: a.score })),
                borderColor: colors[colorIndex % colors.length],
                backgroundColor: colors[colorIndex % colors.length] + '20',
                tension: 0.4
            });
            colorIndex++;
        });
        
        new Chart(progressCtx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            parser: 'YYYY-MM-DD',
                            displayFormats: {
                                day: 'MMM DD'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }
    
    // XP Distribution Chart
    const xpCtx = document.getElementById('xpChart');
    if (xpCtx) {
        new Chart(xpCtx, {
            type: 'doughnut',
            data: {
                labels: ['Assessments', 'Resume', 'Activities', 'Badges', 'Challenges'],
                datasets: [{
                    data: [40, 25, 15, 10, 10],
                    backgroundColor: [
                        'rgba(108, 92, 231, 0.8)',
                        'rgba(0, 184, 148, 0.8)',
                        'rgba(253, 121, 168, 0.8)',
                        'rgba(253, 203, 110, 0.8)',
                        'rgba(232, 67, 147, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

function initializeAssessmentTimer() {
    const timerElement = document.getElementById('assessmentTimer');
    if (!timerElement) return;
    
    let startTime = Date.now();
    let timerInterval;
    
    function updateTimer() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        timerElement.textContent = `Time: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    timerInterval = setInterval(updateTimer, 1000);
    updateTimer();
    
    // Stop timer when form is submitted
    const form = document.querySelector('.assessment-form');
    if (form) {
        form.addEventListener('submit', () => {
            clearInterval(timerInterval);
        });
    }
}

function addButtonEffects() {
    const buttons = document.querySelectorAll('.btn-game, .btn-game-secondary');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add CSS animation for ripple effect
    if (!document.querySelector('#ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function initializeNotifications() {
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.5s ease-out';
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 500);
            }, 5000);
        }
    });
}

// Badge notification system
function showBadgeNotification(badgeName, badgeIcon) {
    const notification = document.createElement('div');
    notification.className = 'badge-notification';
    notification.innerHTML = `
        <div class="badge-notification-content">
            <i class="${badgeIcon} badge-notification-icon"></i>
            <div class="badge-notification-text">
                <strong>New Badge Earned!</strong>
                <div>${badgeName}</div>
            </div>
        </div>
    `;
    
    // Add CSS for notification if not exists
    if (!document.querySelector('#badge-notification-css')) {
        const style = document.createElement('style');
        style.id = 'badge-notification-css';
        style.textContent = `
            .badge-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                z-index: 1000;
                animation: slideInRight 0.5s ease-out, fadeOut 0.5s ease-out 4.5s;
                max-width: 300px;
            }
            
            .badge-notification-content {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .badge-notification-icon {
                font-size: 2rem;
                color: #ffd700;
            }
            
            .badge-notification-text strong {
                display: block;
                margin-bottom: 5px;
            }
            
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes fadeOut {
                from {
                    opacity: 1;
                }
                to {
                    opacity: 0;
                    transform: translateX(100%);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Confetti effect for achievements
function triggerConfetti() {
    // Simple confetti effect using CSS animations
    const confettiCount = 50;
    const colors = ['#6c5ce7', '#00b894', '#fd79a8', '#fdcb6e', '#e84393'];
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            left: ${Math.random() * 100}vw;
            top: -10px;
            z-index: 1000;
            border-radius: 50%;
            animation: fall ${Math.random() * 3 + 2}s linear forwards;
            pointer-events: none;
        `;
        
        document.body.appendChild(confetti);
        
        setTimeout(() => {
            confetti.remove();
        }, 5000);
    }
    
    // Add CSS animation for confetti fall
    if (!document.querySelector('#confetti-animation')) {
        const style = document.createElement('style');
        style.id = 'confetti-animation';
        style.textContent = `
            @keyframes fall {
                to {
                    transform: translateY(100vh) rotate(360deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Utility functions
function animateNumber(element, start, end, duration) {
    if (!element) return;
    
    const startTime = performance.now();
    const startValue = start;
    const endValue = end;
    
    function update(currentTime) {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.floor(startValue + (endValue - startValue) * easeOutQuart);
        
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Initialize number animations on page load
document.addEventListener('DOMContentLoaded', function() {
    const scoreElements = document.querySelectorAll('.score-number, .xp-display');
    
    scoreElements.forEach(element => {
        const finalValue = parseInt(element.textContent) || 0;
        element.textContent = '0';
        
        setTimeout(() => {
            animateNumber(element, 0, finalValue, 2000);
        }, 500);
    });
});
