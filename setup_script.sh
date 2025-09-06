#!/bin/bash

echo "🛡️  Phishing Detection System - Setup Script"
echo "================================================"
echo "Author: suhasdk18 <suhasdk18@gmail.com>"
echo "Version: 1.0.0"
echo ""

PROJECT_NAME="phishing-detection-system"

check_command() {
    if command -v $1 >/dev/null 2>&1; then
        echo "✅ $1 is installed"
        return 0
    else
        echo "❌ $1 is not installed"
        return 1
    fi
}

create_directories() {
    echo "📁 Creating directory structure..."
    
    mkdir -p data/{models,quarantine,datasets,logs,backups}
    mkdir -p logs
    mkdir -p templates
    mkdir -p static/{css,js,images}
    mkdir -p config
    mkdir -p tests/{unit,integration}
    mkdir -p monitoring/{grafana,prometheus}
    
    echo "✅ Directory structure created"
}

setup_python_env() {
    echo "🐍 Setting up Python virtual environment..."
    
    if check_command python3; then
        python3 -m venv venv
        
        if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
        
        echo "📦 Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        
        echo "✅ Python environment setup complete"
    else
        echo "❌ Python 3 is required but not installed"
        exit 1
    fi
}

setup_config() {
    echo "⚙️  Setting up configuration files..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env file - please edit with your settings"
    fi
    
    if [ ! -f config.yml ]; then
        echo "📝 config.yml already exists - using existing configuration"
    fi
    
    echo "✅ Configuration files ready"
}

init_database() {
    echo "🗄️  Initializing databases..."
    
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    python main.py --init-db
    
    echo "✅ Database initialization complete"
}

setup_docker() {
    if check_command docker && check_command docker-compose; then
        echo "🐳 Docker setup available"
        echo "   Run 'docker-compose up -d' to start all services"
        return 0
    else
        echo "⚠️  Docker not available - manual setup required"
        return 1
    fi
}

start_services() {
    echo "🚀 Starting services..."
    
    if check_command docker-compose; then
        echo "Starting services with Docker Compose..."
        docker-compose up -d
        echo "✅ All services started"
        echo ""
        echo "🌐 Service URLs:"
        echo "   Dashboard: http://localhost:5000"
        echo "   MailHog:   http://localhost:8025"
        echo "   Grafana:   http://localhost:3000"
        echo "   Kibana:    http://localhost:5601"
    else
        echo "Starting services manually..."
        
        echo "Starting MailHog for email testing..."
        if check_command docker; then
            docker run -d -p 1025:1025 -p 8025:8025 --name mailhog mailhog/mailhog
            echo "✅ MailHog started at http://localhost:8025"
        else
            echo "⚠️  Please install Docker to run MailHog"
        fi
        
        echo ""
        echo "To start the detection system:"
        echo "  python main.py --mode monitor"
        echo ""
        echo "To start the web dashboard:"
        echo "  python app.py"
    fi
}

run_tests() {
    echo "🧪 Running system tests..."
    
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    python main.py --mode test
    
    echo "✅ System tests completed"
}

show_usage() {
    echo ""
    echo "📋 Next Steps:"
    echo "=============="
    echo ""
    echo "1. Edit configuration:"
    echo "   nano .env"
    echo "   nano config.yml"
    echo ""
    echo "2. Start monitoring:"
    echo "   python main.py --mode monitor"
    echo ""
    echo "3. Start web dashboard:"
    echo "   python app.py"
    echo ""
    echo "4. Train ML model (optional):"
    echo "   python main.py --mode train --dataset data/phishing_dataset.csv"
    echo ""
    echo "5. Access services:"
    echo "   • Dashboard: http://localhost:5000"
    echo "   • MailHog:   http://localhost:8025"
    echo ""
    echo "For help: python main.py --help"
    echo ""
}

main() {
    echo "Starting setup process..."
    echo ""
    
    echo "🔍 Checking prerequisites..."
    check_command git
    check_command python3 || check_command python
    
    create_directories
    
    if [ -f requirements.txt ]; then
        setup_python_env
    else
        echo "❌ requirements.txt not found"
        exit 1
    fi
    
    setup_config
    init_database
    
    echo ""
    echo "🎯 Setup Options:"
    echo "1) Start with Docker (recommended)"
    echo "2) Manual setup"
    echo "3) Run tests only"
    echo "4) Skip service startup"
    
    read -p "Choose option (1-4): " choice
    
    case $choice in
        1)
            if setup_docker; then
                start_services
            else
                echo "Docker not available, falling back to manual setup"
                setup_docker
            fi
            ;;
        2)
            start_services
            ;;
        3)
            run_tests
            ;;
        4)
            echo "⏭️  Skipping service startup"
            ;;
        *)
            echo "Invalid choice, skipping service startup"
            ;;
    esac
    
    echo ""
    echo "🎉 Setup completed successfully!"
    show_usage
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi