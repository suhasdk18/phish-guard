#!/usr/bin/env python3

import os
import sys
import logging
import sqlite3
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

class ConfigManager:
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        default_config = {
            'web_dashboard': {'host': '0.0.0.0', 'port': 5000, 'debug': True, 'secret_key': 'dev-key'},
            'quarantine': {'database_path': 'data/quarantine.db'},
            'training': {'database_path': 'data/training.db'},
            'incident_response': {'database_path': 'data/incident_response.db'}
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                self._deep_update(default_config, user_config)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        
        return default_config
    
    def _deep_update(self, base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default=None):
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

class DatabaseManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.quarantine_db = config.get('quarantine.database_path', 'data/quarantine.db')
        self.training_db = config.get('training.database_path', 'data/training.db')
        self.incident_db = config.get('incident_response.database_path', 'data/incident_response.db')
    
    def get_quarantined_emails(self, limit: int = 100, status: str = None) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.quarantine_db)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, sender, recipient, subject, body, ml_score, rule_score, 
                       combined_score, detection_reasons, quarantine_date, status
                FROM quarantined_emails
            '''
            params = []
            
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            
            query += ' ORDER BY quarantine_date DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = ['id', 'sender', 'recipient', 'subject', 'body', 'ml_score', 
                      'rule_score', 'combined_score', 'detection_reasons', 'quarantine_date', 'status']
            
            emails = []
            for row in rows:
                email_dict = dict(zip(columns, row))
                try:
                    email_dict['detection_reasons'] = json.loads(email_dict['detection_reasons'] or '[]')
                except:
                    email_dict['detection_reasons'] = []
                
                email_dict['risk_level'] = self._calculate_risk_level(email_dict['combined_score'])
                emails.append(email_dict)
            
            conn.close()
            return emails
            
        except Exception as e:
            print(f"Error getting quarantined emails: {e}")
            return []
    
    def get_email_by_id(self, email_id: int) -> Optional[Dict]:
        emails = self.get_quarantined_emails(limit=1000)
        return next((e for e in emails if e['id'] == email_id), None)
    
    def release_email(self, email_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.quarantine_db)
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE quarantined_emails SET status = ? WHERE id = ?',
                ('released', email_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
        except Exception as e:
            print(f"Error releasing email: {e}")
            return False
    
    def delete_email(self, email_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.quarantine_db)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM quarantined_emails WHERE id = ?', (email_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
        except Exception as e:
            print(f"Error deleting email: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict:
        try:
            conn = sqlite3.connect(self.quarantine_db)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM quarantined_emails WHERE status = "quarantined"')
            total_quarantined = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM quarantined_emails WHERE combined_score > 0.8')
            high_risk = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM quarantined_emails WHERE combined_score BETWEEN 0.5 AND 0.8')
            medium_risk = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM quarantined_emails WHERE quarantine_date >= ?', 
                          ((datetime.now() - timedelta(days=1)).isoformat(),))
            today_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(combined_score) FROM quarantined_emails')
            avg_risk = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_quarantined': total_quarantined,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'today_count': today_count,
                'average_risk_score': round(avg_risk * 100, 1),
                'system_status': 'Active'
            }
            
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {
                'total_quarantined': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'today_count': 0,
                'average_risk_score': 0,
                'system_status': 'Error'
            }
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.quarantine_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sender, subject, combined_score, quarantine_date, status
                FROM quarantined_emails
                ORDER BY quarantine_date DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            activities = []
            for row in rows:
                activities.append({
                    'sender': row[0],
                    'subject': row[1][:50] + '...' if len(row[1]) > 50 else row[1],
                    'risk_score': round(row[2] * 100, 1),
                    'date': row[3],
                    'status': row[4],
                    'risk_level': self._calculate_risk_level(row[2])
                })
            
            return activities
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def _calculate_risk_level(self, score: float) -> str:
        if score >= 0.8:
            return 'HIGH'
        elif score >= 0.5:
            return 'MEDIUM'
        elif score >= 0.3:
            return 'LOW'
        else:
            return 'MINIMAL'

class TrainingManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.db_path = config.get('training.database_path', 'data/training.db')
        self.init_database()
    
    def init_database(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    completion_date TEXT NOT NULL,
                    answers TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing training database: {e}")
    
    def get_quiz_questions(self) -> List[Dict]:
        return [
            {
                'id': 1,
                'question': 'What should you do first when you receive a suspicious email?',
                'options': ['Delete it immediately', 'Check the sender address', 'Click links to verify', 'Forward to colleagues'],
                'correct': 1,
                'explanation': 'Always verify the sender address first to identify potential spoofing attempts.'
            },
            {
                'id': 2,
                'question': 'Which of these is a common phishing indicator?',
                'options': ['Professional formatting', 'Urgent language demanding action', 'Proper grammar', 'Company branding'],
                'correct': 1,
                'explanation': 'Phishing emails often use urgent language to create pressure and bypass critical thinking.'
            },
            {
                'id': 3,
                'question': 'How can you safely check where a link leads?',
                'options': ['Click it to see', 'Hover over it without clicking', 'Ask IT department', 'Google the website'],
                'correct': 1,
                'explanation': 'Hovering over links reveals the actual destination URL without clicking.'
            },
            {
                'id': 4,
                'question': 'What should you do with suspicious attachments?',
                'options': ['Open in protected mode', 'Scan with antivirus first', 'Never open them', 'Check file extension'],
                'correct': 2,
                'explanation': 'Never open suspicious attachments as they may contain malware.'
            },
            {
                'id': 5,
                'question': 'Which domain is likely a phishing attempt?',
                'options': ['paypal.com', 'payp4l.com', 'amazon.com', 'google.com'],
                'correct': 1,
                'explanation': 'payp4l.com uses character substitution (4 instead of a) to mimic the legitimate PayPal domain.'
            }
        ]
    
    def submit_quiz(self, user_email: str, answers: List[int]) -> Dict:
        questions = self.get_quiz_questions()
        score = 0
        results = []
        
        for i, question in enumerate(questions):
            user_answer = answers[i] if i < len(answers) else -1
            is_correct = user_answer == question['correct']
            if is_correct:
                score += 1
            
            results.append({
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': question['correct'],
                'is_correct': is_correct,
                'explanation': question['explanation']
            })
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quiz_results (user_email, score, total_questions, completion_date, answers)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_email, score, len(questions), datetime.now().isoformat(), json.dumps(answers)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving quiz results: {e}")
        
        percentage = round((score / len(questions)) * 100, 1)
        passed = percentage >= 70
        
        return {
            'score': score,
            'total': len(questions),
            'percentage': percentage,
            'passed': passed,
            'results': results
        }
    
    def get_user_stats(self, user_email: str) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score,
                       COUNT(*) as total_attempts,
                       MAX(CAST(score AS FLOAT) / total_questions * 100) as best_score
                FROM quiz_results 
                WHERE user_email = ?
            ''', (user_email,))
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'average_score': round(result[0] or 0, 1),
                'total_attempts': result[1] or 0,
                'best_score': round(result[2] or 0, 1)
            }
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {'average_score': 0, 'total_attempts': 0, 'best_score': 0}

