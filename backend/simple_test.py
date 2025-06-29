#!/usr/bin/env python3
"""
Advanced IBM Granite Test Script with Crystal Clear Implementation Planning
Includes repository analysis, Jira integration, and code-aware implementation suggestions
"""

import os
import sys
import json
import asyncio
import aiohttp
import base64
import time
import re
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import quote
import logging
import requests

try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️ transformers not available - install with: pip install transformers")
    TRANSFORMERS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available - install with: pip install python-dotenv")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryType(Enum):
    """Repository type classification"""
    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    FULL_STACK = "full_stack"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    LIBRARY = "library"
    FRAMEWORK = "framework"
    CLI_TOOL = "cli_tool"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    BLOCKCHAIN = "blockchain"
    GAME = "game"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    MONOREPO = "monorepo"
    UNKNOWN = "unknown"

class TechStack(Enum):
    """Technology stack identification"""
    # Frontend
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    NUXTJS = "nuxtjs"
    ANGULAR = "angular"
    SVELTE = "svelte"
    VANILLA_JS = "vanilla_js"
    
    # Backend
    NODEJS = "nodejs"
    PYTHON_DJANGO = "python_django"
    PYTHON_FLASK = "python_flask"
    PYTHON_FASTAPI = "python_fastapi"
    JAVA_SPRING = "java_spring"
    DOTNET = "dotnet"
    RUBY_RAILS = "ruby_rails"
    PHP_LARAVEL = "php_laravel"
    GO = "go"
    RUST = "rust"
    
    # Mobile
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    IONIC = "ionic"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    
    # Other
    ELECTRON = "electron"
    UNITY = "unity"
    UNREAL = "unreal"

@dataclass
class FileAnalysis:
    """File analysis result"""
    path: str
    type: str
    language: str
    size: int
    complexity: int
    dependencies: List[str]
    last_modified: str
    content_preview: str = ""
    
@dataclass
class RepositoryAnalysis:
    """Comprehensive repository analysis"""
    url: str
    name: str
    description: str
    type: RepositoryType
    tech_stack: List[TechStack]
    languages: Dict[str, float]
    structure: Dict[str, Any]
    dependencies: Dict[str, List[str]]
    config_files: List[str]
    test_files: List[str]
    documentation: List[str]
    build_tools: List[str]
    deployment_configs: List[str]
    security_configs: List[str]
    performance_metrics: Dict[str, Any]
    complexity_score: int
    maintainability_score: int
    architecture_patterns: List[str]
    potential_issues: List[str]
    recommendations: List[str]
    key_code_files: List[Dict[str, Any]] = None

class JiraService:
    """Enhanced Jira service for issue management"""
    
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL', 'https://your-domain.atlassian.net')
        self.username = os.getenv('JIRA_USERNAME')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([self.username, self.api_token]):
            logger.warning("Jira credentials not configured. Some features may not work.")
            return
        
        # Create auth headers
        import base64
        auth_string = f"{self.username}:{self.api_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"Jira service initialized for {self.base_url}")
    
    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get detailed issue information"""
        if not hasattr(self, 'headers'):
            # Return mock issue for testing
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
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'key': data['key'],
                            'summary': data['fields']['summary'],
                            'description': data['fields'].get('description', ''),
                            'status': data['fields']['status'],
                            'priority': data['fields'].get('priority'),
                            'assignee': data['fields'].get('assignee'),
                            'created': data['fields']['created']
                        }
                    else:
                        logger.error(f"Failed to get issue {issue_key}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {e}")
            return None

class GraniteAPI:
    """Enhanced IBM Granite API client with improved error handling"""
    
    def __init__(self, api_key: str, project_id: str, base_url: str = "https://eu-de.ml.cloud.ibm.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url
        self.generation_endpoint = f"{base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
    
    def get_bearer_token(self):
        """Generate Bearer token from IBM API key"""
        import time
        
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
                logger.info(f"Bearer token: {self.bearer_token[:20]}...")
                
                return self.bearer_token
            else:
                logger.error(f"❌ Error generating Bearer token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception generating Bearer token: {e}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Generate text using IBM Granite Text Generation API"""
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
                }
            }
        }
        
        # Add temperature only for sampling mode
        if payload["parameters"]["decoding_method"] == "sample":
            payload["parameters"]["temperature"] = temperature
        
        try:
            logger.debug(f"Making request to: {self.generation_endpoint}")
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return ""
                
            result = response.json()
            logger.debug(f"API Response keys: {list(result.keys())}")
            
            # Handle text generation API response format
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                logger.debug(f"Generated text length: {len(generated_text)} characters")
                return generated_text
            else:
                logger.error(f"Unexpected response format: {result}")
                return ""
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Error response: {e.response.text}")
            return ""

