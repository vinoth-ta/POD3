# 🚀 Quick Deployment Guide

## For New Users (Clone and Run)

### 1. Clone the Repository
```bash
git clone https://github.com/vinoth-ta/POD3.git
cd POD3
```

### 2. Run the Setup Script
```bash
./setup.sh
```

### 3. Configure Azure OpenAI
Edit the `.env` file with your credentials:
```env
AZURE_OPENAI_API_KEY=your_actual_api_key
AZURE_OPENAI_API_VERSION=2024-07-01-preview
AZURE_OPENAI_ENDPOINT=your_actual_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 4. Start the Application
```bash
source venv/bin/activate
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the API
The API will be available at: `http://localhost:8000`

## For Existing Users (Update)

### 1. Pull Latest Changes
```bash
git pull origin main
git checkout v1.0.0  # Optional: checkout specific version
```

### 2. Update Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Restart the Application
```bash
uvicorn sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app --host 0.0.0.0 --port 8000 --reload
```

## Version Information

- **Current Version**: v1.0.0
- **Status**: Production Ready ✅
- **Last Tested**: 2025-07-28
- **Azure OpenAI Model**: gpt-4o

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:8000 | xargs kill -9
```

### Virtual Environment Issues
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Template Not Found
Ensure you're in the correct directory and templates exist:
```bash
ls templates/silver/
```

## Support

- 📖 Full Documentation: See `README.md`
- 🐛 Issues: Create an issue in the repository
- 📧 Contact: [your-email@domain.com] 