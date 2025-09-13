# 🛡️ Phishing Detection System

A comprehensive email security system that automatically detects, quarantines, and responds to phishing attempts using machine learning and rule-based detection.

## 📋 Features

### 🔍 Detection Engine
- **Machine Learning Classifier**: Trained on phishing datasets using scikit-learn
- **Rule-Based Engine**: Pattern matching for suspicious keywords, URLs, and domains
- **Attachment Analysis**: OCR text extraction and VirusTotal scanning
- **Multi-layered Detection**: Combines ML predictions with rule-based analysis

### 📧 Email Processing
- **MailHog Integration**: For testing environments
- **Postfix Support**: For production mail servers
- **Real-time Processing**: Continuous email monitoring
- **Attachment Handling**: Safe analysis of email attachments

### 🗄️ Quarantine System
- **Secure Storage**: SQLite database for quarantined emails
- **Risk Scoring**: Detailed threat assessment
- **Safe Preview**: Read-only email viewing with disabled links
- **Bulk Management**: Release, delete, or mark false positives

### 🚨 Incident Response
- **Automated Blacklisting**: Domain and IP blocking
- **Smart Notifications**: User and SOC team alerts
- **Response Tracking**: Detailed incident logging
- **Escalation Rules**: Risk-based alert prioritization

### 🎓 User Training
- **Interactive Quizzes**: Security awareness testing
- **Progress Tracking**: Individual performance metrics
- **Gamification**: Leaderboards and achievements
- **Personalized Training**: Recommendations based on exposure

### 📊 Monitoring & Analytics
- **Web Dashboard**: Real-time security overview
- **Detailed Reports**: Threat statistics and trends
- **Performance Metrics**: System health monitoring
- **Export Capabilities**: Data export for analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email Server  │───▶│  Detection      │───▶│   Quarantine    │
│  MailHog/Postfix│    │  ML + Rules     │    │   SQLite DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  Incident       │    │  User Training  │
│   Flask App     │    │  Response       │    │  Quiz System    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Monitoring    │
                       │  ELK + Grafana  │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose (optional)
- SQLite3

### 1. Installation
```bash
git clone https://github.com/suhasdk18/phishing-detection-system.git
cd phishing-detection-system

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp config.yml.example config.yml
# Edit config.yml with your settings
```

### 3. Initialize Database
```bash
python main.py --init-db
```

### 4. Start Services

**Option A: Using Docker Compose (Recommended)**
```bash
docker-compose up -d
```

**Option B: Manual Setup**
```bash
# Start MailHog for testing
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Start Detection System
python main.py

# In another terminal, start Web Dashboard
python app.py
```

### 5. Access Services
- **Web Dashboard**: http://localhost:5000
- **MailHog UI**: http://localhost:8025
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kibana**: http://localhost:5601

## 📊 Usage

### Web Dashboard
Navigate to `http://localhost:5000` to access the main dashboard featuring:
- Real-time threat overview
- Quarantined email management
- User training portal
- System statistics

### Command Line Interface
```bash
# Start monitoring
python main.py --mode monitor --interval 30

# Train ML model
python main.py --mode train --dataset data/phishing_dataset.csv

# Test single batch
python main.py --mode test

# Initialize databases
python main.py --init-db
```

### API Endpoints
- `GET /api/stats` - System statistics
- `GET /api/quarantine` - List quarantined emails
- `POST /api/quarantine/{id}/release` - Release email
- `POST /api/quarantine/{id}/delete` - Delete email
- `GET /api/training/quiz` - Get quiz questions
- `POST /api/training/submit` - Submit quiz answers

## 📁 Project Structure

```
phishing-detection-system/
├── main.py                 # Main application entry point
├── app.py                  # Web dashboard application
├── requirements.txt        # Python dependencies
├── config.yml             # Configuration file
├── docker-compose.yml     # Docker services setup
├── Dockerfile            # Container image definition
├── README.md            # This file
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
├── src/                # Source code modules
│   ├── detection/      # ML and rule-based detection
│   ├── quarantine/     # Email quarantine system
│   ├── response/       # Incident response automation
│   ├── training/       # User training system
│   └── utils/          # Utility functions
├── templates/          # HTML templates for web UI
├── static/            # CSS, JS, and image assets
├── data/              # Data storage directory
│   ├── models/        # ML models
│   ├── datasets/      # Training datasets
│   └── quarantine/    # Quarantined emails
├── logs/              # Application logs
├── tests/             # Unit and integration tests
└── docs/              # Additional documentation
```

## 🔧 Configuration

Edit `config.yml` to customize the system:

```yaml
# Email server settings
email:
  mode: "mailhog"  # or "postfix"
  host: "localhost"
  port: 8025

# Detection thresholds
detection:
  ml_threshold: 0.7
  rule_threshold: 50
  combined_threshold: 0.6

# External APIs
apis:
  virustotal_key: "your_api_key"
  abuseipdb_key: "your_api_key"

# Notifications
notifications:
  smtp_host: "localhost"
  smtp_port: 1025
  from_address: "security@company.local"
  soc_email: "soc@company.local"
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### Send Test Phishing Email
```bash
curl -X POST http://localhost:8025/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "from": "attacker@phishing-site.com",
    "to": ["user@company.com"],
    "subject": "URGENT: Verify your account immediately",
    "body": "Click here to verify: http://malicious-link.com"
  }'
```

## 📈 Monitoring

### Grafana Dashboards
Access Grafana at `http://localhost:3000` with:
- Username: `admin`
- Password: `admin`

Pre-configured dashboards include:
- Email Processing Overview
- Threat Detection Statistics
- System Performance Metrics
- User Training Progress

### ELK Stack
Kibana available at `http://localhost:5601` for:
- Log analysis and searching
- Custom visualizations
- Alert management
- Data exploration

## 🔒 Security Features

- **Sandboxed Email Preview**: Safe viewing without executing malicious content
- **Automated Quarantine**: Immediate isolation of suspicious emails
- **Blacklist Management**: Dynamic blocking of malicious senders/domains
- **Audit Trail**: Comprehensive logging of all security events
- **Access Controls**: Role-based permissions for dashboard access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**suhasdk18**
- Email: suhasdk18@gmail.com
- GitHub: [@suhasdk18](https://github.com/suhasdk18)

## 🙏 Acknowledgments

- PhishTank for phishing URL datasets
- VirusTotal for malware detection API
- scikit-learn for machine learning capabilities
- Flask for web framework
- The cybersecurity community for threat intelligence

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/suhasdk18/phishing-detection-system/issues) page
2. Review the documentation in the `docs/` directory
3. Contact the maintainer at suhasdk18@gmail.co

---

⭐ **Star this repo if you find it helpful!**