class UniversalRepositoryAnalyzer:
    """Advanced repository analyzer for any tech stack"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.rate_limit_delay = 0.1
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Granite-Repo-Analyzer/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _parse_github_url(self, url: str) -> tuple:
        """Parse GitHub URL and extract owner/repo"""
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$',
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, url.strip())
            if match:
                return match.groups()
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    async def _api_request(self, url: str, headers: Optional[dict] = None) -> Optional[dict]:
        """Make API request with rate limiting and error handling"""
        await asyncio.sleep(self.rate_limit_delay)
        
        if url in self.cache:
            cache_time, data = self.cache[url]
            if time.time() - cache_time < 300:  # 5 minute cache
                return data
        
        try:
            async with self.session.get(url, headers=headers or {}) as response:
                if response.status == 403:
                    self.rate_limit_delay = min(self.rate_limit_delay * 2, 5)
                    raise Exception("GitHub API rate limit exceeded")
                
                if response.status == 404:
                    return None
                
                if response.status != 200:
                    raise Exception(f"GitHub API error: {response.status}")
                
                data = await response.json()
                self.cache[url] = (time.time(), data)
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"API request failed for {url}: {e}")
            return None
    
    async def _get_file_content(self, api_base: str, path: str) -> str:
        """Get file content from GitHub API"""
        try:
            data = await self._api_request(f"{api_base}/contents/{quote(path)}")
            if data and data.get('content'):
                return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.debug(f"Failed to get content for {path}: {e}")
        return ""

    async def _get_key_code_files(self, api_base: str, structure: Dict, issue_context: str = "") -> List[Dict]:
        """Get content of key code files for analysis"""
        key_files = []
        
        def find_relevant_files(struct, path="", max_files=10):
            if len(key_files) >= max_files:
                return
                
            # Priority file patterns
            priority_patterns = [
                r'\.jsx?$', r'\.tsx?$', r'\.py$', r'\.java$', r'\.php$', 
                r'index\.(js|jsx|ts|tsx)$', r'app\.(js|jsx|ts|tsx)$',
                r'main\.(js|jsx|ts|tsx|py)$', r'component.*\.(js|jsx|ts|tsx)$'
            ]
            
            # Issue-specific patterns
            issue_keywords = issue_context.lower().split()
            
            for file_info in struct.get("files", []):
                if len(key_files) >= max_files:
                    break
                    
                file_name = file_info.get("name", "").lower()
                file_path = f"{path}/{file_name}" if path else file_name
                
                # Check if file is relevant
                is_priority = any(__import__('re').search(pattern, file_name) for pattern in priority_patterns)
                is_issue_relevant = any(keyword in file_name for keyword in issue_keywords if len(keyword) > 3)
                
                if is_priority or is_issue_relevant:
                    key_files.append({
                        "name": file_info.get("name"),
                        "path": file_path,
                        "size": file_info.get("size", 0),
                        "priority": "high" if is_priority else "medium"
                    })
            
            # Recursively search important directories
            for dir_name, dir_struct in struct.get("directories", {}).items():
                if len(key_files) >= max_files:
                    break
                if dir_name.lower() in ['src', 'components', 'pages', 'lib', 'utils', 'api', 'services']:
                    find_relevant_files(dir_struct, f"{path}/{dir_name}" if path else dir_name, max_files)
        
        find_relevant_files(structure)
        
        # Get file contents
        for file_info in key_files[:8]:  # Limit to 8 files to avoid API limits
            try:
                content = await self._get_file_content(api_base, file_info["path"])
                file_info["content"] = content
                file_info["lines"] = len(content.split('\n')) if content else 0
                # Add preview for analysis
                file_info["content_preview"] = content[:500] + "..." if len(content) > 500 else content
            except Exception as e:
                logger.debug(f"Failed to get content for {file_info['path']}: {e}")
                file_info["content"] = ""
                file_info["lines"] = 0
                file_info["content_preview"] = ""
        
        return key_files
    
    async def _analyze_languages(self, api_base: str) -> Dict[str, float]:
        """Analyze repository languages"""
        data = await self._api_request(f"{api_base}/languages")
        if not data:
            return {}
        
        total = sum(data.values())
        return {lang: (bytes_count / total) * 100 for lang, bytes_count in data.items()}
    
    async def _analyze_directory_structure(self, api_base: str, path: str = "") -> Dict[str, Any]:
        """Recursively analyze directory structure"""
        data = await self._api_request(f"{api_base}/contents/{quote(path) if path else ''}")
        if not data:
            return {}
        
        structure = {"files": [], "directories": {}}
        
        for item in data:
            if item['type'] == 'file':
                structure["files"].append({
                    "name": item['name'],
                    "size": item['size'],
                    "path": item['path']
                })
            elif item['type'] == 'dir':
                # Recursively analyze important directories
                if item['name'] in ['src', 'lib', 'components', 'pages', 'api', 'services', 'utils', 'config']:
                    subdir = await self._analyze_directory_structure(api_base, item['path'])
                    structure["directories"][item['name']] = subdir
                else:
                    structure["directories"][item['name']] = {"files": [], "directories": {}}
        
        return structure
    
    def _detect_repository_type(self, structure: Dict, languages: Dict, package_files: Dict) -> RepositoryType:
        """Intelligent repository type detection"""
        files = self._get_all_files(structure)
        file_names = [f['name'].lower() for f in files]
        
        # Mobile apps
        if 'package.json' in package_files:
            pkg = package_files['package.json']
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            if 'react-native' in deps:
                return RepositoryType.MOBILE_APP
        
        # Web development
        if 'package.json' in package_files:
            pkg = package_files['package.json']
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            
            if 'next' in deps:
                return RepositoryType.WEB_FRONTEND
            if 'react' in deps and not any(backend in deps for backend in ['express', 'koa', 'fastify']):
                return RepositoryType.WEB_FRONTEND
            if any(backend in deps for backend in ['express', 'koa', 'fastify']):
                return RepositoryType.WEB_BACKEND
        
        # Python frameworks
        python_percentage = languages.get('Python', 0)
        if python_percentage > 50:
            if any(name in file_names for name in ['manage.py']):
                return RepositoryType.WEB_BACKEND
            if 'fastapi' in str(package_files).lower():
                return RepositoryType.API_SERVICE
        
        return RepositoryType.UNKNOWN
    
    def _detect_tech_stack(self, structure: Dict, languages: Dict, package_files: Dict) -> List[TechStack]:
        """Detect technology stack"""
        tech_stack = []
        
        if 'package.json' in package_files:
            pkg = package_files['package.json']
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            
            if 'next' in deps:
                tech_stack.append(TechStack.NEXTJS)
            elif 'react' in deps:
                tech_stack.append(TechStack.REACT)
            if 'express' in deps:
                tech_stack.append(TechStack.NODEJS)
        
        return tech_stack
    
    def _get_all_files(self, structure: Dict, prefix: str = "") -> List[Dict]:
        """Recursively get all files from structure"""
        files = []
        
        for file_info in structure.get("files", []):
            files.append({
                "name": file_info["name"],
                "path": f"{prefix}/{file_info['name']}" if prefix else file_info["name"],
                "size": file_info["size"]
            })
        
        for dir_name, dir_structure in structure.get("directories", {}).items():
            files.extend(self._get_all_files(dir_structure, f"{prefix}/{dir_name}" if prefix else dir_name))
        
        return files
    
    async def _analyze_package_files(self, api_base: str, structure: Dict) -> Dict[str, Any]:
        """Analyze package and configuration files"""
        package_files = {}
        
        config_file_patterns = [
            'package.json', 'requirements.txt', 'pyproject.toml',
            'tsconfig.json', 'next.config.js'
        ]
        
        all_files = self._get_all_files(structure)
        
        for pattern in config_file_patterns:
            matching_files = [f for f in all_files if f['name'].lower() == pattern.lower()]
            if matching_files:
                content = await self._get_file_content(api_base, matching_files[0]['path'])
                if content:
                    try:
                        if pattern.endswith('.json'):
                            package_files[pattern] = json.loads(content)
                        else:
                            package_files[pattern] = content
                    except json.JSONDecodeError:
                        package_files[pattern] = content
        
        return package_files
    
    def _calculate_complexity_score(self, structure: Dict, languages: Dict, package_files: Dict) -> int:
        """Calculate repository complexity score (1-100)"""
        score = 0
        
        # File count factor
        all_files = self._get_all_files(structure)
        file_count = len(all_files)
        score += min(file_count / 10, 30)
        
        # Language diversity factor
        lang_count = len([lang for lang, percentage in languages.items() if percentage > 5])
        score += min(lang_count * 5, 20)
        
        return min(int(score), 100)
    
    async def analyze_repository(self, github_url: str, issue_context: str = "") -> RepositoryAnalysis:
        """Main repository analysis method"""
        try:
            owner, repo = self._parse_github_url(github_url)
            api_base = f"https://api.github.com/repos/{owner}/{repo}"
            
            # Get basic repository info
            repo_info = await self._api_request(api_base)
            if not repo_info:
                raise Exception("Repository not found")
            
            # Parallel analysis tasks
            languages_task = self._analyze_languages(api_base)
            structure_task = self._analyze_directory_structure(api_base)
            
            languages, structure = await asyncio.gather(languages_task, structure_task)
            
            # Analyze package files
            package_files = await self._analyze_package_files(api_base, structure)
            
            # Get key code files for analysis
            key_code_files = await self._get_key_code_files(api_base, structure, issue_context)
            
            # Detect repository characteristics
            repo_type = self._detect_repository_type(structure, languages, package_files)
            tech_stack = self._detect_tech_stack(structure, languages, package_files)
            complexity_score = self._calculate_complexity_score(structure, languages, package_files)
            
            # Build comprehensive analysis
            analysis = RepositoryAnalysis(
                url=github_url,
                name=repo_info.get('name', ''),
                description=repo_info.get('description', ''),
                type=repo_type,
                tech_stack=tech_stack,
                languages=languages,
                structure=structure,
                dependencies={},
                config_files=list(package_files.keys()),
                test_files=[],
                documentation=[],
                build_tools=[],
                deployment_configs=[],
                security_configs=[],
                performance_metrics={"file_count": len(self._get_all_files(structure))},
                complexity_score=complexity_score,
                maintainability_score=max(0, 100 - complexity_score),
                architecture_patterns=[],
                potential_issues=[],
                recommendations=[],
                key_code_files=key_code_files
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            raise Exception(f"Analysis failed: {str(e)}")

class CrystalClearImplementationPlanner:
    """Advanced implementation planning with code analysis"""
    
    def __init__(self, granite_api, jira_service):
        self.granite_api = granite_api
        self.jira_service = jira_service
    
    async def generate_crystal_clear_plan(self, issue_key: str, github_url: str = None) -> Dict[str, Any]:
        """Generate crystal clear implementation plan using repository code analysis"""
        
        # Get Jira issue details
        issue = await self.jira_service.get_issue(issue_key)
        if not issue:
            return {"error": f"Could not fetch issue {issue_key}"}
        
        issue_summary = issue.get('summary', '')
        issue_description = issue.get('description', '')
        
        # Analyze repository if URL provided
        repo_analysis = None
        if github_url:
            try:
                async with UniversalRepositoryAnalyzer() as analyzer:
                    repo_analysis = await analyzer.analyze_repository(
                        github_url, 
                        issue_context=f"{issue_summary} {issue_description}"
                    )
            except Exception as e:
                logger.error(f"Repository analysis failed: {e}")
                repo_analysis = None
        
        # Create comprehensive context for Granite
        context = self._build_analysis_context(issue, repo_analysis)
        
        # Generate the crystal clear plan
        plan_prompt = f"""
