# main.py (place this in /mnt/c/Users/golla/ibm/backend/)
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager

from src.services.jira_service import JiraService
from src.services.github_service import GitHubService
from src.services.granite_service import GraniteService
from src.services.pdf_service import PDFService
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
jira_service = None
github_service = None
granite_service = None
pdf_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global jira_service, github_service, granite_service, pdf_service
    try:
        logger.info("Initializing services...")
        
        # Initialize services
        jira_service = JiraService()
        github_service = GitHubService()
        granite_service = GraniteService()
        pdf_service = PDFService()
        
        logger.info("All services initialized successfully")
        
        # Test Jira connection
        if jira_service:
            try:
                projects = await jira_service.get_projects()
                logger.info(f"Jira connected - Found {len(projects)} projects")
            except Exception as e:
                logger.warning(f"Jira connection test failed: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't fail the startup, just log the error
    
    yield
    
    # Shutdown
    logger.info("Shutting down services")

app = FastAPI(
    title="Jira-GitHub Analyzer API",
    description="API for analyzing Jira tickets and GitHub repositories",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Jira-GitHub Analyzer API is running",
        "status": "healthy",
        "version": "1.0.0",
                    "services": {
                "jira": jira_service is not None,
                "github": github_service is not None,
                "granite": granite_service is not None,
                "pdf": pdf_service is not None
            }
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "timestamp": "2025-06-27T12:00:00Z",
        "services": {},
        "configuration": {
            "jira_url": settings.JIRA_URL if settings.JIRA_URL else "Not configured",
            "github_token": "Configured" if settings.GITHUB_TOKEN else "Not configured"
        }
    }
    
    # Check Jira service
    try:
        if jira_service and jira_service.jira:
            projects = await jira_service.get_projects()
            health_status["services"]["jira"] = {
                "status": "connected",
                "projects_count": len(projects),
                "url": settings.JIRA_URL
            }
        else:
            health_status["services"]["jira"] = {
                "status": "not_initialized",
                "error": "Check JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env"
            }
    except Exception as e:
        health_status["services"]["jira"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check other services
    health_status["services"]["github"] = {
        "status": "ready" if github_service else "not_initialized"
    }
    health_status["services"]["granite"] = {
        "status": "ready" if granite_service else "not_initialized"
    }
    health_status["services"]["pdf"] = {
        "status": "ready" if pdf_service else "not_initialized"
    }
    
    return health_status

@app.get("/api/jira/projects")
async def get_jira_projects():
    """Get all accessible Jira projects"""
    if not jira_service or not jira_service.jira:
        raise HTTPException(
            status_code=503, 
            detail="Jira service not available. Check your Jira configuration in .env file."
        )
    
    try:
        projects = await jira_service.get_projects()
        return {
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        logger.error(f"Failed to fetch projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@app.get("/api/jira/issues")
async def get_jira_issues(
    project_key: str = Query(..., description="Jira project key (e.g., SCRUM)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    max_results: int = Query(50, description="Maximum number of results")
):
    """Get Jira issues for a project"""
    if not jira_service or not jira_service.jira:
        raise HTTPException(
            status_code=503, 
            detail="Jira service not available. Check your Jira configuration in .env file."
        )
    
    try:
        logger.info(f"Fetching issues for project: {project_key}")
        issues = await jira_service.get_issues(project_key, status, max_results)
        
        # Transform issues for frontend
        transformed_issues = []
        for issue in issues:
            fields = issue.get("fields", {})
            transformed_issues.append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "description": fields.get("description"),
                "status": fields.get("status", {}).get("name") if fields.get("status") else None,
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
                "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "labels": fields.get("labels", []),
                "components": [comp.get("name") for comp in fields.get("components", [])]
            })
        
        return {
            "issues": transformed_issues,
            "count": len(transformed_issues),
            "project_key": project_key
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch issues for {project_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

@app.get("/api/jira/issues/{issue_key}")
async def get_jira_issue(issue_key: str):
    """Get detailed information for a specific Jira issue"""
    if not jira_service or not jira_service.jira:
        raise HTTPException(status_code=503, detail="Jira service not available")
    
    try:
        issue = await jira_service.get_issue(issue_key)
        return {
            "issue": {
                "key": issue.key,
                "summary": issue.summary,
                "description": issue.description,
                "acceptance_criteria": issue.acceptance_criteria,
                "story_points": issue.story_points,
                "assignee": issue.assignee,
                "status": issue.status,
                "priority": getattr(issue, 'priority', 'Medium'),
                "issue_type": getattr(issue, 'issue_type', 'Story'),
                "labels": getattr(issue, 'labels', []),
                "components": getattr(issue, 'components', []),
                "created": issue.created.isoformat() if issue.created else None,
                "updated": issue.updated.isoformat() if issue.updated else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch issue {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue: {str(e)}")

@app.post("/api/jira/issues/{issue_key}/comments")
async def add_comment_to_issue(issue_key: str, comment_data: Dict[str, str]):
    """Add a comment to a Jira issue"""
    if not jira_service or not jira_service.jira:
        raise HTTPException(status_code=503, detail="Jira service not available")
    
    try:
        comment = comment_data.get("comment", "")
        if not comment:
            raise HTTPException(status_code=400, detail="Comment text is required")
        
        await jira_service.add_comment(issue_key, comment)
        return {"message": f"Comment added to {issue_key}", "success": True}
        
    except Exception as e:
        logger.error(f"Failed to add comment to {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@app.get("/api/github/repos/{owner}/{repo}")
async def get_github_repo(owner: str, repo: str):
    """Get GitHub repository information"""
    if not github_service:
        raise HTTPException(status_code=503, detail="GitHub service not available")
    
    try:
        repo_info = await github_service.get_repository_info(f"{owner}/{repo}")
        return repo_info
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repo {owner}/{repo}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository: {str(e)}")

@app.post("/api/analyze/ticket/{ticket_key}")
async def analyze_ticket(
    ticket_key: str,
    analysis_data: Dict[str, Any] = None
):
    """Analyze a Jira ticket and generate implementation plan"""
    if not jira_service or not jira_service.jira:
        raise HTTPException(status_code=503, detail="Jira service not available")
    
    try:
        # Get ticket details
        ticket = await jira_service.get_issue(ticket_key)
        
        # Basic analysis
        analysis_result = {
            "ticket_key": ticket_key,
            "summary": ticket.summary,
            "description": ticket.description,
            "status": ticket.status,
            "complexity_estimate": len(ticket.acceptance_criteria) * 2 if ticket.acceptance_criteria else 5,
            "implementation_suggestions": [
                "Break down the task into smaller components",
                "Create unit tests for each component",
                "Document the implementation approach",
                "Review code with team members"
            ]
        }
        
        return {"analysis": analysis_result}
        
    except Exception as e:
        logger.error(f"Failed to analyze ticket {ticket_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/agile/1.0/backlog/issue")
async def get_agile_backlog_branches(
    board_id: Optional[int] = Query(None, description="Board ID (optional, will use first available if not provided)")
):
    """
    Fetch all branches from agile backlog issues for connectivity check.
    This endpoint tests the Jira Agile API connectivity by fetching backlog issues
    and extracting potential branch names from them.
    """
    if not jira_service or not hasattr(jira_service, 'base_url'):
        raise HTTPException(
            status_code=503, 
            detail="Jira service not available. Check your Jira configuration in .env file."
        )
    
    try:
        logger.info(f"Fetching agile backlog branches with board_id: {board_id}")
        result = await jira_service.get_agile_backlog_branches(board_id)
        
        if result.get("success"):
            logger.info(f"Successfully fetched {result.get('total_branches_found', 0)} branches from board {result.get('board_id')}")
        else:
            logger.error(f"Failed to fetch branches: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch agile backlog branches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch branches: {str(e)}")

@app.post("/api/generate/pdf")
async def generate_pdf_report(report_data: Dict[str, Any]):
    """Generate PDF report"""
    if not pdf_service:
        raise HTTPException(status_code=503, detail="PDF service not available")
    
    try:
        pdf_path = await pdf_service.generate_report(report_data)
        return {"message": "PDF generated successfully", "path": pdf_path}
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )