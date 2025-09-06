#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import time
import yaml
import sqlite3
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import requests
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

class ConfigManager:
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        default_config = {
            'system': {'log_level': 'INFO', 'debug': True},
            'email': {'mode': 'mailhog', 'mailhog': {'host': 'localhost', 'port': 8025}},
            'detection': {'ml_classifier': {'threshold': 0.7}, 'rule_engine': {'threshold': 50}},
            'quarantine': {'database_path': 'data/quarantine.db'},
            'web_dashboard': {'host': '0.0.0.0', 'port': 5000}
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                self._deep_update(default_config, user_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
        
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

class EmailProcessor:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.mode = config.get('email.mode', 'mailhog')
        self.logger = logging.getLogger(__name__)
        self.processed_emails = set()
    
    def fetch_emails(self) -> List[Dict]:
        if self.mode == 'mailhog':
            return self._fetch_mailhog_emails()
        elif self.mode == 'postfix':
            return self._fetch_postfix_emails()
        else:
            self.logger.error(f"Unknown email mode: {self.mode}")
            return []
    
    def _fetch_mailhog_emails(self) -> List[Dict]:
        try:
            host = self.config.get('email.mailhog.host', 'localhost')
            port = self.config.get('email.mailhog.port', 8025)
            
            response = requests.get(f"http://{host}:{port}/api/v2/messages?limit=50", timeout=10)
            response.raise_for_status()
            
            messages = response.json().get('messages', [])
            processed_emails = []
            
            for message in messages:
                email_id = message.get('ID', '')
                if email_id in self.processed_emails:
                    continue
                
                email_data = self._extract_mailhog_data(message)
                if email_data:
                    processed_emails.append(email_data)
                    self.processed_emails.add(email_id)
            
            return processed_emails
            
        except Exception as e:
            self.logger.error(f"Error fetching MailHog emails: {e}")
            return []
    
    def _extract_mailhog_data(self, message: Dict) -> Optional[Dict]:
        try:
            headers = message.get('Content', {}).get('Headers', {})
            from_info = message.get('From', {})
            to_info = message.get('To', [{}])[0] if message.get('To') else {}
            
            return {
                'id': message.get('ID', ''),
                'subject': headers.get('Subject', [''])[0] if headers.get('Subject') else '',
                'sender': f"{from_info.get('Mailbox', '')}@{from_info.get('Domain', '')}",
                'recipient': f"{to_info.get('Mailbox', '')}@{to_info.get('Domain', '')}",
                'body': message.get('Content', {}).get('Body', ''),
                'timestamp': datetime.now().isoformat(),
                'attachments': []
            }
        except Exception as e:
            self.logger.error(f"Error extracting email data: {e}")
            return None
    
    def _fetch_postfix_emails(self) -> List[Dict]:
        self.logger.info("Postfix integration not implemented in this version")
        return []

class MLClassifier:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.model = None
        self.is_trained = False
        self.model_path = config.get('detection.ml_classifier.model_path', 'data/models/phishing_model.pkl')
        self.threshold = config.get('detection.ml_classifier.threshold', 0.7)
        self.logger = logging.getLogger(__name__)
    
    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                self.logger.info(f"Model loaded from {self.model_path}")
            else:
                self.logger.warning(f"Model file not found: {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
    
    def train(self, training_data: List[Dict], labels: List[int]) -> Dict:
        try:
            texts = []
            for email in training_data:
                subject = email.get('subject', '')
                body = email.get('body', '')
                combined_text = f"{subject} {body}".lower().strip()
                texts.append(combined_text)
            
            if not texts or not labels or len(texts) != len(labels):
                return {'error': 'Invalid training data'}
            
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )
            
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.save_model()
            
            self.logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            
            return {
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'report': classification_report(y_test, y_pred, output_dict=True)
            }
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return {'error': str(e)}
    
    def predict(self, email: Dict) -> Tuple[int, float]:
        if not self.is_trained or not self.model:
            return 0, 0.5
        
        try:
            subject = email.get('subject', '')
            body = email.get('body', '')
            text = f"{subject} {body}".lower().strip()
            
            if not text:
                return 0, 0.5
            