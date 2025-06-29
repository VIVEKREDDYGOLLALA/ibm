#!/usr/bin/env python3
"""
GitHub-Jira AI Assistant - Backend Runner
"""
import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting GitHub-Jira AI Assistant Backend")
    print(f"📡 Server: http://{settings.host}:{settings.port}")
    print(f"📖 Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🔍 Health: http://{settings.host}:{settings.port}/api/health")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 