config = ConfigManager()
db_manager = DatabaseManager(config)
training_manager = TrainingManager(config)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.get('web_dashboard.secret_key', 'dev-key-change-in-production')
app.config['DEBUG'] = config.get('web_dashboard.debug', True)

logging.basicConfig(level=logging.INFO)

@app.route('/')
def dashboard():
    stats = db_manager.get_dashboard_stats()
    recent_activity = db_manager.get_recent_activity(10)
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_activity=recent_activity,
                         current_page='dashboard')

@app.route('/quarantine')
def quarantine_view():
    status_filter = request.args.get('status')
    emails = db_manager.get_quarantined_emails(limit=100, status=status_filter)
    
    return render_template('quarantine.html', 
                         emails=emails, 
                         current_filter=status_filter,
                         current_page='quarantine')

@app.route('/quarantine/<int:email_id>')
def email_detail(email_id):
    email = db_manager.get_email_by_id(email_id)
    if not email:
        flash('Email not found', 'error')
        return redirect(url_for('quarantine_view'))
    
    return render_template('email_detail.html', 
                         email=email,
                         current_page='quarantine')

@app.route('/api/quarantine/<int:email_id>/release', methods=['POST'])
def release_email(email_id):
    success = db_manager.release_email(email_id)
    return jsonify({'success': success, 'message': 'Email released' if success else 'Failed to release email'})

