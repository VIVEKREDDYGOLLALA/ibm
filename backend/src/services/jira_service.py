# src/services/jira_service.py - Using Direct REST API
import requests
import base64
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging

from src.core.config import settings
from src.core.models import JiraStory

logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        self.base_url = settings.JIRA_URL.rstrip('/')
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.headers = self._create_headers()
        self._test_connection()
    
    def _create_headers(self) -> Dict[str, str]:
        """Create authentication headers for Jira API"""
        if not all([self.email, self.api_token]):
            raise Exception("Jira email and API token are required")
        
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
                logger.info(f"Jira connection successful - User: {user_data.get('displayName', 'Unknown')}")
            else:
                raise Exception(f"Jira connection failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Jira connection test failed: {e}")
            raise Exception(f"Jira connection test failed: {e}")
    
    async def get_projects(self) -> List[Dict]:
        """Get all accessible projects"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/project",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        projects = await response.json()
                        logger.info(f"Fetched {len(projects)} projects")
                        return projects
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch projects: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise Exception(f"Failed to fetch Jira projects: {str(e)}")
    
    async def get_issues(self, project_key: str, status: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Get issues from Jira project using JQL"""
        # Build JQL query
        jql = f"project = {project_key}"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY created DESC"
        
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
                        logger.info(f"Fetched {len(issues)} issues from project {project_key}")
                        return issues
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch issues: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch Jira issues for project {project_key}: {str(e)}")
            raise Exception(f"Failed to fetch Jira issues for project {project_key}: {str(e)}")
    
    async def get_issue(self, issue_key: str) -> JiraStory:
        """Get detailed issue information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}",
                    headers=self.headers,
                    params={'expand': 'changelog,attachments,comments'}
                ) as response:
                    if response.status == 200:
                        issue = await response.json()
                        return self._convert_to_jira_story(issue)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch issue: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch issue {issue_key}: {e}")
            raise Exception(f"Failed to fetch Jira issue {issue_key}: {str(e)}")
    
    def _convert_to_jira_story(self, issue: Dict) -> JiraStory:
        """Convert Jira API response to JiraStory model"""
        fields = issue["fields"]
        
        # Extract acceptance criteria from description
        description = fields.get("description") or ""
        if isinstance(description, dict):
            # Handle ADF (Atlassian Document Format)
            description = self._extract_text_from_adf(description)
        
        acceptance_criteria = self._extract_acceptance_criteria(description)
        
        # Get story points (might be in different custom fields)
        story_points = None
        for field_key in ["customfield_10001", "customfield_10002", "customfield_10003", "customfield_10016"]:
            if fields.get(field_key):
                story_points = fields[field_key]
                break
        
        return JiraStory(
            key=issue["key"],
            summary=fields.get("summary", ""),
            description=description,
            acceptance_criteria=acceptance_criteria,
            story_points=story_points,
            assignee=fields["assignee"]["displayName"] if fields.get("assignee") else None,
            status=fields["status"]["name"] if fields.get("status") else "Unknown",
            priority=fields["priority"]["name"] if fields.get("priority") else "Medium",
            issue_type=fields["issuetype"]["name"] if fields.get("issuetype") else "Story",
            labels=fields.get("labels", []),
            components=[comp["name"] for comp in fields.get("components", [])],
            created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")) if fields.get("created") else None,
            updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")) if fields.get("updated") else None
        )
    
    def _extract_text_from_adf(self, adf_content: Dict) -> str:
        """Extract plain text from Atlassian Document Format (ADF)"""
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        text_parts = []
        
        def extract_text_recursive(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    text_parts.append(node.get("text", ""))
                elif "content" in node:
                    for child in node["content"]:
                        extract_text_recursive(child)
                elif "text" in node:
                    text_parts.append(node["text"])
            elif isinstance(node, list):
                for item in node:
                    extract_text_recursive(item)
        
        extract_text_recursive(adf_content)
        return " ".join(text_parts).strip()
    
    async def add_comment(self, issue_key: str, comment: str):
        """Add comment to Jira issue"""
        try:
            comment_data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                    headers=self.headers,
                    json=comment_data
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Added comment to {issue_key}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to add comment: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to add comment to {issue_key}: {e}")
            raise Exception(f"Failed to add comment to {issue_key}: {str(e)}")
    
    async def attach_file_to_issue(self, issue_key: str, file_path: str):
        """Attach file to Jira issue"""
        try:
            # Create headers without Content-Type for file upload
            upload_headers = {
                'Authorization': self.headers['Authorization'],
                'X-Atlassian-Token': 'no-check'
            }
            
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=file_path.split('/')[-1])
                    
                    async with session.post(
                        f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments",
                        headers=upload_headers,
                        data=data
                    ) as response:
                        if response.status in [200, 201]:
                            logger.info(f"Attached file to {issue_key}")
                        else:
                            error_text = await response.text()
                            raise Exception(f"Failed to attach file: {response.status} - {error_text}")
                            
        except Exception as e:
            logger.error(f"Failed to attach file to {issue_key}: {e}")
            raise Exception(f"Failed to attach file: {str(e)}")
    
    async def create_issue(self, project_key: str, summary: str, description: str, 
                          issue_type: str = "Story", assignee: Optional[str] = None,
                          labels: Optional[List[str]] = None, components: Optional[List[str]] = None) -> str:
        """Create a new Jira issue"""
        try:
            issue_data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }
            
            if assignee:
                issue_data["fields"]["assignee"] = {"emailAddress": assignee}
            
            if labels:
                issue_data["fields"]["labels"] = labels
                
            if components:
                issue_data["fields"]["components"] = [{"name": comp} for comp in components]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/rest/api/3/issue",
                    headers=self.headers,
                    json=issue_data
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        issue_key = result["key"]
                        logger.info(f"Created new issue: {issue_key}")
                        return issue_key
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to create issue: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise Exception(f"Failed to create Jira issue: {str(e)}")
    
    async def transition_issue(self, issue_key: str, transition_name: str):
        """Transition issue to different status"""
        try:
            # Get available transitions
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        transitions_data = await response.json()
                        transitions = transitions_data.get("transitions", [])
                        
                        # Find the transition ID
                        transition_id = None
                        for transition in transitions:
                            if transition["name"].lower() == transition_name.lower():
                                transition_id = transition["id"]
                                break
                        
                        if not transition_id:
                            available = [t["name"] for t in transitions]
                            raise Exception(f"Transition '{transition_name}' not found. Available: {available}")
                        
                        # Execute transition
                        transition_data = {
                            "transition": {"id": transition_id}
                        }
                        
                        async with session.post(
                            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                            headers=self.headers,
                            json=transition_data
                        ) as trans_response:
                            if trans_response.status in [200, 204]:
                                logger.info(f"Transitioned {issue_key} to {transition_name}")
                            else:
                                error_text = await trans_response.text()
                                raise Exception(f"Failed to transition: {trans_response.status} - {error_text}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get transitions: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to transition {issue_key}: {e}")
            raise Exception(f"Failed to transition issue: {str(e)}")
    
    async def get_agile_boards(self) -> List[Dict]:
        """Get Agile boards using the Agile REST API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/agile/1.0/board",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        boards = data.get("values", [])
                        logger.info(f"Fetched {len(boards)} agile boards")
                        return boards
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch boards: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch agile boards: {e}")
            raise Exception(f"Failed to fetch agile boards: {str(e)}")
    
    async def get_agile_backlog_branches(self, board_id: Optional[int] = None) -> Dict[str, any]:
        """
        Fetch all branches using the agile 1.0 backlog issue endpoint for connectivity check
        Simple implementation using direct REST API calls
        """
        try:
            # If no board_id provided, get the first available board
            if board_id is None:
                boards = await self.get_agile_boards()
                if not boards:
                    raise Exception("No agile boards found")
                board_id = boards[0]["id"]
                logger.info(f"Using board ID: {board_id}")
            
            # Get backlog issues from the board using direct REST API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/agile/1.0/board/{board_id}/backlog",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        backlog_data = await response.json()
                        issues = backlog_data.get("issues", [])
                        
                        # Extract basic branch information
                        branches = []
                        for issue in issues[:10]:  # Limit to first 10 for simplicity
                            fields = issue.get("fields", {})
                            issue_key = issue.get("key", "")
                            summary = fields.get("summary", "")
                            
                            # Simple branch naming
                            potential_branches = []
                            if issue_key:
                                potential_branches.append(f"feature/{issue_key.lower()}")
                                potential_branches.append(f"bugfix/{issue_key.lower()}")
                            
                            branches.append({
                                "issue_key": issue_key,
                                "summary": summary[:50] + "..." if len(summary) > 50 else summary,
                                "status": fields.get("status", {}).get("name", "Unknown"),
                                "potential_branches": potential_branches
                            })
                        
                        return {
                            "success": True,
                            "board_id": board_id,
                            "backlog_issue_count": len(issues),
                            "connectivity_status": "Connected to Jira Agile API",
                            "endpoint": f"/rest/agile/1.0/board/{board_id}/backlog",
                            "branches": branches,
                            "total_branches_found": len(branches)
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch backlog: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to fetch agile backlog branches: {e}")
            return {
                "success": False,
                "error": str(e),
                "connectivity_status": "Failed to connect to Jira Agile API",
                "endpoint": "/rest/agile/1.0/backlog/issue"
            }
    
    async def get_github_integration_info(self, issue_key: str) -> Dict[str, any]:
        """Extract GitHub-related information from issue"""
        try:
            issue = await self.get_issue(issue_key)
            
            github_info = {
                'branches': [],
                'pull_requests': [],
                'commits': [],
                'repository_hints': []
            }
            
            # Look for GitHub URLs in description and comments
            text_to_search = [issue.description]
            
            # Get comments if available
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        comments_data = await response.json()
                        comments = comments_data.get("comments", [])
                        for comment in comments:
                            body = comment.get("body", "")
                            if isinstance(body, dict):
                                body = self._extract_text_from_adf(body)
                            text_to_search.append(body)
            
            # Extract GitHub URLs and references
            import re
            github_patterns = {
                'repo': r'github\.com[/:]([^/\s]+/[^/\s]+)',
                'pr': r'github\.com/[^/\s]+/[^/\s]+/pull/(\d+)',
                'commit': r'github\.com/[^/\s]+/[^/\s]+/commit/([a-f0-9]{7,40})',
                'branch': r'(?:branch|feature|bugfix)[:\s]+([^\s,]+)'
            }
            
            for text in text_to_search:
                if not text:
                    continue
                    
                for pattern_type, pattern in github_patterns.items():
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        if pattern_type == 'repo':
                            github_info['repository_hints'].extend(matches)
                        else:
                            github_info[f'{pattern_type}s'].extend(matches)
            
            # Remove duplicates
            for key in github_info:
                github_info[key] = list(set(github_info[key]))
            
            return github_info
            
        except Exception as e:
            logger.error(f"Failed to extract GitHub info from {issue_key}: {e}")
            return {}
    
    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """Extract acceptance criteria from description"""
        if not description:
            return []
            
        criteria = []
        lines = description.split('\n')
        in_ac_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for acceptance criteria section headers
            if any(keyword in line.lower() for keyword in [
                'acceptance criteria', 'acceptance criterion', 'ac:', 'definition of done'
            ]):
                in_ac_section = True
                continue
            
            # Stop if we hit another section
            if in_ac_section and line.lower().startswith(('description', 'notes', 'background', 'attachments')):
                break
                
            # Extract criteria items
            if in_ac_section and line:
                # Remove bullet points and numbering
                cleaned = line
                for prefix in ['*', '-', '•', '1.', '2.', '3.', '4.', '5.']:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip()
                        break
                
                if cleaned and len(cleaned) > 5:  # Ignore very short lines
                    criteria.append(cleaned)
        
        return criteria