#!/usr/bin/env python3
"""
Final GitHub-Jira AI Assistant - Production Ready
Combines the working Jira implementation from simple_main.py with exact granite_test.py approach
"""

import os
import sys
import logging
import json
import time
import base64
import requests
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# CONFIGURATION (Simple approach)
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

class Settings:
    """Simple settings class matching granite_test.py approach"""
    def __init__(self):
        # IBM Granite Settings (exact same as granite_test.py)
        self.IBM_GRANITE_API_KEY = os.getenv('IBM_GRANITE_API_KEY', '')
        self.IBM_PROJECT_ID = os.getenv('IBM_PROJECT_ID', '')
        
        # Jira Settings (from working simple_main.py)
        self.JIRA_URL = os.getenv('JIRA_URL', '').rstrip('/')
        self.JIRA_EMAIL = os.getenv('JIRA_EMAIL', '')
        self.JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '')
        
        # GitHub Settings
        self.GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
        
        # Server Settings
        self.HOST = "0.0.0.0"
        self.PORT = int(os.getenv('PORT', '8000'))

settings = Settings()

# ================================
# IBM GRANITE SERVICE (exact granite_test.py approach)
# ================================

class GraniteService:
    """IBM Granite service using exact same approach as granite_test.py"""
    
    def __init__(self):
        self.api_key = settings.IBM_GRANITE_API_KEY
        self.project_id = settings.IBM_PROJECT_ID
        self.base_url = "https://eu-de.ml.cloud.ibm.com"
        self.generation_endpoint = f"{self.base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
        
        if not self.api_key or not self.project_id:
            logger.warning("IBM Granite configuration incomplete - AI features will be limited")
    
    def get_bearer_token(self):
        """Generate Bearer token from IBM API key (exact copy from granite_test.py)"""
        
        # Check if we have a valid token
        if self.bearer_token and time.time() < self.token_expires_at:
            return self.bearer_token
        
        logger.info("🔄 Generating new Bearer token from API key...")
        
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
            logger.info(f"Token request status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.bearer_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                
                # Set expiration time (refresh 5 minutes early)
                self.token_expires_at = time.time() + expires_in - 300
                
                logger.info(f"✅ Bearer token generated! Expires in {expires_in//60} minutes")
                return self.bearer_token
            else:
                logger.error(f"❌ Error generating Bearer token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception generating Bearer token: {e}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Generate text using IBM Granite (exact copy from granite_test.py)"""
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
            "project_id": self.project_id,
            "moderations": {
                "hap": {
                    "input": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    },
                    "output": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    }
                },
                "pii": {
                    "input": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    },
                    "output": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    }
                },
                "granite_guardian": {
                    "input": {
                        "enabled": False,
                        "threshold": 1
                    }
                }
            }
        }
        
        # Add temperature only for sampling mode
        if payload["parameters"]["decoding_method"] == "sample":
            payload["parameters"]["temperature"] = temperature
        
        try:
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return ""
                
            result = response.json()
            
            # Handle text generation API response format
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                logger.info(f"Generated text length: {len(generated_text)} characters")
                return generated_text
            else:
                logger.error(f"Unexpected response format: {result}")
                return ""
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            return ""

    def analyze_jira_ticket(self, ticket_data: Dict) -> Dict:
        """Analyze Jira ticket and generate crystal clear implementation plan"""
        
        # Create comprehensive analysis prompt
        prompt = f"""You are a senior software engineer analyzing a Jira ticket to create a detailed implementation plan.

JIRA TICKET DETAILS:
Title: {ticket_data.get('summary', 'N/A')}
Description: {ticket_data.get('description', 'N/A')}
Type: {ticket_data.get('issuetype', {}).get('name', 'N/A')}
Priority: {ticket_data.get('priority', {}).get('name', 'N/A')}
Status: {ticket_data.get('status', {}).get('name', 'N/A')}

Create a comprehensive implementation plan with the following sections:

## EXECUTIVE SUMMARY
- Brief overview of what needs to be implemented
- Estimated complexity and effort

## TECHNICAL APPROACH
- High-level technical strategy
- Key technologies and frameworks to use
- Architecture considerations

## SPECIFIC FILE CHANGES
List specific files that need to be created or modified:
- File: path/to/file.ext
  Change: Specific changes needed
  Priority: high/medium/low

## IMPLEMENTATION STEPS
1. Step-by-step implementation sequence
2. Dependencies between steps
3. Order of operations

## CODE EXAMPLES
Provide key code snippets or examples showing:
- Important functions or classes to implement
- Configuration changes needed
- API endpoints or database changes

## DEPENDENCIES
- External libraries or services needed
- Infrastructure requirements
- Version requirements

## TESTING STRATEGY
- Unit tests needed
- Integration tests required
- Manual testing steps
- Acceptance criteria

## RISK ASSESSMENT
- Potential challenges or blockers
- Mitigation strategies
- Rollback plans

## ESTIMATED TIMELINE
- Development time estimate
- Testing time needed
- Deployment considerations

Please provide a clear, actionable plan that a developer can follow immediately."""

        try:
            response = self.generate(prompt, max_tokens=2000, temperature=0.3)
            
            if response:
                return {
                    "success": True,
                    "analysis": response.strip(),
                    "ticket_key": ticket_data.get('key', 'N/A'),
                    "ticket_summary": ticket_data.get('summary', 'N/A'),
                    "model_used": "ibm/granite-3-8b-instruct",
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate analysis",
                    "ticket_key": ticket_data.get('key', 'N/A')
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing ticket: {str(e)}",
                "ticket_key": ticket_data.get('key', 'N/A')
            }

    def check_connection(self) -> Dict:
        """Test connection to IBM Granite API"""
        try:
            if not self.api_key or not self.project_id:
                return {
                    "status": "error",
                    "message": "IBM Granite configuration incomplete"
                }
            
            # Test token generation
            token = self.get_bearer_token()
            if not token:
                return {
                    "status": "error",
                    "message": "Failed to generate Bearer token"
                }
            
            # Test simple generation
            test_response = self.generate("Hello", max_tokens=10, temperature=0)
            
            if test_response:
                return {
                    "status": "success",
                    "message": "Successfully connected to IBM Granite",
                    "model": "ibm/granite-3-8b-instruct"
                }
            else:
                return {
                    "status": "error", 
                    "message": "Failed to generate text response"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }

# ================================
# JIRA SERVICE (from working simple_main.py)
# ================================

class JiraService:
    """Jira service using the working implementation from simple_main.py"""
    
    def __init__(self):
        self.base_url = settings.JIRA_URL
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.headers = self._create_headers()
        
        if not all([self.base_url, self.email, self.api_token]):
            logger.warning("Jira configuration incomplete - Jira features will be limited")
        else:
            self._test_connection()
    
    def _create_headers(self) -> Dict[str, str]:
        """Create authentication headers for Jira API"""
        if not all([self.email, self.api_token]):
            return {}
        
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
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
    
    async def get_projects(self) -> List[Dict]:
        """Get all accessible projects"""
        if not self.headers:
            raise HTTPException(status_code=400, detail="Jira not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/project",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        projects = await response.json()
                        logger.info(f"✅ Fetched {len(projects)} projects")
                        return projects
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"Failed to fetch projects: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {str(e)}")
    
    async def get_issues(self, project_key: str, status: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Get issues from Jira project using JQL (from working simple_main.py)"""
        if not self.headers:
            raise HTTPException(status_code=400, detail="Jira not configured")
        
        # Build JQL query
        jql = f"project = {project_key}"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY updated DESC"
        
        logger.info(f"Searching issues with JQL: {jql}")
        
        try:
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,description,status,assignee,created,updated,issuetype,priority,labels,components'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/search",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        issues = data.get("issues", [])
                        logger.info(f"✅ Retrieved {len(issues)} issues from project {project_key}")
                        return issues
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"Failed to fetch issues: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch Jira issues for project {project_key}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch Jira issues: {str(e)}")
    
    async def get_issue(self, issue_key: str) -> Dict:
        """Get detailed issue information"""
        if not self.headers:
            raise HTTPException(status_code=400, detail="Jira not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}",
                    headers=self.headers,
                    params={'expand': 'changelog,attachments,comments'}
                ) as response:
                    if response.status == 200:
                        issue = await response.json()
                        logger.info(f"✅ Retrieved issue {issue_key}")
                        return issue
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"Failed to fetch issue: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch issue {issue_key}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch issue: {str(e)}")

# ================================
# GLOBAL SERVICE INSTANCES
# ================================

granite_service = GraniteService()
jira_service = JiraService()

# ================================
# FASTAPI APPLICATION
# ================================

app = FastAPI(
    title="GitHub-Jira AI Assistant",
    version="2.0.0",
    description="Production-ready AI assistant with IBM Granite and Jira integration"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
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
        "message": "GitHub-Jira AI Assistant - Production Ready",
        "version": "2.0.0",
        "services": {
            "granite": "IBM Granite 3-8B Instruct",
            "jira": "Atlassian Jira Cloud API",
            "github": "GitHub REST API"
        },
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "jira_projects": "/api/jira/projects",
            "jira_issues": "/api/jira/issues",
            "generate_plan": "/api/generate-implementation-plan"
        }
    }

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Test Granite connection
        granite_status = granite_service.check_connection()
        
        # Test Jira connection (simple check)
        jira_status = {"status": "success", "message": "Jira configured"} if jira_service.headers else {"status": "warning", "message": "Jira not configured"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "granite": granite_status,
                "jira": jira_status,
                "application": {"status": "success", "message": "Application running"}
            },
            "configuration": {
                "granite_configured": bool(settings.IBM_GRANITE_API_KEY and settings.IBM_PROJECT_ID),
                "jira_configured": bool(settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN),
                "github_configured": bool(settings.GITHUB_TOKEN)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/jira/projects")
async def get_jira_projects():
    """Get Jira projects"""
    try:
        projects = await jira_service.get_projects()
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
    """Get Jira issues (using working implementation from simple_main.py)"""
    try:
        issues = await jira_service.get_issues(project_key, status, max_results)
        return {"issues": issues}
    except Exception as e:
        logger.error(f"Failed to get issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jira/issue/{issue_key}")
async def get_jira_issue(issue_key: str):
    """Get specific Jira issue"""
    try:
        issue = await jira_service.get_issue(issue_key)
        return {"issue": issue}
    except Exception as e:
        logger.error(f"Failed to get issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-implementation-plan")
async def generate_implementation_plan(request_data: dict):
    """Generate AI-powered implementation plan using IBM Granite"""
    try:
        issue_key = request_data.get('issue_key')
        if not issue_key:
            raise HTTPException(status_code=400, detail="issue_key is required")
        
        # Get issue details from Jira
        logger.info(f"🎯 Generating implementation plan for {issue_key}")
        issue_data = await jira_service.get_issue(issue_key)
        
        # Generate implementation plan using IBM Granite
        plan_result = granite_service.analyze_jira_ticket(issue_data)
        
        if plan_result.get("success"):
            return {
                "success": True,
                "issue_key": issue_key,
                "issue_summary": plan_result.get("ticket_summary"),
                "implementation_plan": plan_result.get("analysis"),
                "model_used": plan_result.get("model_used"),
                "generated_at": plan_result.get("generated_at"),
                "ai_powered": True
            }
        else:
            raise HTTPException(status_code=500, detail=plan_result.get("error"))
            
    except Exception as e:
        logger.error(f"Failed to generate implementation plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-granite")
async def test_granite_generation(request_data: dict):
    """Test IBM Granite text generation"""
    try:
        prompt = request_data.get('prompt', 'Hello, this is a test.')
        max_tokens = request_data.get('max_tokens', 100)
        temperature = request_data.get('temperature', 0.7)
        
        response = granite_service.generate(prompt, max_tokens, temperature)
        
        return {
            "success": True,
            "prompt": prompt,
            "response": response,
            "model": "ibm/granite-3-8b-instruct",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Granite test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# APPLICATION STARTUP
# ================================

@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("🚀 Starting GitHub-Jira AI Assistant - Final Version")
    logger.info(f"🤖 IBM Granite configured: {bool(settings.IBM_GRANITE_API_KEY and settings.IBM_PROJECT_ID)}")
    logger.info(f"📋 Jira configured: {bool(settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)}")
    logger.info(f"🐙 GitHub configured: {bool(settings.GITHUB_TOKEN)}")
    logger.info("✅ Application startup completed")

# ================================
# RUN APPLICATION
# ================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 GitHub-Jira AI Assistant - Final Version")
    print(f"📡 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔍 Health: http://{settings.HOST}:{settings.PORT}/api/health")
    print()
    
    uvicorn.run(
        "final_main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    ) 