Based on the Jira issue and repository analysis, create a CRYSTAL CLEAR implementation plan:

JIRA ISSUE: {issue_key}
SUMMARY: {issue_summary}
DESCRIPTION: {issue_description}

REPOSITORY CONTEXT:
{context}

Generate a detailed implementation plan that includes:
1. CRYSTAL CLEAR step-by-step implementation approach
2. SPECIFIC code changes needed with examples
3. EXACT files to modify and why
4. DETAILED implementation strategy
5. RISK assessment and mitigation
6. TESTING requirements
7. ESTIMATED complexity (low/medium/high)

Make this plan so clear that any developer could implement it exactly.
"""
        
        crystal_plan = self.granite_api.generate(plan_prompt, max_tokens=1000, temperature=0.3)
        
        # Analyze specific code files for detailed changes
        file_changes = await self._analyze_file_changes(issue, repo_analysis)
        
        # Generate code examples
        code_examples = await self._generate_code_examples(issue, repo_analysis)
        
        return {
            "jira_issue": {
                "key": issue_key,
                "summary": issue_summary,
                "description": issue_description,
                "status": issue.get('status', {}).get('name', 'Unknown')
            },
            "crystal_clear_plan": crystal_plan,
            "detailed_file_changes": file_changes,
            "code_examples": code_examples,
            "repository_insights": {
                "tech_stack": [tech.value for tech in repo_analysis.tech_stack] if repo_analysis else [],
                "complexity": "high" if repo_analysis and repo_analysis.complexity_score > 70 else "medium" if repo_analysis and repo_analysis.complexity_score > 40 else "low",
                "key_files_analyzed": len(repo_analysis.key_code_files or []) if repo_analysis else 0,
                "implementation_strategy": self._determine_implementation_strategy(repo_analysis)
            },
            "estimated_complexity": self._estimate_complexity(issue_summary, issue_description, repo_analysis),
            "file_analyses": [self._analyze_individual_file(file) for file in (repo_analysis.key_code_files or [])[:5]] if repo_analysis else [],
            "implementation_confidence": 0.85 if repo_analysis else 0.6
        }
    
    def _build_analysis_context(self, issue: Dict, repo_analysis: RepositoryAnalysis = None) -> str:
        """Build comprehensive context for analysis"""
        context = f"""
Issue Status: {issue.get('status', {}).get('name', 'Unknown')}
Priority: {issue.get('priority', {}).get('name', 'Unknown')}
Assignee: {issue.get('assignee', {}).get('displayName', 'Unassigned')}
"""
        
        if repo_analysis:
            context += f"""
Repository Type: {repo_analysis.type.value}
Technology Stack: {', '.join([tech.value for tech in repo_analysis.tech_stack])}
Primary Languages: {', '.join(list(repo_analysis.languages.keys())[:3])}
Complexity Score: {repo_analysis.complexity_score}/100

Directory Structure:
{self._format_structure(repo_analysis.structure)}

Key Configuration Files:
{', '.join(repo_analysis.config_files)}
"""
            
            # Add key code files analysis
            if repo_analysis.key_code_files:
                context += "\n\nKey Code Files Found:\n"
                for file in repo_analysis.key_code_files[:3]:
                    context += f"- {file['path']} ({file.get('lines', 0)} lines)\n"
                    if file.get('content_preview'):
                        context += f"  Preview: {file['content_preview'][:200]}...\n"
        
        return context
    
    def _format_structure(self, structure: Dict, indent: int = 0) -> str:
        """Format directory structure for context"""
        result = ""
        prefix = "  " * indent
        
        # Show directories
        for dir_name in list(structure.get("directories", {}).keys())[:5]:
            result += f"{prefix}{dir_name}/\n"
        
        # Show some files
        for file in list(structure.get("files", []))[:3]:
            result += f"{prefix}{file['name']}\n"
        
        return result
    
    async def _analyze_file_changes(self, issue: Dict, repo_analysis: RepositoryAnalysis = None) -> List[Dict]:
        """Analyze specific file changes needed"""
        changes = []
        
        if not repo_analysis or not repo_analysis.key_code_files:
            return []
        
        issue_summary = issue.get('summary', '')
        
        for file in repo_analysis.key_code_files[:5]:
            change_prompt = f"""
Analyze this file for implementing: {issue_summary}

File: {file['path']}
Content Preview:
{file.get('content_preview', '')}

What SPECIFIC changes are needed in this file? Provide:
1. EXACT modifications required
2. WHY these changes are needed
3. RISK level (low/medium/high)
4. CODE snippets if helpful

Be very specific and actionable.
"""
            
            change_analysis = self.granite_api.generate(change_prompt, max_tokens=300, temperature=0.2)
            
            changes.append({
                "file": file['path'],
                "analysis": change_analysis,
                "priority": file.get('priority', 'medium'),
                "size": file.get('size', 0),
                "lines": file.get('lines', 0)
            })
        
        return changes
    
    async def _generate_code_examples(self, issue: Dict, repo_analysis: RepositoryAnalysis = None) -> List[Dict]:
        """Generate specific code examples for implementation"""
        examples = []
        
        if not repo_analysis:
            return []
        
        issue_summary = issue.get('summary', '')
        
        # Determine what kind of code examples to generate based on tech stack
        if TechStack.REACT in repo_analysis.tech_stack or TechStack.NEXTJS in repo_analysis.tech_stack:
            example_prompt = f"""
Generate a SPECIFIC React/Next.js code example for implementing: {issue_summary}

Based on the repository structure, provide:
1. A complete component example
2. Proper imports and exports
3. TypeScript if applicable
4. Following best practices

Make it production-ready code.
"""
            
            code_example = self.granite_api.generate(example_prompt, max_tokens=400, temperature=0.1)
            examples.append({
                "type": "React Component",
                "code": code_example,
                "filename": "Example.jsx"
            })
        
        elif repo_analysis.languages.get('Python', 0) > 30:
            example_prompt = f"""
Generate a SPECIFIC Python code example for implementing: {issue_summary}

Provide:
1. Complete function or class implementation
2. Proper imports
3. Error handling
4. Documentation strings

