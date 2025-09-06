# Phishing Detection System Environment Variables
# Copy this file to .env and customize the values

# Email Server Configuration
MAILHOG_HOST=localhost
MAILHOG_PORT=8025
SMTP_HOST=localhost
SMTP_PORT=1025

# External API Keys
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here

# Database Configuration
DATABASE_PATH=data/quarantine.db
TRAINING_DB_PATH=data/training.db
INCIDENT_DB_PATH=data/incident_response.db

# ML Model Configuration
MODEL_PATH=data/models/phishing_model.pkl
MODEL_THRESHOLD=0.7

# Web Dashboard Configuration
FLASK_SECRET_KEY=change-this-secret-key-in-production
FLASK_DEBUG=True
FLASK_PORT=5000
FLASK_HOST=0.0.0.0

# Security Configuration
ADMIN_EMAIL=admin@company.local
SOC_EMAIL=soc@company.local
SECURITY_EMAIL=security@company.local

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_USER_NOTIFICATIONS=True
ENABLE_SOC_ALERTS=True

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=True
ENABLE_METRICS=True

# Monitoring Configuration
PROMETHEUS_ENABLED=False
ELASTICSEARCH_ENABLED=False
GRAFANA_ENABLED=False

# Performance Settings
MAX_CONCURRENT_EMAILS=10
BATCH_SIZE=50
PROCESSING_INTERVAL=30

# Feature Flags
ENABLE_ATTACHMENT_ANALYSIS=True
ENABLE_OCR_PROCESSING=True
ENABLE_BLACKLIST_AUTO_UPDATE=True
ENABLE_TRAINING_MODULE=True

# Development Settings
MOCK_EXTERNAL_APIS=False
TEST_MODE=False
SAMPLE_DATA_ENABLED=False