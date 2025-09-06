class PhishingDashboard {
    constructor() {
        this.init();
        this.bindEvents();
        this.startAutoRefresh();
    }

    init() {
        this.loadTooltips();
        this.initializeCharts();
    }

    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-release-email')) {
                this.releaseEmail(e.target.dataset.emailId);
            }
            if (e.target.matches('.btn-delete-email')) {
                this.deleteEmail(e.target.dataset.emailId);
            }
            if (e.target.matches('.btn-load-user-stats')) {
                this.loadUserStats();
            }
        });
    }

    loadTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    async releaseEmail(emailId) {
        if (!confirm('Are you sure you want to release this email?')) {
            return;
        }

        try {
            const response = await fetch(`/api/quarantine/${emailId}/release`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Email released successfully', 'success');
                this.refreshEmailList();
            } else {
                this.showAlert('Failed to release email', 'danger');
            }
        } catch (error) {
            console.error('Error releasing email:', error);
            this.showAlert('Error releasing email', 'danger');
        }
    }

    async deleteEmail(emailId) {
        if (!confirm('Are you sure you want to permanently delete this email?')) {
            return;
        }

        try {
            const response = await fetch(`/api/quarantine/${emailId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Email deleted successfully', 'success');
                this.refreshEmailList();
                document.querySelector(`#email-${emailId}`)?.remove();
            } else {
                this.showAlert('Failed to delete email', 'danger');
            }
        } catch (error) {
            console.error('Error deleting email:', error);
            this.showAlert('Error deleting email', 'danger');
        }
    }

    async loadUserStats() {
        const userEmail = document.getElementById('userEmail').value;
        if (!userEmail) {
            this.showAlert('Please enter an email address', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/training/user-stats/${encodeURIComponent(userEmail)}`);
            const stats = await response.json();
            
            this.displayUserStats(stats, userEmail);
        } catch (error) {
            console.error('Error loading user stats:', error);
            this.showAlert('Error loading user statistics', 'danger');
        }
    }

    displayUserStats(stats, userEmail) {
        const statsContent = document.getElementById('statsContent');
        if (!statsContent) return;

        statsContent.innerHTML = `
            <h6>Statistics for: ${userEmail}</h6>
            <div class="row text-center">
                <div class="col-4">
                    <h4 class="text-primary">${stats.average_score}%</h4>
                    <small>Average Score</small>
                </div>
                <div class="col-4">
                    <h4 class="text-success">${stats.total_attempts}</h4>
                    <small>Total Attempts</small>
                </div>
                <div class="col-4">
                    <h4 class="text-warning">${stats.best_score}%</h4>
                    <small>Best Score</small>
                </div>
            </div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('statsModal'));
        modal.show();
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('.container-fluid');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.insertBefore(alert, alertContainer.firstChild);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    async refreshDashboardStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            this.updateStatsCards(stats);
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }

    updateStatsCards(stats) {
        const todayElement = document.querySelector('[data-stat="today-count"]');
        const highRiskElement = document.querySelector('[data-stat="high-risk"]');
        const mediumRiskElement = document.querySelector('[data-stat="medium-risk"]');
        
        if (todayElement) todayElement.textContent = stats.today_count || 0;
        if (highRiskElement) highRiskElement.textContent = stats.high_risk_count || 0;
        if (mediumRiskElement) mediumRiskElement.textContent = stats.medium_risk_count || 0;
    }

    async refreshEmailList() {
        const tbody = document.querySelector('#email-list tbody');
        if (!tbody) return;

        try {
            const response = await fetch('/api/quarantine?limit=20');
            const data = await response.json();
            
            if (data.emails) {
                this.renderEmailList(data.emails, tbody);
            }
        } catch (error) {
            console.error('Error refreshing email list:', error);
        }
    }

    renderEmailList(emails, container) {
        container.innerHTML = '';
        
        emails.forEach(email => {
            const row = document.createElement('tr');
            row.id = `email-${email.id}`;
            row.innerHTML = `
                <td>${this.formatDate(email.quarantine_date)}</td>
                <td><span class="text-truncate d-inline-block" style="max-width: 150px;">${email.sender}</span></td>
                <td><span class="text-truncate d-inline-block" style="max-width: 200px;">${email.subject}</span></td>
                <td><span class="badge ${this.getRiskBadgeClass(email.combined_score)}">${this.getRiskLevel(email.combined_score)}</span></td>
                <td><span class="badge ${email.status === 'quarantined' ? 'bg-warning' : 'bg-secondary'}">${email.status}</span></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/quarantine/${email.id}" class="btn btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                        <button class="btn btn-outline-success btn-release-email" data-email-id="${email.id}">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-delete-email" data-email-id="${email.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            container.appendChild(row);
        });
    }

    initializeCharts() {
        this.initRiskChart();
        this.initTrendChart();
    }

    initRiskChart() {
        const ctx = document.getElementById('riskChart');
        if (!ctx) return;

        this.riskChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['High Risk', 'Medium Risk', 'Low Risk'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#dc3545', '#ffc107', '#17a2b8'],
                    borderWidth: 2,
                    borderColor: '#fff'
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

    initTrendChart() {
        const ctx = document.getElementById('trendChart');
        if (!ctx) return;

        this.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Phishing Emails Detected',
                    data: [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    startAutoRefresh() {
        setInterval(() => {
            this.refreshDashboardStats();
        }, 30000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    getRiskLevel(score) {
        if (score >= 0.8) return 'HIGH';
        if (score >= 0.5) return 'MEDIUM';
        if (score >= 0.3) return 'LOW';
        return 'MINIMAL';
    }

    getRiskBadgeClass(score) {
        if (score >= 0.8) return 'bg-danger';
        if (score >= 0.5) return 'bg-warning text-dark';
        if (score >= 0.3) return 'bg-info';
        return 'bg-success';
    }
}

class QuizManager {
    constructor() {
        this.currentQuestion = 0;
        this.answers = [];
        this.startTime = Date.now();
    }

    submitAnswer(questionIndex, answerIndex) {
        this.answers[questionIndex] = answerIndex;
    }

    calculateScore() {
        return {
            score: this.answers.filter(a => a !== -1).length,
            total: this.answers.length,
            timeSpent: Math.round((Date.now() - this.startTime) / 1000)
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PhishingDashboard();
    
    if (document.querySelector('.quiz-container')) {
        window.quizManager = new QuizManager();
    }
});

function releaseEmail(emailId) {
    window.dashboard.releaseEmail(emailId);
}

function deleteEmail(emailId) {
    window.dashboard.deleteEmail(emailId);
}

function loadUserStats() {
    window.dashboard.loadUserStats();
}