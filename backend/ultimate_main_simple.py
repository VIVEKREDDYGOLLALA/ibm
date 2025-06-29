#!/usr/bin/env python3
"""
Ultimate GitHub-Jira AI Assistant - Simplified and Optimized Version
"""

import os
import sys
import logging
import json
import time
import base64
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# CONFIGURATION
# ================================

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment
load_environment()

# ================================
# JIRA SERVICE
# ================================

class JiraService:
    """Jira service for issue management"""
    
    def __init__(self):
        self.base_url = os.getenv('JIRA_URL', 'https://your-domain.atlassian.net').rstrip('/')
        self.username = os.getenv('JIRA_EMAIL')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([self.username, self.api_token]):
            logger.warning("Jira credentials not configured. Some features may not work.")
            return
        
        # Create auth headers
        auth_string = f"{self.username}:{self.api_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"✅ Jira service initialized for {self.base_url}")
        self._test_connection()
    
    def _test_connection(self):
        """Test Jira connection"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ Jira connection successful - User: {user_data.get('displayName', 'Unknown')}")
            else:
                logger.warning(f"Jira connection issue: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Jira connection test failed: {e}")
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed issue information"""
        if not hasattr(self, 'headers'):
            return {
                'key': issue_key,
                'summary': f'Mock issue: {issue_key}',
                'description': 'This is a mock issue for testing purposes',
                'status': {'name': 'To Do'},
                'priority': {'name': 'Medium'},
                'assignee': {'displayName': 'Test User'},
                'created': '2024-01-01T00:00:00.000Z'
            }
        
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'key': data['key'],
                    'summary': data['fields']['summary'],
                    'description': data['fields'].get('description', ''),
                    'status': data['fields']['status'],
                    'priority': data['fields'].get('priority'),
                    'assignee': data['fields'].get('assignee'),
                    'created': data['fields']['created'],
                    'issuetype': data['fields'].get('issuetype'),
                    'labels': data['fields'].get('labels', []),
                    'components': data['fields'].get('components', [])
                }
            else:
                logger.error(f"Failed to get issue {issue_key}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {e}")
            return None
    
    def get_issues(self, project_key: str, status: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Get issues from Jira project using JQL"""
        if not hasattr(self, 'headers'):
            return []
        
        jql = f"project = {project_key}"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY updated DESC"
        
        try:
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,description,status,assignee,created,updated,issuetype,priority,labels,components'
            }
            
            response = requests.get(
                f"{self.base_url}/rest/api/3/search",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                logger.info(f"✅ Retrieved {len(issues)} issues from project {project_key}")
                return issues
            else:
                logger.error(f"Failed to fetch issues: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch Jira issues: {str(e)}")
            return []
    
    def get_projects(self) -> List[Dict]:
        """Get all accessible projects"""
        if not hasattr(self, 'headers'):
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                projects = response.json()
                logger.info(f"✅ Fetched {len(projects)} projects")
                return projects
            else:
                logger.error(f"Failed to fetch projects: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            return []

# ================================
# SIMPLIFIED GITHUB REPOSITORY ANALYZER
# ================================

class SimpleGitHubAnalyzer:
    """Simplified GitHub repository analyzer optimized for speed"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
        self.base_url = 'https://api.github.com'
        logger.info(f"✅ GitHub analyzer initialized (token: {'Yes' if self.github_token else 'No'})")
    
    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL to extract owner and repo"""
        try:
            url = url.replace('https://github.com/', '').replace('http://github.com/', '')
            url = url.rstrip('/')
            parts = url.split('/')
            if len(parts) >= 2:
                return {'owner': parts[0], 'repo': parts[1]}
            return None
        except Exception as e:
            logger.error(f"Failed to parse GitHub URL {url}: {e}")
            return None
    
    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict]:
        """Get basic repository information"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get repo info: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return None
    
    def get_directory_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Get repository directory contents"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                if response.status_code != 404:
                    logger.warning(f"Failed to get directory contents for {path}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting directory contents: {e}")
            return []
    
    def analyze_repository_simple(self, github_url: str, ticket_context: str = "") -> Dict:
        """Perform quick repository analysis"""
        try:
            logger.info(f"🔍 Starting quick analysis of {github_url}")
            
            # Parse URL
            parsed = self.parse_github_url(github_url)
            if not parsed:
                return {"error": "Invalid GitHub URL"}
            
            owner, repo = parsed['owner'], parsed['repo']
            
            # Get repository information
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return {"error": "Repository not found or not accessible"}
            
            # Quick scan of root directory only
            root_contents = self.get_directory_contents(owner, repo, "")
            
            # Simple file analysis
            relevant_files = []
            file_types = {'css': 0, 'js': 0, 'jsx': 0, 'ts': 0, 'tsx': 0, 'html': 0, 'json': 0}
            
            for item in root_contents:
                if item['type'] == 'file':
                    file_name = item['name'].lower()
                    file_ext = Path(file_name).suffix.lstrip('.')
                    
                    if file_ext in file_types:
                        file_types[file_ext] += 1
                    
                    # Check for relevant files based on ticket context
                    if any(keyword in file_name for keyword in ['style', 'color', 'theme', 'nav', 'header', 'component']):
                        relevant_files.append({
                            'path': item['path'],
                            'name': item['name'],
                            'type': file_ext,
                            'size': item.get('size', 0)
                        })
            
            # Determine framework
            framework = "unknown"
            if any(item['name'] == 'package.json' for item in root_contents):
                framework = "nodejs"
            if any(item['name'] == 'next.config.js' for item in root_contents):
                framework = "nextjs"
            elif file_types['jsx'] > 0 or file_types['tsx'] > 0:
                framework = "react"
            
            result = {
                "success": True,
                "repository": {
                    "name": repo_info['name'],
                    "description": repo_info.get('description', ''),
                    "language": repo_info.get('language', ''),
                    "stars": repo_info.get('stargazers_count', 0),
                    "forks": repo_info.get('forks_count', 0)
                },
                "framework": framework,
                "file_types": file_types,
                "relevant_files": relevant_files[:5],  # Top 5 files
                "total_files_analyzed": len(relevant_files),
                "analysis_type": "quick"
            }
            
            logger.info(f"✅ Quick repository analysis complete: {len(relevant_files)} relevant files found")
            return result
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {"error": f"Repository analysis failed: {str(e)}"}

# ================================
# IBM GRANITE SERVICE
# ================================

class GraniteAPI:
    """Simplified IBM Granite API client"""
    
    def __init__(self, api_key: str, project_id: str, base_url: str = "https://eu-de.ml.cloud.ibm.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url
        self.generation_endpoint = f"{base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
        
        if not self.api_key or not self.project_id:
            logger.warning("IBM Granite configuration incomplete")
    
    def get_bearer_token(self):
        """Generate Bearer token from IBM API key"""
        if self.bearer_token and time.time() < self.token_expires_at:
            return self.bearer_token
        
        logger.info("🔄 Generating new Bearer token...")
        
        token_url = "https://iam.cloud.ibm.com/identity/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': self.api_key
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.bearer_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in - 300
                
                logger.info(f"✅ Bearer token generated! Expires in {expires_in//60} minutes")
                return self.bearer_token
            else:
                logger.error(f"❌ Error generating Bearer token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception generating Bearer token: {e}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.2) -> str:
        """Generate text using IBM Granite"""
        bearer_token = self.get_bearer_token()
        if not bearer_token:
            logger.error("Failed to get Bearer token")
            return ""
        
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "input": prompt,
            "parameters": {
                "decoding_method": "sample" if temperature > 0 else "greedy",
                "max_new_tokens": max_tokens,
                "min_new_tokens": 0,
                "stop_sequences": [],
                "repetition_penalty": 1
            },
            "model_id": "ibm/granite-3-8b-instruct",
            "project_id": self.project_id
        }
        
        if payload["parameters"]["decoding_method"] == "sample":
            payload["parameters"]["temperature"] = temperature
        
        try:
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return ""
                
            result = response.json()
            
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                return generated_text
            else:
                logger.error(f"Unexpected response format: {result}")
                return ""
                
        except Exception as e:
            logger.error(f"API Error: {e}")
            return ""
    
    def create_implementation_prompt(self, ticket_data: Dict, repo_analysis: Optional[Dict] = None) -> str:
        """Create implementation prompt with repository context"""
        
        # Safe field extraction
        title = ticket_data.get('summary') or 'N/A'
        description = ticket_data.get('description') or 'N/A'
        issue_type = 'N/A'
        priority = 'N/A'
        status = 'N/A'
        
        if ticket_data.get('issuetype') and isinstance(ticket_data['issuetype'], dict):
            issue_type = ticket_data['issuetype'].get('name', 'N/A')
        if ticket_data.get('priority') and isinstance(ticket_data['priority'], dict):
            priority = ticket_data['priority'].get('name', 'N/A')
        if ticket_data.get('status') and isinstance(ticket_data['status'], dict):
            status = ticket_data['status'].get('name', 'N/A')
        
        # Build repository context
        repo_context = ""
        if repo_analysis and repo_analysis.get("success"):
            repo_info = repo_analysis.get("repository", {})
            framework = repo_analysis.get("framework", "unknown")
            file_types = repo_analysis.get("file_types", {})
            relevant_files = repo_analysis.get("relevant_files", [])
            
            repo_context = f"""
🔍 REPOSITORY ANALYSIS:

📋 Project: {repo_info.get('name', 'Unknown')}
📝 Description: {repo_info.get('description', 'No description')}
🔤 Language: {repo_info.get('language', 'Unknown')}
🏗️ Framework: {framework}
⭐ Stars: {repo_info.get('stars', 0)}

📂 FILE TYPES FOUND:
{', '.join(f'{ext}: {count}' for ext, count in file_types.items() if count > 0)}

📄 RELEVANT FILES:
{chr(10).join(f'• {f["path"]} ({f["type"]})' for f in relevant_files)}
"""
        
        prompt = f"""You are a senior software engineer. Create a comprehensive implementation plan for this Jira ticket.

📋 JIRA TICKET:
Title: {title}
Description: {description}
Type: {issue_type}
Priority: {priority}
Status: {status}
{repo_context}

🎯 Create a detailed implementation plan that:
1. Uses the repository structure and framework identified above
2. Provides specific, actionable steps
3. Includes code examples
4. Considers the existing codebase patterns

## 📋 EXECUTIVE SUMMARY
- What exactly needs to be implemented
- Complexity assessment
- Estimated effort

## 🛠️ TECHNICAL APPROACH
- Detailed strategy
- Files to modify/create
- Implementation approach

## 📁 FILE MODIFICATIONS
### Files to modify:
{f"Based on the {framework} framework and files found above" if repo_context else "Recommended files to create/modify"}

## 🔧 IMPLEMENTATION STEPS
1. **Preparation**
   - Environment setup
   - Code review

2. **Implementation**
   - Step-by-step changes
   - Code examples

3. **Testing**
   - Testing strategy
   - Validation steps

## 💻 CODE EXAMPLES
Provide specific code examples for the key changes needed.

## ⏱️ TIMELINE
- Estimated development time
- Testing time
- Total effort

Keep the plan practical and actionable."""

        return prompt
    
    def analyze_jira_ticket(self, ticket_data: Dict, repo_analysis: Optional[Dict] = None) -> Dict:
        """Analyze Jira ticket and generate implementation plan"""
        try:
            # Create prompt
            prompt = self.create_implementation_prompt(ticket_data, repo_analysis)
            
            # Generate implementation plan
            response = self.generate(prompt, max_tokens=1500, temperature=0.2)
            
            if response:
                return {
                    "success": True,
                    "analysis": response.strip(),
                    "ticket_key": ticket_data.get('key', 'N/A'),
                    "ticket_summary": ticket_data.get('summary') or 'N/A',
                    "model_used": "ibm/granite-3-8b-instruct",
                    "generated_at": datetime.now().isoformat(),
                    "repository_analyzed": bool(repo_analysis and repo_analysis.get("success")),
                    "analysis_type": repo_analysis.get("analysis_type", "none") if repo_analysis else "none"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate analysis",
                    "ticket_key": ticket_data.get('key', 'N/A')
                }
                
        except Exception as e:
            logger.error(f"Error analyzing ticket: {e}")
            return {
                "success": False,
                "error": f"Error analyzing ticket: {str(e)}",
                "ticket_key": ticket_data.get('key', 'N/A')
            }
    
    def check_connection(self) -> Dict:
        """Test connection to IBM Granite API"""
        try:
            if not self.api_key or not self.project_id:
                return {"status": "error", "message": "IBM Granite configuration incomplete"}
            
            token = self.get_bearer_token()
            if not token:
                return {"status": "error", "message": "Failed to generate Bearer token"}
            
            return {
                "status": "success",
                "message": "Successfully connected to IBM Granite",
                "model": "ibm/granite-3-8b-instruct"
            }
                
        except Exception as e:
            return {"status": "error", "message": f"Connection test failed: {str(e)}"}

# ================================
# GLOBAL SERVICE INSTANCES
# ================================

API_KEY = os.getenv('IBM_GRANITE_API_KEY', '')
PROJECT_ID = os.getenv('IBM_PROJECT_ID', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

granite_api = GraniteAPI(API_KEY, PROJECT_ID)
jira_service = JiraService()
github_analyzer = SimpleGitHubAnalyzer(GITHUB_TOKEN)

# ================================
# FASTAPI APPLICATION
# ================================

app = FastAPI(
    title="GitHub-Jira AI Assistant - Simple",
    version="3.0.0",
    description="Simplified AI assistant with basic repository analysis"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8004",
        "http://127.0.0.1:8004",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# API ENDPOINTS
# ================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GitHub-Jira AI Assistant - Simplified Version",
        "version": "3.0.0",
        "services": {
            "granite": "IBM Granite 3-8B Instruct",
            "jira": "Atlassian Jira Cloud API",
            "github": "Simple GitHub Analysis API"
        },
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """Health check"""
    try:
        granite_status = granite_api.check_connection()
        jira_status = {"status": "success", "message": "Jira configured"} if hasattr(jira_service, 'headers') else {"status": "warning", "message": "Jira not configured"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "granite": granite_status,
                "jira": jira_status,
                "github": {"status": "success", "message": "Simple GitHub analyzer ready"}
            },
            "configuration": {
                "granite_configured": bool(API_KEY and PROJECT_ID),
                "jira_configured": bool(hasattr(jira_service, 'headers')),
                "github_configured": bool(GITHUB_TOKEN)
            },
            "version": "3.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/api/jira/projects")
async def get_jira_projects():
    """Get Jira projects"""
    try:
        projects = jira_service.get_projects()
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jira/issues")
async def get_jira_issues(
    project_key: str = Query(..., description="Jira project key"),
    status: Optional[str] = Query(None, description="Filter by status"),
    max_results: int = Query(50, description="Maximum number of results")
):
    """Get Jira issues"""
    try:
        issues = jira_service.get_issues(project_key, status, max_results)
        return {"issues": issues}
    except Exception as e:
        logger.error(f"Failed to get issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-implementation-plan")
async def generate_implementation_plan(request_data: dict):
    """Generate implementation plan with simple repository analysis"""
    try:
        # Enhanced logging
        logger.info("=" * 60)
        logger.info("🚀 IMPLEMENTATION PLAN REQUEST RECEIVED")
        logger.info(f"📦 Request data: {request_data}")
        
        issue_key = request_data.get('issue_key')
        github_url = request_data.get('github_url')
        
        logger.info(f"🎫 Issue key: {issue_key}")
        logger.info(f"🔗 GitHub URL: '{github_url}'")
        logger.info("=" * 60)
        
        if not issue_key:
            raise HTTPException(status_code=400, detail="issue_key is required")
        
        logger.info(f"🎯 Generating implementation plan for {issue_key}")
        
        # Get issue details from Jira
        issue_data = jira_service.get_issue(issue_key)
        if issue_data is None:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
        
        # Perform simple repository analysis if URL provided
        repo_analysis = None
        if github_url:
            logger.info(f"🔍 Performing simple repository analysis: {github_url}")
            try:
                summary = issue_data.get('summary') or ''
                description = issue_data.get('description') or ''
                ticket_context = f"{summary} {description}".strip()
                
                repo_analysis = github_analyzer.analyze_repository_simple(github_url, ticket_context)
                
                if repo_analysis.get("success"):
                    logger.info(f"✅ Repository analysis complete: {repo_analysis.get('total_files_analyzed', 0)} files found")
                else:
                    logger.warning(f"Repository analysis failed: {repo_analysis.get('error')}")
                    
            except Exception as e:
                logger.error(f"❌ Repository analysis exception: {e}")
                repo_analysis = None
        
        # Generate implementation plan
        plan_result = granite_api.analyze_jira_ticket(issue_data, repo_analysis)
        
        if plan_result.get("success"):
            response_data = {
                "success": True,
                "issue_key": issue_key,
                "issue_summary": plan_result.get("ticket_summary"),
                "implementation_plan": plan_result.get("analysis"),
                "model_used": plan_result.get("model_used"),
                "generated_at": plan_result.get("generated_at"),
                "repository_analyzed": plan_result.get("repository_analyzed", False),
                "analysis_type": plan_result.get("analysis_type", "none"),
                "ai_powered": True
            }
            
            # Include repository info if available
            if repo_analysis and repo_analysis.get("success"):
                response_data["repository_info"] = {
                    "name": repo_analysis.get("repository", {}).get("name"),
                    "language": repo_analysis.get("repository", {}).get("language"),
                    "framework": repo_analysis.get("framework"),
                    "total_files_analyzed": repo_analysis.get("total_files_analyzed", 0)
                }
            
            logger.info(f"✅ Implementation plan generated successfully for {issue_key}")
            return response_data
        else:
            error_detail = plan_result.get("error", "Failed to generate implementation plan")
            logger.error(f"❌ Plan generation failed: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Implementation plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate implementation plan: {str(e)}")

# ================================
# APPLICATION STARTUP
# ================================

@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("🚀 Starting Simplified GitHub-Jira AI Assistant v3.0")
    logger.info(f"🤖 IBM Granite configured: {bool(API_KEY and PROJECT_ID)}")
    logger.info(f"📋 Jira configured: {bool(hasattr(jira_service, 'headers'))}")
    logger.info(f"🔗 GitHub configured: {bool(GITHUB_TOKEN)}")
    logger.info("✅ Application startup completed")

# ================================
# RUN APPLICATION
# ================================

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def find_available_port(start_port=8004):
        """Find an available port starting from the given port"""
        port = start_port
        while port < start_port + 100:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
        return None
    
    HOST = "0.0.0.0"
    PORT = int(os.getenv('PORT', '8004'))
    
    # Check if port is available
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', PORT))
    except OSError:
        logger.warning(f"Port {PORT} is in use, finding alternative...")
        PORT = find_available_port(8004)
        if PORT is None:
            logger.error("No available ports found")
            sys.exit(1)
        logger.info(f"Using alternative port: {PORT}")
    
    print("🚀 Simplified GitHub-Jira AI Assistant v3.0")
    print(f"📡 Server: http://{HOST}:{PORT}")
    print(f"📖 Docs: http://{HOST}:{PORT}/docs")
    print(f"🔍 Health: http://{HOST}:{PORT}/api/health")
    print()
    
    try:
        uvicorn.run(
            "ultimate_main_simple:app",
            host=HOST,
            port=PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1) 