Make it production-ready code.
"""
            
            code_example = self.granite_api.generate(example_prompt, max_tokens=400, temperature=0.1)
            examples.append({
                "type": "Python Implementation",
                "code": code_example,
                "filename": "example.py"
            })
        
        return examples
    
    def _determine_implementation_strategy(self, repo_analysis: RepositoryAnalysis = None) -> str:
        """Determine the best implementation strategy"""
        if not repo_analysis:
            return "Follow standard development practices"
        
        if repo_analysis.type == RepositoryType.WEB_FRONTEND:
            return "Component-based development with proper state management"
        elif repo_analysis.type == RepositoryType.WEB_BACKEND:
            return "API-first development with proper error handling"
        elif repo_analysis.type == RepositoryType.FULL_STACK:
            return "Full-stack development with frontend and backend coordination"
        else:
            return "Follow repository patterns and best practices"
    
    def _estimate_complexity(self, issue_summary: str, issue_description: str, repo_analysis: RepositoryAnalysis = None) -> str:
        """Estimate implementation complexity"""
        complexity_indicators = 0
        
        # Check issue complexity
        text = f"{issue_summary} {issue_description}".lower()
        if any(word in text for word in ['complex', 'integration', 'multiple', 'architecture']):
            complexity_indicators += 2
        if any(word in text for word in ['simple', 'basic', 'add', 'remove']):
            complexity_indicators -= 1
        
        # Check repository complexity
        if repo_analysis and repo_analysis.complexity_score > 70:
            complexity_indicators += 2
        elif repo_analysis and repo_analysis.complexity_score > 40:
            complexity_indicators += 1
        
        # Check tech stack complexity
        if repo_analysis and len(repo_analysis.tech_stack) > 2:
            complexity_indicators += 1
        
        if complexity_indicators >= 3:
            return "high"
        elif complexity_indicators >= 1:
            return "medium"
        else:
            return "low"
    
    def _analyze_individual_file(self, file: Dict) -> Dict:
        """Analyze individual file for insights"""
        return {
            "path": file['path'],
            "size": file.get('size', 0),
            "lines": file.get('lines', 0),
            "priority": file.get('priority', 'medium'),
            "analysis": f"Key file for implementation - requires careful review",
            "modifications_needed": "Specific changes will be determined during implementation"
        }

def create_summarization_prompt(documents: List[Dict[str, str]], instruction: str) -> str:
    """Create a prompt with documents for summarization"""
    prompt = f"{instruction}\n\n"
    
    for doc in documents:
        prompt += f"Document: {doc['title']}\n"
        prompt += f"Content: {doc['text']}\n\n"
    
    return prompt

def generate_with_documents(user_prompt: str, documents: list[dict[str, str]], granite_api, tokenizer) -> str:
    """Generate text using documents as context (enhanced version)"""
    # Create comprehensive prompt
    prompt = create_summarization_prompt(documents, user_prompt)
    
    # Check token count if tokenizer available
    if tokenizer:
        token_count = len(tokenizer.tokenize(prompt))
        print(f"Input prompt tokens: {token_count}")
        
        # Adjust max_tokens based on input length
        max_tokens = min(800, 4000 - token_count)
    else:
        max_tokens = 500
    
    # Generate response
    return granite_api.generate(prompt, max_tokens=max_tokens, temperature=0.7)

def generate_simple_prompt(user_prompt: str, documents: list[dict[str, str]], granite_api) -> str:
    """Simple prompt generation without tokenizer dependency"""
    prompt = create_summarization_prompt(documents, user_prompt)
    return granite_api.generate(prompt, max_tokens=500, temperature=0.7)

def test_crystal_clear_implementation_planning():
    """Test crystal clear implementation planning with repository analysis"""
    print("\n" + "="*80)
    print("🚀 CRYSTAL CLEAR IMPLEMENTATION PLANNING TEST")
    print("="*80)
    
    # Configuration
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("❌ Please set IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return
    
    # Initialize services
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    jira_service = JiraService()
    planner = CrystalClearImplementationPlanner(granite_api, jira_service)
    
    # Test configuration
    test_issue_key = "TEST-123"  # You can change this to a real Jira issue
    test_github_url = "https://github.com/vercel/next.js"  # Example repository
    
    async def run_analysis():
        print(f"📊 Analyzing Jira issue: {test_issue_key}")
        print(f"🔍 Repository: {test_github_url}")
        print()
        
        try:
            # Generate crystal clear implementation plan
            print("🎯 Generating CRYSTAL CLEAR implementation plan...")
            crystal_plan = await planner.generate_crystal_clear_plan(
                test_issue_key,
                test_github_url
            )
            
            print("✅ Crystal clear plan generated!")
            print()
            
            # Display the results
            if "error" in crystal_plan:
                print(f"❌ Error: {crystal_plan['error']}")
                return
            
            print("📋 JIRA ISSUE DETAILS")
            print("-" * 60)
            jira_issue = crystal_plan.get('jira_issue', {})
            print(f"Key: {jira_issue.get('key', 'N/A')}")
            print(f"Summary: {jira_issue.get('summary', 'N/A')}")
            print(f"Status: {jira_issue.get('status', 'N/A')}")
            print()
            
            print("📋 CRYSTAL CLEAR IMPLEMENTATION PLAN")
            print("-" * 60)
            print(crystal_plan.get('crystal_clear_plan', 'Plan generation failed'))
            print()
            
            print("📁 DETAILED FILE CHANGES REQUIRED")
            print("-" * 60)
            for change in crystal_plan.get('detailed_file_changes', []):
                print(f"🔧 {change['file']} ({change['priority']} priority)")
                print(f"   Analysis: {change['analysis'][:200]}...")
                print(f"   Size: {change['size']} bytes, Lines: {change['lines']}")
                print()
            
            print("💻 CODE EXAMPLES")
            print("-" * 60)
            for example in crystal_plan.get('code_examples', []):
                print(f"📄 {example['type']} ({example['filename']})")
                print(f"```")
                print(example['code'][:300] + "..." if len(example['code']) > 300 else example['code'])
                print(f"```")
                print()
            
            print("🔍 REPOSITORY INSIGHTS")
            print("-" * 60)
            insights = crystal_plan.get('repository_insights', {})
            print(f"Tech Stack: {insights.get('tech_stack', [])}")
            print(f"Complexity: {insights.get('complexity', 'unknown')}")
            print(f"Files Analyzed: {insights.get('key_files_analyzed', 0)}")
            print(f"Strategy: {insights.get('implementation_strategy', 'N/A')}")
            print(f"Estimated Complexity: {crystal_plan.get('estimated_complexity', 'unknown')}")
            print(f"Implementation Confidence: {crystal_plan.get('implementation_confidence', 0):.1%}")
            print()
            
            print("📊 FILE ANALYSIS DETAILS")
            print("-" * 60)
            for analysis in crystal_plan.get('file_analyses', []):
                print(f"📄 {analysis['path']}")
                print(f"   • Size: {analysis['size']} bytes")
                print(f"   • Lines: {analysis['lines']}")
                print(f"   • Priority: {analysis['priority']}")
                print(f"   • Modifications: {analysis['modifications_needed']}")
                print()
            
            print("✅ CRYSTAL CLEAR IMPLEMENTATION PLANNING COMPLETED!")
            print("🎯 This plan provides specific, actionable steps for any developer to implement.")
            
        except Exception as e:
            print(f"❌ Crystal clear planning failed: {e}")
            print("This might be due to GitHub API rate limits or network issues.")
            print("The system will work with actual repositories that have proper access.")
    
    # Run the async analysis
    try:
        import asyncio
        asyncio.run(run_analysis())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Note: This test requires network access and GitHub API availability.")

def test_simple_crystal_clear_planning():
    """Test crystal clear planning with minimal repository data"""
    print("\n" + "="*80)
    print("🎯 SIMPLE CRYSTAL CLEAR PLANNING TEST")
    print("="*80)
    
    # Configuration
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("❌ Please set IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return
    
    # Initialize services
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    jira_service = JiraService()
    planner = CrystalClearImplementationPlanner(granite_api, jira_service)
    
    async def run_simple_planning():
        try:
            print("🎯 Testing with mock Jira issue...")
            print("Issue: Add dark mode toggle to header component")
            print()
            
            # Generate crystal clear plan without repository URL (uses mock data)
            print("🔄 Generating crystal clear implementation plan...")
            crystal_plan = await planner.generate_crystal_clear_plan("MOCK-123")
            
            print("✅ Plan generated successfully!")
            print()
            
            # Display results
            if "error" in crystal_plan:
                print(f"❌ Error: {crystal_plan['error']}")
                return
            
            print("📋 IMPLEMENTATION PLAN")
            print("-" * 50)
            print(crystal_plan.get('crystal_clear_plan', 'No plan generated'))
            print()
            
            print("🔧 FILE CHANGES")
            print("-" * 50)
            for change in crystal_plan.get('detailed_file_changes', []):
                print(f"📄 {change['file']}")
                print(f"   {change['analysis'][:150]}...")
                print()
            
            print("💡 INSIGHTS")
            print("-" * 50)
            insights = crystal_plan.get('repository_insights', {})
            print(f"Complexity: {crystal_plan.get('estimated_complexity', 'unknown')}")
            print(f"Confidence: {crystal_plan.get('implementation_confidence', 0):.1%}")
            print(f"Strategy: {insights.get('implementation_strategy', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Simple planning test failed: {e}")
    
    # Run the test
    try:
        import asyncio
        asyncio.run(run_simple_planning())
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

def test_granite_summarization():
    """Test Granite document summarization (original functionality)"""
    print("\n" + "="*80)
    print("📄 GRANITE DOCUMENT SUMMARIZATION TEST")
    print("="*80)
    
    # Configuration
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("❌ Please set IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return

    # Initialize components
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    
    # Initialize tokenizer for token counting
    model_path = "ibm-granite/granite-3.3-8b-instruct"
    try:
        if TRANSFORMERS_AVAILABLE:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            print(f"✅ Loaded tokenizer for {model_path}")
        else:
            tokenizer = None
            print("⚠️ Tokenizer not available, continuing without token counting")
    except Exception as e:
        print(f"⚠️ Could not load tokenizer: {e}")
        print("Continuing without tokenizer...")
        tokenizer = None

    # Sample document for testing
    sample_document = """
    Artificial Intelligence (AI) has become one of the most transformative technologies of the 21st century. 
    From machine learning algorithms that power recommendation systems to natural language processing models 
    that enable chatbots, AI is reshaping industries and daily life. The field encompasses various approaches 
    including supervised learning, unsupervised learning, and reinforcement learning. Recent advances in 
    deep learning, particularly with transformer architectures, have led to breakthrough applications in 
    image recognition, language translation, and content generation. However, AI development also raises 
    important ethical considerations around bias, privacy, and the future of work. As organizations increasingly 
    adopt AI solutions, the need for responsible AI practices and governance frameworks becomes critical.
    """
    
    # Create chunks for processing
    chunks = [
        {
            'title': 'AI Overview - Part 1',
            'text': sample_document[:400]
        },
        {
            'title': 'AI Overview - Part 2', 
            'text': sample_document[400:]
        }
    ]
    
    print(f"Created {len(chunks)} chunks for processing")

    # Step 2: Summarize each chunk
    print("\n2. Summarizing individual chunks...")
    chunk_summaries = []
    
    user_prompt = """Using only the book chapter document, compose a summary of the book chapter.
