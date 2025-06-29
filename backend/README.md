# GitHub-Jira AI Assistant - Backend

AI-powered backend service for analyzing Jira tickets and generating implementation plans using IBM Granite models.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the backend directory:

```env
# IBM Granite AI Configuration (REQUIRED)
IBM_GRANITE_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_ibm_watsonx_project_id_here

# Jira Configuration (REQUIRED for Jira integration)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token_here

# GitHub Configuration (OPTIONAL)
GITHUB_TOKEN=your_github_personal_access_token_here

# Application Configuration
DEBUG=False
API_HOST=127.0.0.1
API_PORT=8000
```

### 3. Run the Application

```bash
# Simple run
python run.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 🏗️ Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   │   ├── __init__.py
│   │   └── config.py        # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── granite_service.py  # IBM Granite AI service
│   │   └── jira_service.py     # Jira integration
│   └── api/
│       ├── __init__.py
│       └── routes.py        # API endpoints
├── requirements.txt
├── run.py                   # Application runner
└── README.md
```

## 🔧 Services

### IBM Granite Service
- Uses the exact same connection pattern as `granite_test.py`
- Bearer token authentication with automatic renewal
- Jira ticket analysis and implementation plan generation
- Model: `ibm/granite-3-8b-instruct`

### Jira Service
- Secure API integration with Jira Cloud
- Issue fetching and project management
- Proper error handling and logging

## 📡 API Endpoints

### Health & Status
- `GET /` - Root endpoint with app info
- `GET /api/health` - Comprehensive health check
- `GET /health` - Simple health check

### Jira Integration
- `GET /api/jira/issues?project_key=PROJ&status=In Progress` - Get project issues
- `GET /api/jira/projects` - Get accessible projects
- `GET /api/jira/issue/{issue_key}` - Get specific issue

### AI-Powered Analysis
- `POST /api/generate-implementation-plan` - Generate implementation plan
- `POST /api/validate-pr` - Validate pull request

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Generate Implementation Plan
```bash
curl -X POST "http://localhost:8000/api/generate-implementation-plan" \
     -H "Content-Type: application/json" \
     -d '{
       "jira_issue_key": "PROJ-123",
       "github_repo_url": "https://github.com/your-org/your-repo"
     }'
```

## 🔐 Configuration Guide

### IBM Granite Setup
1. Sign up for IBM Cloud: https://cloud.ibm.com/
2. Access IBM watsonx.ai: https://dataplatform.cloud.ibm.com/wx/
3. Create a project in watsonx.ai
4. Generate API key from IBM Cloud IAM
5. Get project ID from watsonx.ai project settings

### Jira Setup
1. Get your Jira Cloud URL (e.g., `https://yourcompany.atlassian.net`)
2. Use your email address for `JIRA_EMAIL`
3. Generate API token: Account Settings → Security → API tokens → Create

## 🛠️ Development

### Run in Development Mode
```bash
# With auto-reload
python run.py

# Or set DEBUG=True in .env and run
uvicorn app.main:app --reload
```

### Code Structure
- **Clean Architecture**: Separation of concerns with clear layers
- **Dependency Injection**: Services are properly injected
- **Error Handling**: Comprehensive error handling and logging
- **Type Safety**: Full type hints and Pydantic validation
- **Documentation**: Auto-generated API docs with FastAPI

### Adding New Features
1. Add models to `app/models/schemas.py`
2. Implement service logic in `app/services/`
3. Add API endpoints in `app/api/routes.py`
4. Update dependencies in `requirements.txt`

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build image
docker build -t github-jira-assistant .

# Run container
docker run -p 8000:8000 --env-file .env github-jira-assistant
```

### Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 📊 Monitoring

### Logs
All services provide structured logging with emojis for easy identification:
- 🚀 Application startup
- 🤖 IBM Granite operations
- ✅ Successful operations
- ❌ Errors and failures
- 🔄 Token renewals

### Health Monitoring
The `/api/health` endpoint provides detailed service status for monitoring tools.

## 🔧 Troubleshooting

### Common Issues

1. **"IBM Granite API key missing"**
   - Ensure `IBM_GRANITE_API_KEY` is set in `.env`
   - Verify the API key is correct

2. **"Jira service not available"**
   - Check `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN`
   - Verify network connectivity to Jira

3. **"Authentication failed"**
   - Regenerate IBM Cloud API key
   - Check Jira API token validity

### Debug Mode
Set `DEBUG=True` in `.env` for detailed error messages and auto-reload.

## 📝 License

MIT License - See LICENSE file for details. 