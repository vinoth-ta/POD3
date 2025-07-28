#!/bin/bash

# STTM-to-Notebook Generator Setup Script
# This script automates the setup process for the STTM-to-Notebook generator

echo "🚀 Setting up STTM-to-Notebook Generator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip are available"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file template..."
    cat > .env << EOF
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-07-01-preview
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
EOF
    echo "⚠️  Please update the .env file with your Azure OpenAI credentials"
else
    echo "✅ .env file already exists"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Update the .env file with your Azure OpenAI credentials"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start the application: uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "📖 For more information, see README.md" 