@app.route('/api/quarantine/<int:email_id>/delete', methods=['POST'])
def delete_email(email_id):
    success = db_manager.delete_email(email_id)
    return jsonify({'success': success, 'message': 'Email deleted' if success else 'Failed to delete email'})

@app.route('/training')
def training_dashboard():
    return render_template('training.html', current_page='training')

@app.route('/training/quiz')
def quiz():
    questions = training_manager.get_quiz_questions()
    return render_template('quiz.html', questions=questions, current_page='training')

@app.route('/training/quiz/submit', methods=['POST'])
def submit_quiz():
    user_email = request.form.get('user_email')
    if not user_email:
        flash('Email address is required', 'error')
        return redirect(url_for('quiz'))
    
    answers = []
    questions = training_manager.get_quiz_questions()
    
    for i in range(len(questions)):
        answer = request.form.get(f'question_{i}')
        if answer is not None:
            answers.append(int(answer))
        else:
            answers.append(-1)
    
    results = training_manager.submit_quiz(user_email, answers)
    
    return render_template('quiz_results.html', 
                         results=results,
                         user_email=user_email,
                         current_page='training')

@app.route('/api/training/user-stats/<user_email>')
def get_user_stats(user_email):
    stats = training_manager.get_user_stats(user_email)
    return jsonify(stats)

@app.route('/api/stats')
def api_stats():
    stats = db_manager.get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/quarantine')
def api_quarantine():
    limit = request.args.get('limit', 50, type=int)
    status = request.args.get('status')
    emails = db_manager.get_quarantined_emails(limit=limit, status=status)
    return jsonify({'emails': emails, 'count': len(emails)})

@app.route('/reports')
def reports():
    stats = db_manager.get_dashboard_stats()
    recent_emails = db_manager.get_quarantined_emails(limit=20)
    
    risk_distribution = {
        'HIGH': sum(1 for e in recent_emails if e['risk_level'] == 'HIGH'),
        'MEDIUM': sum(1 for e in recent_emails if e['risk_level'] == 'MEDIUM'),
        'LOW': sum(1 for e in recent_emails if e['risk_level'] == 'LOW')
    }
    
    return render_template('reports.html',
                         stats=stats,
                         risk_distribution=risk_distribution,
                         current_page='reports')

@app.route('/settings')
def settings():
    return render_template('settings.html', current_page='settings')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.template_filter('datetime')
def datetime_filter(s):
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return s

@app.template_filter('risk_badge_class')
def risk_badge_class(risk_level):
    classes = {
        'HIGH': 'badge bg-danger',
        'MEDIUM': 'badge bg-warning text-dark', 
        'LOW': 'badge bg-info',
        'MINIMAL': 'badge bg-success'
    }
    return classes.get(risk_level, 'badge bg-secondary')

@app.context_processor
def inject_config():
    return {
        'system_name': config.get('system.name', 'Phishing Detection System'),
        'version': config.get('system.version', '1.0.0'),
        'author': config.get('system.author', 'suhasdk18')
    }

if __name__ == '__main__':
    host = config.get('web_dashboard.host', '0.0.0.0')
    port = config.get('web_dashboard.port', 5000)
    debug = config.get('web_dashboard.debug', True)
    
    print(f"Starting Phishing Detection Web Dashboard...")
    print(f"Dashboard URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)