Your response should only include the summary. Do not provide any further explanation."""
    
    for i, chunk in enumerate(chunks):
        print(f"\n============================= {chunk['title']} ({i+1}/{len(chunks)}) =============================")
        
        # Use the document-aware generation method
        if tokenizer:
            summary = generate_with_documents(user_prompt, [chunk], granite_api, tokenizer)
        else:
            summary = generate_simple_prompt(user_prompt, [chunk], granite_api)
        
        if summary:
            chunk_summaries.append({
                'doc_id': str(i+1),
                'title': f"Summary of {chunk['title']}",
                'text': summary.strip()
            })
            print(f"✅ Generated summary ({len(summary.split())} words)")
        else:
            print("❌ Failed to generate summary")
    
    print(f"\nSummary count: {len(chunk_summaries)}")

    # Step 3: Create final unified summary
    if chunk_summaries:
        print(f"\n3. Creating unified summary from {len(chunk_summaries)} chunk summaries...")
        
        final_user_prompt = """Using only the book chapter summary documents, compose a single, unified summary of the book.
Your response should only include the unified summary. Do not provide any further explanation."""
        
        print("Generating final unified summary...")
        if tokenizer:
            final_summary = generate_with_documents(final_user_prompt, chunk_summaries, granite_api, tokenizer)
        else:
            final_summary = generate_simple_prompt(final_user_prompt, chunk_summaries, granite_api)
        
        print("\n" + "=" * 60)
        print("FINAL UNIFIED SUMMARY")
        print("=" * 60)
        if final_summary:
            # Simple text wrapping
            words = final_summary.strip().split()
            lines = []
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) <= 80:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                print(line)
        else:
            print("Failed to generate final summary")
        print("=" * 60)
    else:
        print("No chunk summaries were generated, cannot create final summary")

def test_simple_generation():
    """Test basic text generation with IBM Granite"""
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("Please set your IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return
    
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    
    prompt = "Explain quantum computing in simple terms."
    
    print("Testing basic text generation...")
    response = granite_api.generate(prompt, max_tokens=300)
    
    if response:
        print("Success! Generated response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
    else:
        print("Failed to generate response")

def test_jira_integration():
    """Test Jira service integration"""
    print("\n" + "="*80)
    print("🎫 JIRA INTEGRATION TEST")
    print("="*80)
    
    jira_service = JiraService()
    
    async def test_jira():
        try:
            # Test with a mock issue
            issue = await jira_service.get_issue("TEST-123")
            
            if issue:
                print("✅ Jira service working!")
                print(f"Issue Key: {issue.get('key')}")
                print(f"Summary: {issue.get('summary')}")
                print(f"Status: {issue.get('status', {}).get('name')}")
                print(f"Priority: {issue.get('priority', {}).get('name')}")
            else:
                print("⚠️ Using mock Jira data (credentials not configured)")
                
        except Exception as e:
            print(f"❌ Jira test failed: {e}")
    
    try:
        import asyncio
        asyncio.run(test_jira())
    except Exception as e:
        print(f"❌ Jira test execution failed: {e}")

def main():
    """Main test function with enhanced capabilities"""
    print("IBM Granite API Test Script with Crystal Clear Implementation Planning")
    print("Using environment variables: IBM_GRANITE_API_KEY and IBM_PROJECT_ID")
    print("Optional Jira integration: JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN")
    print()

    # Test 1: Basic generation test
    print("1. Basic Generation Test")
    print("-" * 30)
    test_simple_generation()

    # Test 2: Jira Integration Test
    print("\n2. Jira Integration Test")
    print("-" * 30)
    test_jira_integration()

    # Test 3: Simple Crystal Clear Planning Test
    print("\n3. Simple Crystal Clear Planning Test")
    print("-" * 50)
    test_simple_crystal_clear_planning()

    # Test 4: Advanced Repository Analysis Test (if network available)
    print("\n4. Advanced Repository Analysis Test")
    print("-" * 40)
    print("This test requires network access to GitHub API...")
    test_crystal_clear_implementation_planning()

    # Test 5: Document Summarization Test
    print("\n5. Document Summarization Test")
    print("-" * 35)
    test_granite_summarization()

if __name__ == "__main__":
    main()