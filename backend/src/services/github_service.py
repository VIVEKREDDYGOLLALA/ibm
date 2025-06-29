# src/services/github_service.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
from github import Github
from src.core.config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.client = None
        if settings.GITHUB_TOKEN:
            try:
                self.client = Github(settings.GITHUB_TOKEN)
                # Test connection
                user = self.client.get_user()
                logger.info(f"GitHub client initialized for user: {user.login}")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.client = None
        else:
            logger.warning("GitHub token not provided")
    
    async def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information"""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            repo = await loop.run_in_executor(
                None,
                lambda: self.client.get_repo(repo_name)
            )
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "languages": dict(repo.get_languages()),
                "size": repo.size,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            }
        except Exception as e:
            logger.error(f"Failed to get repository info for {repo_name}: {e}")
            raise Exception(f"Failed to get repository information: {str(e)}")
    
    async def search_code(self, query: str, repo_name: Optional[str] = None) -> List[Dict]:
        """Search code in repositories"""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            search_query = query
            if repo_name:
                search_query += f" repo:{repo_name}"
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.client.search_code(search_query)[:10])  # Limit results
            )
            
            return [
                {
                    "name": result.name,
                    "path": result.path,
                    "repository": result.repository.full_name,
                    "url": result.html_url,
                    "sha": result.sha
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Failed to search code: {e}")
            raise Exception(f"Code search failed: {str(e)}")