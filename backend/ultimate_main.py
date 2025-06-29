#!/usr/bin/env python3
"""
Ultimate GitHub-Jira AI Assistant - Enhanced with Advanced Large Repository Analysis
Integrates comprehensive GitHub analysis with IBM Granite for context-aware implementation plans
"""

import os
import sys
import logging
import json
import time
import base64
import requests
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re
from dataclasses import dataclass

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
# DATA STRUCTURES
# ================================

@dataclass
class FileAnalysis:
    """Enhanced file analysis data structure"""
    path: str
    name: str
    type: str
    size: int
    language: str
    relevance_score: float
    relevance_level: str
    context_matches: List[str]
    code_patterns: List[str]
    dependencies: List[str]
    functions: List[str]
    classes: List[str]
    imports: List[str]
    content_preview: Optional[str] = None
    modification_priority: str = "low"
    suggested_changes: Optional[List[str]] = None

    def __post_init__(self):
        if self.suggested_changes is None:
            self.suggested_changes = []

@dataclass
class RepositoryInsights:
    """Repository insights and patterns"""
    architecture_type: str
    framework: str
    tech_stack: List[str]
    patterns: Dict[str, List[str]]
    entry_points: List[str]
    config_files: List[str]
    test_files: List[str]
    build_files: List[str]
    style_approach: str
    state_management: str
    routing_approach: str

# ================================
# JIRA SERVICE (Unchanged)
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
# ADVANCED GITHUB REPOSITORY ANALYZER
# ================================

class AdvancedGitHubAnalyzer:
    """Advanced GitHub repository analyzer optimized for large repositories"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
        self.base_url = 'https://api.github.com'
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Advanced patterns for different languages and frameworks
        self.LANGUAGE_PATTERNS = {
            'javascript': {
                'extensions': ['.js', '.mjs', '.cjs'],
                'frameworks': ['react', 'vue', 'angular', 'express', 'next'],
                'config_files': ['package.json', 'webpack.config.js', 'babel.config.js'],
                'patterns': {
                    'component': r'(function|const|class)\s+(\w+Component?)',
                    'export': r'export\s+(default\s+)?(function|const|class|interface)',
                    'import': r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
                }
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'frameworks': ['react', 'angular', 'nest', 'next'],
                'config_files': ['tsconfig.json', 'angular.json'],
                'patterns': {
                    'interface': r'interface\s+(\w+)',
                    'type': r'type\s+(\w+)',
                    'class': r'class\s+(\w+)',
                    'function': r'function\s+(\w+)'
                }
            },
            'python': {
                'extensions': ['.py'],
                'frameworks': ['django', 'flask', 'fastapi', 'pyramid'],
                'config_files': ['requirements.txt', 'setup.py', 'pyproject.toml'],
                'patterns': {
                    'class': r'class\s+(\w+)',
                    'function': r'def\s+(\w+)',
                    'import': r'from\s+(\S+)\s+import|import\s+(\S+)'
                }
            }
        }
        
        # Framework-specific patterns
        self.FRAMEWORK_INDICATORS = {
            'react': ['jsx', 'useState', 'useEffect', 'component', 'props'],
            'vue': ['template', 'script', 'style', 'setup', 'ref'],
            'angular': ['@Component', '@Injectable', '@NgModule', 'selector'],
            'next': ['getStaticProps', 'getServerSideProps', 'pages/', 'app/'],
            'django': ['models.py', 'views.py', 'urls.py', 'settings.py'],
            'flask': ['app.py', 'routes.py', '@app.route', 'Blueprint']
        }
        
        logger.info(f"✅ Advanced GitHub analyzer initialized (token: {'Yes' if self.github_token else 'No'})")
    
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
        """Get comprehensive repository information"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get repo info: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return None
    
    def get_repository_tree_sync(self, owner: str, repo: str, recursive: bool = True) -> Optional[Dict]:
        """Get complete repository tree structure synchronously"""
        try:
            # First get the default branch
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return None
            
            default_branch = repo_info.get('default_branch', 'main')
            
            # Get the tree recursively
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}"
            if recursive:
                url += "?recursive=1"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get repository tree: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting repository tree: {e}")
            return None

    def get_file_content_sync(self, owner: str, repo: str, file_path: str) -> Tuple[Optional[str], Dict]:
        """Get file content synchronously"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                metadata = {
                    'size': data.get('size', 0),
                    'type': data.get('type', 'file'),
                    'encoding': data.get('encoding', 'unknown')
                }
                
                if data.get('encoding') == 'base64':
                    content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                    return content, metadata
                
                return data.get('content', ''), metadata
            return None, {}
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {e}")
            return None, {}

    async def get_repository_tree(self, owner: str, repo: str, recursive: bool = True) -> Optional[Dict]:
        """Get complete repository tree structure using Git Trees API"""
        try:
            # First get the default branch
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return None
            
            default_branch = repo_info.get('default_branch', 'main')
            
            # Get the tree recursively
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}"
            if recursive:
                url += "?recursive=1"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get repository tree: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting repository tree: {e}")
            return None
    
    def extract_smart_keywords(self, ticket_summary: str, ticket_description: str) -> Dict[str, List[str]]:
        """Extract intelligent keywords using NLP-like approaches"""
        combined_text = f"{ticket_summary} {ticket_description}".lower()
        
        keyword_categories = {
            'ui_components': [],
            'functionality': [],
            'data_flow': [],
            'navigation': [],
            'styling': [],
            'business_logic': [],
            'api_integration': [],
            'testing': []
        }
        
        # Enhanced keyword mapping with context
        keyword_mappings = {
            'ui_components': {
                'keywords': ['button', 'form', 'input', 'modal', 'dialog', 'component', 'widget', 'card', 'table', 'list'],
                'patterns': [r'create.*component', r'add.*button', r'new.*form', r'build.*ui']
            },
            'functionality': {
                'keywords': ['function', 'feature', 'functionality', 'behavior', 'action', 'operation'],
                'patterns': [r'implement.*feature', r'add.*functionality', r'create.*function']
            },
            'data_flow': {
                'keywords': ['data', 'api', 'fetch', 'load', 'save', 'store', 'database', 'model'],
                'patterns': [r'fetch.*data', r'save.*to', r'load.*from', r'api.*call']
            },
            'navigation': {
                'keywords': ['navigate', 'route', 'page', 'redirect', 'link', 'menu', 'header', 'sidebar'],
                'patterns': [r'navigate.*to', r'add.*page', r'create.*route']
            },
            'styling': {
                'keywords': ['style', 'css', 'theme', 'color', 'layout', 'design', 'appearance'],
                'patterns': [r'style.*component', r'change.*color', r'update.*theme']
            },
            'business_logic': {
                'keywords': ['logic', 'rule', 'validation', 'calculate', 'process', 'workflow'],
                'patterns': [r'business.*logic', r'add.*validation', r'implement.*rule']
            },
            'api_integration': {
                'keywords': ['api', 'endpoint', 'service', 'integration', 'external', 'webhook'],
                'patterns': [r'integrate.*api', r'call.*service', r'connect.*to']
            },
            'testing': {
                'keywords': ['test', 'testing', 'spec', 'unit', 'integration', 'e2e'],
                'patterns': [r'add.*test', r'test.*for', r'write.*spec']
            }
        }
        
        # Extract keywords using both direct matching and pattern matching
        for category, config in keyword_mappings.items():
            # Direct keyword matching
            for keyword in config['keywords']:
                if keyword in combined_text:
                    keyword_categories[category].append(keyword)
            
            # Pattern matching
            for pattern in config['patterns']:
                matches = re.findall(pattern, combined_text)
                if matches:
                    keyword_categories[category].extend(matches)
        
        # Remove duplicates and empty categories
        for category in keyword_categories:
            keyword_categories[category] = list(set(keyword_categories[category]))
        
        return keyword_categories
    
    def analyze_code_content(self, content: str, file_extension: str) -> Dict[str, List[str]]:
        """Analyze code content to extract functions, classes, imports, etc."""
        if not content:
            return {'functions': [], 'classes': [], 'imports': [], 'patterns': []}
        
        content_lower = content.lower()
        results = {
            'functions': [],
            'classes': [],
            'imports': [],
            'patterns': []
        }
        
        # Get language-specific patterns
        language = None
        for lang, config in self.LANGUAGE_PATTERNS.items():
            if file_extension in config['extensions']:
                language = lang
                break
        
        if language and language in self.LANGUAGE_PATTERNS:
            patterns = self.LANGUAGE_PATTERNS[language]['patterns']
            
            for pattern_type, pattern in patterns.items():
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                if matches:
                    if pattern_type == 'import':
                        results['imports'].extend([match for match in matches if match])
                    elif pattern_type in ['function', 'class']:
                        results[pattern_type + 's'].extend([match for match in matches if match])
                    else:
                        results['patterns'].extend([f"{pattern_type}: {match}" for match in matches if match])
        
        # Framework detection
        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            if any(indicator in content_lower for indicator in indicators):
                results['patterns'].append(f"framework: {framework}")
        
        return results
    
    def calculate_advanced_relevance(self, file_path: str, file_name: str, file_content: str, 
                                   keyword_categories: Dict, repo_insights: RepositoryInsights) -> FileAnalysis:
        """Calculate advanced relevance score with multiple factors"""
        
        file_ext = '.' + file_name.split('.')[-1] if '.' in file_name else ''
        file_lower = file_path.lower()
        content_lower = file_content.lower() if file_content else ""
        
        relevance_score = 0.0
        context_matches = []
        modification_priority = "low"
        suggested_changes = []
        
        # Base file type scoring
        file_type_scores = {
            '.tsx': 3.0, '.jsx': 3.0, '.ts': 2.5, '.js': 2.5,
            '.vue': 3.0, '.py': 2.5, '.css': 2.0, '.scss': 2.0,
            '.html': 1.5, '.json': 1.0
        }
        
        base_score = file_type_scores.get(file_ext, 0.5)
        relevance_score += base_score
        
        # Keyword matching with weighted scoring
        total_keyword_matches = 0
        for category, keywords in keyword_categories.items():
            category_matches = 0
            for keyword in keywords:
                # File path matching (higher weight)
                if keyword in file_lower:
                    relevance_score += 2.0
                    context_matches.append(f"Path contains '{keyword}' ({category})")
                    category_matches += 1
                
                # Content matching
                if file_content and keyword in content_lower:
                    count = content_lower.count(keyword)
                    relevance_score += min(count * 0.5, 2.0)  # Cap at 2.0 per keyword
                    context_matches.append(f"Content mentions '{keyword}' {count} times ({category})")
                    category_matches += 1
            
            total_keyword_matches += category_matches
        
        # Architecture pattern matching
        if repo_insights.framework in file_lower or any(tech in file_lower for tech in repo_insights.tech_stack):
            relevance_score += 1.5
            context_matches.append(f"Matches repository framework: {repo_insights.framework}")
        
        # Code analysis
        code_analysis = self.analyze_code_content(file_content, file_ext)
        
        # Entry point files get higher priority
        if file_path in repo_insights.entry_points:
            relevance_score += 2.0
            modification_priority = "high"
            context_matches.append("Entry point file")
        
        # Configuration files
        if file_name in repo_insights.config_files:
            relevance_score += 1.5
            context_matches.append("Configuration file")
        
        # Determine file type and language
        file_type = self._determine_file_type(file_path, file_name, file_content)
        language = self._determine_language(file_ext, file_content)
        
        # Generate suggested changes based on context
        suggested_changes = self._generate_suggested_changes(
            file_path, file_type, keyword_categories, code_analysis
        )
        
        # Determine modification priority
        if relevance_score >= 5.0:
            modification_priority = "critical"
        elif relevance_score >= 3.0:
            modification_priority = "high"
        elif relevance_score >= 1.5:
            modification_priority = "medium"
        
        # Determine relevance level
        if relevance_score >= 4.0:
            relevance_level = "high"
        elif relevance_score >= 2.0:
            relevance_level = "medium"
        else:
            relevance_level = "low"
        
        return FileAnalysis(
            path=file_path,
            name=file_name,
            type=file_type,
            size=len(file_content) if file_content else 0,
            language=language,
            relevance_score=relevance_score,
            relevance_level=relevance_level,
            context_matches=context_matches,
            code_patterns=code_analysis.get('patterns', []),
            dependencies=code_analysis.get('imports', []),
            functions=code_analysis.get('functions', []),
            classes=code_analysis.get('classes', []),
            imports=code_analysis.get('imports', []),
            content_preview=file_content[:500] if file_content else None,
            modification_priority=modification_priority,
            suggested_changes=suggested_changes
        )
    
    def _determine_file_type(self, file_path: str, file_name: str, content: str) -> str:
        """Determine the type of file based on path, name, and content"""
        file_ext = '.' + file_name.split('.')[-1] if '.' in file_name else ''
        path_lower = file_path.lower()
        
        # Configuration files
        config_files = ['package.json', 'tsconfig.json', 'webpack.config.js', 'next.config.js', 
                       'tailwind.config.js', 'babel.config.js', '.env', 'requirements.txt']
        if file_name in config_files:
            return 'config'
        
        # Component files
        if any(indicator in path_lower for indicator in ['component', 'widget', 'element']):
            return 'component'
        
        # Page files
        if any(indicator in path_lower for indicator in ['page', 'view', 'screen']):
            return 'page'
        
        # Style files
        if file_ext in ['.css', '.scss', '.sass', '.less', '.styl']:
            return 'style'
        
        # Test files
        if any(indicator in path_lower for indicator in ['test', 'spec', '__tests__', '.test.', '.spec.']):
            return 'test'
        
        # API/Service files
        if any(indicator in path_lower for indicator in ['api', 'service', 'endpoint', 'controller']):
            return 'api'
        
        # Utility files
        if any(indicator in path_lower for indicator in ['util', 'helper', 'lib', 'common']):
            return 'utility'
        
        # By extension
        type_mappings = {
            '.tsx': 'react_component',
            '.jsx': 'react_component',
            '.vue': 'vue_component',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.py': 'python',
            '.html': 'template',
            '.json': 'data'
        }
        
        return type_mappings.get(file_ext, 'unknown')
    
    def _determine_language(self, file_ext: str, content: str) -> str:
        """Determine programming language"""
        language_mappings = {
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.py': 'python',
            '.vue': 'vue',
            '.css': 'css',
            '.scss': 'scss',
            '.html': 'html',
            '.json': 'json'
        }
        
        return language_mappings.get(file_ext, 'unknown')
    
    def _generate_suggested_changes(self, file_path: str, file_type: str, 
                                  keyword_categories: Dict, code_analysis: Dict) -> List[str]:
        """Generate specific suggested changes based on analysis"""
        suggestions = []
        
        # UI component suggestions
        if 'ui_components' in keyword_categories and keyword_categories['ui_components']:
            if file_type in ['react_component', 'vue_component', 'component']:
                suggestions.append("Add new UI components or modify existing ones")
                suggestions.append("Update component props and state management")
                suggestions.append("Implement responsive design patterns")
        
        # Functionality suggestions
        if 'functionality' in keyword_categories and keyword_categories['functionality']:
            if file_type in ['javascript', 'typescript', 'python']:
                suggestions.append("Implement new business logic functions")
                suggestions.append("Add error handling and validation")
                suggestions.append("Update existing function signatures")
        
        # Styling suggestions
        if 'styling' in keyword_categories and keyword_categories['styling']:
            if file_type == 'style':
                suggestions.append("Update CSS classes and styling rules")
                suggestions.append("Implement new design system tokens")
                suggestions.append("Add responsive breakpoints")
        
        # API integration suggestions
        if 'api_integration' in keyword_categories and keyword_categories['api_integration']:
            if file_type in ['api', 'service', 'javascript', 'typescript']:
                suggestions.append("Add new API endpoints or modify existing ones")
                suggestions.append("Update request/response handling")
                suggestions.append("Implement proper error handling for API calls")
        
        # Configuration suggestions
        if file_type == 'config':
            suggestions.append("Update configuration settings")
            suggestions.append("Add new environment variables")
            suggestions.append("Modify build or bundling settings")
        
        return suggestions
    
    def analyze_repository_insights(self, tree_data: Dict, repo_info: Dict) -> RepositoryInsights:
        """Analyze repository to extract architectural insights"""
        
        tree_items = tree_data.get('tree', [])
        all_files = [item for item in tree_items if item['type'] == 'blob']
        
        # Detect framework and architecture
        framework = "unknown"
        tech_stack = []
        patterns = {
            'components': [],
            'pages': [],
            'services': [],
            'utilities': []
        }
        
        # Framework detection logic
        file_extensions = [Path(item['path']).suffix for item in all_files]
        file_paths = [item['path'] for item in all_files]
        
        # React/Next.js detection
        if any(ext in ['.jsx', '.tsx'] for ext in file_extensions):
            if any('pages/' in path or 'app/' in path for path in file_paths):
                framework = "next.js"
            else:
                framework = "react"
            tech_stack.extend(['react', 'javascript'])
        
        # Vue detection
        elif any(ext == '.vue' for ext in file_extensions):
            framework = "vue"
            tech_stack.extend(['vue', 'javascript'])
        
        # Python framework detection
        elif any(ext == '.py' for ext in file_extensions):
            if any('manage.py' in path or 'settings.py' in path for path in file_paths):
                framework = "django"
            elif any('app.py' in path or 'routes.py' in path for path in file_paths):
                framework = "flask"
            else:
                framework = "python"
            tech_stack.append('python')
        
        # TypeScript detection
        if any(ext in ['.ts', '.tsx'] for ext in file_extensions):
            tech_stack.append('typescript')
        
        # Categorize files into patterns
        for item in all_files:
            path = item['path'].lower()
            if 'component' in path:
                patterns['components'].append(item['path'])
            elif any(keyword in path for keyword in ['page', 'view', 'screen']):
                patterns['pages'].append(item['path'])
            elif any(keyword in path for keyword in ['service', 'api', 'endpoint']):
                patterns['services'].append(item['path'])
            elif any(keyword in path for keyword in ['util', 'helper', 'lib']):
                patterns['utilities'].append(item['path'])
        
        # Identify important files
        entry_points = []
        config_files = []
        test_files = []
        build_files = []
        
        config_patterns = ['package.json', 'tsconfig.json', 'next.config.js', 'webpack.config.js', 
                          'tailwind.config.js', 'babel.config.js', 'requirements.txt', 'setup.py']
        
        for item in all_files:
            path = item['path']
            filename = Path(path).name
            
            if filename in config_patterns:
                config_files.append(path)
            elif any(pattern in path.lower() for pattern in ['index.', 'main.', 'app.']):
                entry_points.append(path)
            elif any(pattern in path.lower() for pattern in ['test', 'spec', '__tests__']):
                test_files.append(path)
            elif any(pattern in filename.lower() for pattern in ['webpack', 'rollup', 'vite', 'gulpfile', 'gruntfile']):
                build_files.append(path)
        
        # Determine styling approach
        style_approach = "unknown"
        if any('.css' in path for path in file_paths):
            if any('tailwind' in path.lower() for path in file_paths):
                style_approach = "tailwind"
            elif any('styled' in path.lower() for path in file_paths):
                style_approach = "styled-components"
            else:
                style_approach = "css"
        elif any('.scss' in path for path in file_paths):
            style_approach = "scss"
        
        # Determine state management
        state_management = "unknown"
        if any('redux' in path.lower() for path in file_paths):
            state_management = "redux"
        elif any('zustand' in path.lower() for path in file_paths):
            state_management = "zustand"
        elif any('context' in path.lower() for path in file_paths):
            state_management = "react-context"
        
        # Determine routing approach
        routing_approach = "unknown"
        if framework == "next.js":
            routing_approach = "next-router"
        elif any('router' in path.lower() for path in file_paths):
            routing_approach = "react-router"
        
        return RepositoryInsights(
            architecture_type=framework,
            framework=framework,
            tech_stack=tech_stack,
            patterns=patterns,
            entry_points=entry_points,
            config_files=config_files,
            test_files=test_files,
            build_files=build_files,
            style_approach=style_approach,
            state_management=state_management,
            routing_approach=routing_approach
        )
    
    async def get_file_content_batch(self, owner: str, repo: str, file_paths: List[str]) -> Dict[str, str]:
        """Get multiple file contents efficiently using async requests"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for file_path in file_paths:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
                headers = self.headers.copy()
                task = self._fetch_file_content(session, url, headers, file_path)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            file_contents = {}
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result:
                    file_contents[file_paths[i]] = result
            
            return file_contents
    
    async def _fetch_file_content(self, session: aiohttp.ClientSession, url: str, 
                                 headers: Dict, file_path: str) -> Optional[str]:
        """Fetch individual file content asynchronously"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('encoding') == 'base64':
                        content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                        return content
                return None
        except Exception as e:
            logger.debug(f"Failed to fetch {file_path}: {e}")
            return None
    
    def analyze_repository_optimized(self, github_url: str, ticket_summary: str, 
                                     ticket_description: str = "") -> Dict:
        """Optimized repository analysis focused on actionable insights"""
        try:
            logger.info(f"🔍 Starting optimized repository analysis: {github_url}")
            
            # Parse GitHub URL
            parsed = self.parse_github_url(github_url)
            if not parsed:
                return {"error": "Invalid GitHub URL"}
            
            owner, repo = parsed['owner'], parsed['repo']
            
            # Get repository information
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return {"error": "Repository not found or not accessible"}
            
            # Extract intelligent keywords from ticket
            keyword_categories = self.extract_smart_keywords(ticket_summary, ticket_description)
            logger.info(f"🎯 Keywords: {sum(len(v) for v in keyword_categories.values())} terms")
            
            # Get repository tree (synchronously)
            tree_data = self.get_repository_tree_sync(owner, repo)
            if not tree_data:
                return {"error": "Failed to get repository structure"}
            
            # Analyze repository insights
            repo_insights = self.analyze_repository_insights(tree_data, repo_info)
            logger.info(f"🏗️ Framework: {repo_insights.framework}")
            
            # Filter relevant files intelligently (reduced scope)
            relevant_files = self._filter_relevant_files(tree_data, keyword_categories, repo_insights)
            logger.info(f"📂 Found {len(relevant_files)} relevant files")
            
            # Analyze only top 8 files for efficiency
            analyzed_files = []
            for file_item in relevant_files[:8]:
                try:
                    file_content, metadata = self.get_file_content_sync(owner, repo, file_item['path'])
                    if file_content and metadata.get('size', 0) < 50000:  # Smaller size limit
                        analysis = self.calculate_advanced_relevance(
                            file_item['path'], 
                            file_item['name'], 
                            file_content,
                            keyword_categories, 
                            repo_insights
                        )
                        analyzed_files.append(analysis)
                except Exception as e:
                    logger.debug(f"Skip {file_item['path']}: {e}")
                    continue
            
            # Sort by relevance score
            analyzed_files.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Return optimized results
            result = {
                "success": True,
                "repository": {
                    "name": repo_info['name'],
                    "language": repo_info.get('language', ''),
                },
                "insights": {
                    "framework": repo_insights.framework,
                    "tech_stack": repo_insights.tech_stack[:3],  # Limit to top 3
                    "architecture": repo_insights.architecture_type,
                },
                "analyzed_files": [
                    {
                        "path": f.path,
                        "type": f.type,
                        "modification_priority": f.modification_priority,
                        "suggested_changes": f.suggested_changes[:2] if f.suggested_changes else [],  # Limit suggestions
                        "functions": f.functions[:3] if f.functions else [],  # Limit functions
                        "classes": f.classes[:2] if f.classes else []  # Limit classes
                    } for f in analyzed_files[:5]  # Top 5 files only
                ],
                "total_files_in_repo": len(tree_data.get('tree', [])),
                "files_analyzed": len(analyzed_files),
                "high_priority_files": len([f for f in analyzed_files if f.modification_priority in ['critical', 'high']])
            }
            
            logger.info(f"✅ Optimized analysis complete - {len(analyzed_files)} files")
            return result
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {"error": f"Repository analysis failed: {str(e)}"}

    def analyze_repository_sync(self, github_url: str, ticket_summary: str, 
                                       ticket_description: str = "") -> Dict:
        """Synchronous repository analysis for better reliability"""
        try:
            logger.info(f"🔍 Starting advanced repository analysis: {github_url}")
            
            # Parse GitHub URL
            parsed = self.parse_github_url(github_url)
            if not parsed:
                return {"error": "Invalid GitHub URL"}
            
            owner, repo = parsed['owner'], parsed['repo']
            
            # Get repository information
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return {"error": "Repository not found or not accessible"}
            
            # Extract intelligent keywords from ticket
            keyword_categories = self.extract_smart_keywords(ticket_summary, ticket_description)
            logger.info(f"🎯 Extracted keyword categories: {list(keyword_categories.keys())}")
            
            # Get repository tree (synchronously)
            tree_data = self.get_repository_tree_sync(owner, repo)
            if not tree_data:
                return {"error": "Failed to get repository structure"}
            
            # Analyze repository insights
            repo_insights = self.analyze_repository_insights(tree_data, repo_info)
            logger.info(f"🏗️ Repository framework: {repo_insights.framework}")
            
            # Filter relevant files intelligently
            relevant_files = self._filter_relevant_files(tree_data, keyword_categories, repo_insights)
            logger.info(f"📂 Found {len(relevant_files)} potentially relevant files")
            
            # Analyze top files with content
            analyzed_files = []
            for file_item in relevant_files[:15]:  # Analyze top 15 files
                try:
                    file_content, metadata = self.get_file_content_sync(owner, repo, file_item['path'])
                    if file_content and metadata.get('size', 0) < 100000:  # Skip very large files
                        analysis = self.calculate_advanced_relevance(
                            file_item['path'], 
                            file_item['name'], 
                            file_content,
                            keyword_categories, 
                            repo_insights
                        )
                        analyzed_files.append(analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze {file_item['path']}: {e}")
                    continue
            
            # Sort by relevance score
            analyzed_files.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Generate comprehensive analysis summary
            analysis_summary = self._generate_analysis_summary(
                repo_info, repo_insights, analyzed_files, keyword_categories
            )
            
            # Prepare results
            result = {
                "success": True,
                "repository": {
                    "name": repo_info['name'],
                    "description": repo_info.get('description', ''),
                    "language": repo_info.get('language', ''),
                    "stars": repo_info.get('stargazers_count', 0),
                    "forks": repo_info.get('forks_count', 0),
                    "size": repo_info.get('size', 0)
                },
                "insights": {
                    "framework": repo_insights.framework,
                    "tech_stack": repo_insights.tech_stack,
                    "architecture": repo_insights.architecture_type,
                    "styling_approach": repo_insights.style_approach,
                    "state_management": repo_insights.state_management,
                    "routing": repo_insights.routing_approach
                },
                "keyword_analysis": keyword_categories,
                "analyzed_files": [
                    {
                        "path": f.path,
                        "name": f.name,
                        "type": f.type,
                        "language": f.language,
                        "relevance_score": f.relevance_score,
                        "relevance_level": f.relevance_level,
                        "modification_priority": f.modification_priority,
                        "context_matches": f.context_matches,
                        "suggested_changes": f.suggested_changes,
                        "functions": f.functions,
                        "classes": f.classes,
                        "content_preview": f.content_preview[:300] if f.content_preview else None
                    } for f in analyzed_files
                ],
                "file_patterns": {
                    "components": [f.path for f in analyzed_files if f.type == "component"],
                    "pages": [f.path for f in analyzed_files if f.type == "page"],
                    "services": [f.path for f in analyzed_files if f.type == "service"],
                    "utilities": [f.path for f in analyzed_files if f.type == "utility"]
                },
                "entry_points": repo_insights.entry_points,
                "config_files": repo_insights.config_files,
                "analysis_summary": analysis_summary,
                "total_files_in_repo": len(tree_data.get('tree', [])),
                "files_analyzed": len(analyzed_files),
                "high_priority_files": len([f for f in analyzed_files if f.modification_priority in ['critical', 'high']])
            }
            
            logger.info(f"✅ Advanced repository analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"Advanced repository analysis failed: {e}")
            return {"error": f"Repository analysis failed: {str(e)}"}

    async def analyze_large_repository(self, github_url: str, ticket_summary: str, 
                                      ticket_description: str = "") -> Dict:
        """Analyze large repositories efficiently with smart filtering"""
        try:
            logger.info(f"🔍 Starting advanced analysis of large repository: {github_url}")
            
            # Parse URL
            parsed = self.parse_github_url(github_url)
            if not parsed:
                return {"error": "Invalid GitHub URL"}
            
            owner, repo = parsed['owner'], parsed['repo']
            
            # Get repository information
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return {"error": "Repository not found or not accessible"}
            
            # Extract smart keywords from ticket
            keyword_categories = self.extract_smart_keywords(ticket_summary, ticket_description)
            logger.info(f"🔍 Extracted keyword categories: {list(keyword_categories.keys())}")
            
            # Get complete repository tree
            tree_data = await self._get_repository_tree_async(owner, repo)
            if not tree_data:
                return {"error": "Failed to fetch repository tree"}
            
            # Analyze repository insights
            repo_insights = self.analyze_repository_insights(tree_data, repo_info)
            logger.info(f"🏗️ Detected architecture: {repo_insights.framework}")
            
            # Filter relevant files using intelligent scoring
            relevant_files = self._filter_relevant_files(
                tree_data, keyword_categories, repo_insights
            )
            
            logger.info(f"📂 Found {len(relevant_files)} potentially relevant files")
            
            # Get file contents for high-priority files (limit to avoid timeouts)
            high_priority_files = [f for f in relevant_files if f['estimated_priority'] in ['critical', 'high']][:10]
            file_paths = [f['path'] for f in high_priority_files]
            
            # Fetch file contents asynchronously
            file_contents = await self.get_file_content_batch(owner, repo, file_paths)
            
            # Perform detailed analysis on fetched files
            analyzed_files = []
            for file_info in high_priority_files:
                file_path = file_info['path']
                file_content = file_contents.get(file_path, "")
                
                analysis = self.calculate_advanced_relevance(
                    file_path, 
                    Path(file_path).name,
                    file_content,
                    keyword_categories,
                    repo_insights
                )
                
                analyzed_files.append(analysis)
            
            # Sort by relevance score
            analyzed_files.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Generate comprehensive summary
            analysis_summary = self._generate_analysis_summary(
                repo_info, repo_insights, analyzed_files, keyword_categories
            )
            
            result = {
                "success": True,
                "repository": {
                    "name": repo_info['name'],
                    "description": repo_info.get('description', ''),
                    "language": repo_info.get('language', ''),
                    "topics": repo_info.get('topics', []),
                    "stars": repo_info.get('stargazers_count', 0),
                    "forks": repo_info.get('forks_count', 0),
                    "size": repo_info.get('size', 0)
                },
                "insights": {
                    "architecture": repo_insights.architecture_type,
                    "framework": repo_insights.framework,
                    "tech_stack": repo_insights.tech_stack,
                    "styling_approach": repo_insights.style_approach,
                    "state_management": repo_insights.state_management,
                    "routing": repo_insights.routing_approach
                },
                "keyword_analysis": keyword_categories,
                "analyzed_files": [
                    {
                        "path": f.path,
                        "name": f.name,
                        "type": f.type,
                        "language": f.language,
                        "relevance_score": f.relevance_score,
                        "relevance_level": f.relevance_level,
                        "modification_priority": f.modification_priority,
                        "context_matches": f.context_matches,
                        "suggested_changes": f.suggested_changes,
                        "functions": f.functions[:5],  # Limit for response size
                        "classes": f.classes[:5],
                        "imports": f.imports[:10],
                        "content_preview": f.content_preview
                    }
                    for f in analyzed_files[:15]  # Top 15 files
                ],
                "file_patterns": {
                    "components": repo_insights.patterns.get('components', [])[:5],
                    "pages": repo_insights.patterns.get('pages', [])[:5],
                    "services": repo_insights.patterns.get('services', [])[:5],
                    "utilities": repo_insights.patterns.get('utilities', [])[:5]
                },
                "entry_points": repo_insights.entry_points,
                "config_files": repo_insights.config_files,
                "analysis_summary": analysis_summary,
                "total_files_in_repo": len(tree_data.get('tree', [])),
                "files_analyzed": len(analyzed_files),
                "high_priority_files": len([f for f in analyzed_files if f.modification_priority in ['critical', 'high']])
            }
            
            logger.info(f"✅ Advanced repository analysis complete")
            return result
            
        except Exception as e:
            logger.error(f"Advanced repository analysis failed: {e}")
            return {"error": f"Repository analysis failed: {str(e)}"}
    
    async def _get_repository_tree_async(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository tree asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: asyncio.run(self.get_repository_tree(owner, repo, True))
        )
    
    def _filter_relevant_files(self, tree_data: Dict, keyword_categories: Dict, 
                             repo_insights: RepositoryInsights) -> List[Dict]:
        """Filter files using intelligent scoring before fetching content"""
        
        tree_items = tree_data.get('tree', [])
        files = [item for item in tree_items if item['type'] == 'blob']
        
        # Define file priorities based on extensions and patterns
        high_priority_extensions = {'.tsx', '.jsx', '.vue', '.ts', '.js', '.py'}
        medium_priority_extensions = {'.css', '.scss', '.html', '.json'}
        
        # Define path patterns that indicate importance
        important_patterns = [
            'component', 'page', 'view', 'service', 'api', 'util', 'helper',
            'src/', 'app/', 'pages/', 'components/', 'lib/', 'utils/'
        ]
        
        relevant_files = []
        
        for file_item in files:
            file_path = file_item['path']
            file_name = Path(file_path).name
            file_ext = Path(file_path).suffix
            path_lower = file_path.lower()
            
            # Skip certain files and directories
            if any(skip in path_lower for skip in [
                'node_modules/', '.git/', 'dist/', 'build/', '.next/', 
                'coverage/', '__pycache__/', '.cache/', 'vendor/'
            ]):
                continue
            
            # Calculate initial priority score
            priority_score = 0.0
            estimated_priority = "low"
            reasons = []
            
            # Extension-based scoring
            if file_ext in high_priority_extensions:
                priority_score += 3.0
                reasons.append(f"High-priority extension: {file_ext}")
            elif file_ext in medium_priority_extensions:
                priority_score += 1.5
                reasons.append(f"Medium-priority extension: {file_ext}")
            
            # Path pattern scoring
            for pattern in important_patterns:
                if pattern in path_lower:
                    priority_score += 1.0
                    reasons.append(f"Important path pattern: {pattern}")
            
            # Keyword matching in file path
            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword in path_lower:
                        priority_score += 2.0
                        reasons.append(f"Keyword match: {keyword} ({category})")
            
            # Framework-specific patterns
            if repo_insights.framework != "unknown":
                framework_patterns = {
                    'react': ['component', 'hook', 'context'],
                    'next.js': ['page', 'api', 'layout'],
                    'vue': ['component', 'composable', 'store'],
                    'django': ['model', 'view', 'serializer', 'admin'],
                    'flask': ['route', 'blueprint', 'model']
                }
                
                patterns = framework_patterns.get(repo_insights.framework, [])
                for pattern in patterns:
                    if pattern in path_lower:
                        priority_score += 1.5
                        reasons.append(f"Framework pattern: {pattern}")
            
            # Entry points and config files get high priority
            if file_path in repo_insights.entry_points:
                priority_score += 3.0
                estimated_priority = "critical"
                reasons.append("Entry point file")
            elif file_name in repo_insights.config_files:
                priority_score += 2.0
                reasons.append("Configuration file")
            
            # Determine estimated priority
            if priority_score >= 5.0:
                estimated_priority = "critical"
            elif priority_score >= 3.0:
                estimated_priority = "high"
            elif priority_score >= 1.5:
                estimated_priority = "medium"
            
            # Only include files with some relevance
            if priority_score > 0.5:
                relevant_files.append({
                    'path': file_path,
                    'name': file_name,
                    'extension': file_ext,
                    'size': file_item.get('size', 0),
                    'priority_score': priority_score,
                    'estimated_priority': estimated_priority,
                    'reasons': reasons
                })
        
        # Sort by priority score
        relevant_files.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Return top files to avoid overwhelming the analysis
        return relevant_files[:50]
    
    def _generate_analysis_summary(self, repo_info: Dict, repo_insights: RepositoryInsights, 
                                 analyzed_files: List[FileAnalysis], keyword_categories: Dict) -> str:
        """Generate comprehensive analysis summary"""
        
        high_priority_files = [f for f in analyzed_files if f.modification_priority in ['critical', 'high']]
        
        summary = f"""
🏗️ ADVANCED REPOSITORY ANALYSIS SUMMARY:

📋 PROJECT OVERVIEW:
• Name: {repo_info.get('name', 'Unknown')}
• Description: {repo_info.get('description', 'No description available')}
• Primary Language: {repo_info.get('language', 'Unknown')}
• Repository Size: {repo_info.get('size', 0):,} KB
• Stars: {repo_info.get('stargazers_count', 0):,} | Forks: {repo_info.get('forks_count', 0):,}

🔧 TECHNICAL ARCHITECTURE:
• Framework: {repo_insights.framework}
• Tech Stack: {', '.join(repo_insights.tech_stack)}
• Styling: {repo_insights.style_approach}
• State Management: {repo_insights.state_management}
• Routing: {repo_insights.routing_approach}

🎯 TICKET CONTEXT ANALYSIS:
"""
        
        for category, keywords in keyword_categories.items():
            if keywords:
                summary += f"• {category.replace('_', ' ').title()}: {', '.join(keywords[:3])}\n"
        
        summary += f"""
📂 KEY FILES FOR MODIFICATION ({len(high_priority_files)} high-priority):
"""
        
        for file_analysis in high_priority_files[:8]:
            summary += f"""
📄 {file_analysis.path}
   Type: {file_analysis.type} | Priority: {file_analysis.modification_priority}
   Relevance Score: {file_analysis.relevance_score:.1f}
   Key Matches: {', '.join(file_analysis.context_matches[:2]) if file_analysis.context_matches else 'None'}
   Suggested Changes: {', '.join(file_analysis.suggested_changes[:2]) if file_analysis.suggested_changes and isinstance(file_analysis.suggested_changes, list) else 'None'}
"""
        
        summary += f"""
🔍 ANALYSIS METRICS:
• Total Files Analyzed: {len(analyzed_files)}
• High-Priority Files: {len([f for f in analyzed_files if f.modification_priority == 'high'])}
• Critical Files: {len([f for f in analyzed_files if f.modification_priority == 'critical'])}
• Average Relevance Score: {sum(f.relevance_score for f in analyzed_files) / len(analyzed_files):.1f}
"""
        
        return summary

# ================================
# ENHANCED IBM VISION ANALYSIS SERVICE
# ================================

class EnhancedVisionAPI:
    """Enhanced IBM Llama Vision API client for analyzing images and documents"""
    
    def __init__(self, api_key: str, project_id: str, base_url: str = "https://eu-de.ml.cloud.ibm.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url
        self.generation_endpoint = f"{base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
        
        if not self.api_key or not self.project_id:
            logger.warning("IBM Vision API configuration incomplete")
    
    def get_bearer_token(self):
        """Generate Bearer token from IBM API key (reuse from EnhancedGraniteAPI)"""
        try:
            if self.bearer_token and time.time() < self.token_expires_at:
                return self.bearer_token
            
            if not self.api_key or self.api_key.strip() == "":
                logger.error("❌ IBM API key is not configured or empty")
                return None
            
            logger.info("🔄 Generating new Bearer token for Vision API...")
            
            token_url = "https://iam.cloud.ibm.com/identity/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                'apikey': self.api_key.strip()
            }
            
            response = requests.post(token_url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' not in token_data:
                    logger.error(f"❌ No access token in response: {token_data}")
                    return None
                
                self.bearer_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in - 300
                
                logger.info(f"✅ Vision API Bearer token generated! Expires in {expires_in//60} minutes")
                return self.bearer_token
            else:
                logger.error(f"❌ Error generating Bearer token (status {response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Unexpected error generating Bearer token: {e}")
            return None
    
    def analyze_image_with_context(self, image_data: str, context_prompt: str, max_tokens: int = 500) -> str:
        """Analyze image with specific context using Llama Vision model"""
        try:
            bearer_token = self.get_bearer_token()
            if not bearer_token:
                logger.error("❌ Failed to get Bearer token for vision analysis")
                return ""
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Construct vision prompt
            vision_prompt = f"""Analyze this image in the context of software development and provide detailed insights.

Context: {context_prompt}

Please analyze the image and provide:
1. What is shown in the image (UI components, diagrams, screenshots, etc.)
2. Technical requirements that can be derived from the image
3. Implementation suggestions based on what you see
4. Any specific design patterns or UI elements to replicate
5. Potential technical challenges or considerations

Provide a detailed technical analysis that can guide implementation."""

            body = {
                "input": vision_prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "min_new_tokens": 0,
                    "repetition_penalty": 1
                },
                "model_id": "meta-llama/llama-3-2-11b-vision-instruct",
                "project_id": self.project_id,
                "moderations": {
                    "hap": {
                        "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                        "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
                    },
                    "pii": {
                        "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                        "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
                    },
                    "granite_guardian": {"input": {"threshold": 1}}
                }
            }
            
            # Add image data to the request
            if image_data:
                body["input"] = f"{vision_prompt}\n\nImage: {image_data}"
            
            logger.info(f"🔍 Analyzing image with Vision API...")
            
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=body,
                timeout=180
            )
            
            logger.info(f"🔍 Vision API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Vision API error {response.status_code}: {response.text}")
                return ""
            
            result = response.json()
            
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                if generated_text:
                    logger.info(f"✅ Vision analysis completed, length: {len(generated_text)} characters")
                    return generated_text
                else:
                    logger.error("❌ Empty response from Vision API")
                    return ""
            else:
                logger.error(f"❌ Unexpected response format from Vision API: {result}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Vision analysis failed: {e}")
            return ""
    
    def analyze_pdf_content(self, pdf_text: str, context_prompt: str, max_tokens: int = 800) -> str:
        """Analyze PDF content for implementation insights"""
        try:
            bearer_token = self.get_bearer_token()
            if not bearer_token:
                return ""
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Truncate PDF text if too long
            if len(pdf_text) > 5000:
                pdf_text = pdf_text[:5000] + "... (content truncated)"
            
            analysis_prompt = f"""Analyze this PDF document content in the context of software development and extract implementation requirements.

Context: {context_prompt}

PDF Content:
{pdf_text}

Please provide:
1. Key technical requirements mentioned in the document
2. Specific features or functionality described
3. Business rules or logic that need implementation
4. Data structures or entities mentioned
5. Integration points or external dependencies
6. Performance or security considerations
7. User interface requirements or specifications

Focus on actionable technical insights that can guide implementation."""
            
            body = {
                "input": analysis_prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "min_new_tokens": 0,
                    "repetition_penalty": 1
                },
                "model_id": "meta-llama/llama-3-2-11b-vision-instruct",
                "project_id": self.project_id
            }
            
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=body,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    return result['results'][0].get('generated_text', '')
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ PDF analysis failed: {e}")
            return ""

# ================================
# ENHANCED JIRA SERVICE WITH ATTACHMENTS
# ================================

class EnhancedJiraService(JiraService):
    """Enhanced Jira service with attachment and discussion analysis"""
    
    def get_issue_attachments(self, issue_key: str) -> List[Dict]:
        """Get attachments for a Jira issue"""
        if not hasattr(self, 'headers'):
            return []
        
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            params = {'expand': 'attachment'}
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                attachments = data.get('fields', {}).get('attachment', [])
                
                logger.info(f"📎 Found {len(attachments)} attachments for issue {issue_key}")
                return attachments
            else:
                logger.error(f"Failed to get attachments for {issue_key}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting attachments for {issue_key}: {e}")
            return []
    
    def get_issue_comments(self, issue_key: str, max_comments: int = 20) -> List[Dict]:
        """Get comments/discussions for a Jira issue"""
        if not hasattr(self, 'headers'):
            return []
        
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
            params = {'maxResults': max_comments, 'orderBy': 'created'}
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                comments = data.get('comments', [])
                
                logger.info(f"💬 Found {len(comments)} comments for issue {issue_key}")
                return comments
            else:
                logger.error(f"Failed to get comments for {issue_key}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting comments for {issue_key}: {e}")
            return []
    
    def download_attachment_content(self, attachment_url: str, attachment_name: str) -> Optional[bytes]:
        """Download attachment content"""
        if not hasattr(self, 'headers'):
            return None
        
        try:
            # Check if it's a supported file type
            supported_types = ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.doc', '.docx']
            if not any(attachment_name.lower().endswith(ext) for ext in supported_types):
                logger.warning(f"⚠️ Unsupported attachment type: {attachment_name}")
                return None
            
            response = requests.get(attachment_url, headers=self.headers, timeout=60)
            
            if response.status_code == 200:
                logger.info(f"✅ Downloaded attachment: {attachment_name} ({len(response.content)} bytes)")
                return response.content
            else:
                logger.error(f"Failed to download attachment {attachment_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading attachment {attachment_name}: {e}")
            return None

def extract_pdf_text(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            logger.info(f"✅ Extracted {len(text)} characters from PDF")
            return text
            
        except ImportError:
            logger.warning("⚠️ PyPDF2 not installed. Install with: pip install PyPDF2")
            return "PDF content could not be extracted (PyPDF2 not available)"
            
    except Exception as e:
        logger.error(f"❌ Error extracting PDF text: {e}")
        return "PDF content extraction failed"

def encode_image_to_base64(image_content: bytes) -> str:
    """Encode image content to base64 for vision analysis"""
    try:
        import base64
        encoded = base64.b64encode(image_content).decode('utf-8')
        logger.info(f"✅ Encoded image to base64 ({len(encoded)} characters)")
        return encoded
    except Exception as e:
        logger.error(f"❌ Error encoding image: {e}")
        return ""

def summarize_discussions(comments: List[Dict], ticket_context: str) -> str:
    """Summarize issue discussions and comments"""
    if not comments:
        return "No discussions found for this issue."
    
    try:
        # Extract comment text and metadata
        discussion_text = ""
        for comment in comments[:10]:  # Limit to recent 10 comments
            author = comment.get('author', {}).get('displayName', 'Unknown')
            created = comment.get('created', '')
            body = comment.get('body', '')
            
            # Simple text extraction (Jira uses ADF format)
            if isinstance(body, dict):
                body = extract_text_from_adf(body)
            
            discussion_text += f"\n--- Comment by {author} on {created} ---\n{body}\n"
        
        # Create summary using simple text processing
        summary = f"""
DISCUSSION SUMMARY for {ticket_context}:

Total Comments: {len(comments)}
Key Discussion Points:
{discussion_text[:20000]}...

This discussion provides additional context for implementation requirements and clarifications.
"""
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error summarizing discussions: {e}")
        return "Discussion summary could not be generated."

def extract_text_from_adf(adf_content: dict) -> str:
    """Extract plain text from Atlassian Document Format"""
    try:
        def extract_text_recursive(node):
            text = ""
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text += node.get('text', '')
                elif 'content' in node:
                    for child in node['content']:
                        text += extract_text_recursive(child)
            elif isinstance(node, list):
                for item in node:
                    text += extract_text_recursive(item)
            return text
        
        return extract_text_recursive(adf_content)
        
    except Exception as e:
        logger.debug(f"ADF text extraction failed: {e}")
        return str(adf_content)

# ================================
# ENHANCED IBM GRANITE SERVICE
# ================================

class EnhancedGraniteAPI:
    """Enhanced IBM Granite API client with advanced repository context integration"""
    
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
        try:
            # Check if we have a valid cached token
            if self.bearer_token and time.time() < self.token_expires_at:
                logger.debug("🔄 Using cached Bearer token")
                return self.bearer_token
            
            # Validate API key
            if not self.api_key or self.api_key.strip() == "":
                logger.error("❌ IBM API key is not configured or empty")
                return None
            
            logger.info("🔄 Generating new Bearer token...")
            
            token_url = "https://iam.cloud.ibm.com/identity/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                'apikey': self.api_key.strip()
            }
            
            response = requests.post(token_url, headers=headers, data=data, timeout=30)
            
            logger.info(f"🔄 Token request status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                if 'access_token' not in token_data:
                    logger.error(f"❌ No access token in response: {token_data}")
                    return None
                
                self.bearer_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in - 300  # 5 min buffer
                
                logger.info(f"✅ Bearer token generated! Expires in {expires_in//60} minutes")
                return self.bearer_token
            else:
                logger.error(f"❌ Error generating Bearer token (status {response.status_code}): {response.text}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    if 'error_description' in error_data:
                        logger.error(f"❌ IBM API Error: {error_data['error_description']}")
                except:
                    pass
                
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout while generating Bearer token")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection error while generating Bearer token")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error while generating Bearer token: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error generating Bearer token: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 3000, temperature: float = 0.2) -> str:
        """Generate text using IBM Granite"""
        try:
            # Validate inputs
            if not prompt or not prompt.strip():
                logger.error("Empty prompt provided")
                return ""
            
            if not self.api_key or not self.project_id:
                logger.error("IBM Granite API key or project ID not configured")
                return ""
            
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
                    "repetition_penalty": 1.1
                },
                "model_id": "ibm/granite-3-8b-instruct",
                "project_id": self.project_id
            }
            
            if payload["parameters"]["decoding_method"] == "sample":
                payload["parameters"]["temperature"] = temperature
            
            logger.info(f"🤖 Making API call to IBM Granite with prompt length: {len(prompt)} characters")
            logger.info(f"🤖 API endpoint: {self.generation_endpoint}")
            logger.info(f"🤖 Model ID: {payload['model_id']}")
            logger.info(f"🤖 Project ID: {self.project_id}")
            logger.info(f"🤖 Max tokens: {payload['parameters']['max_new_tokens']}")
            
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload,
                timeout=180
            )
            
            logger.info(f"🤖 IBM Granite API response status: {response.status_code}")
            logger.info(f"🤖 Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"❌ IBM Granite API error {response.status_code}: {response.text}")
                try:
                    error_data = response.json()
                    logger.error(f"❌ Error details: {error_data}")
                except:
                    logger.error("❌ Could not parse error response as JSON")
                return ""
                
            result = response.json()
            logger.info(f"🤖 Raw API response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            logger.info(f"🤖 Full response: {result}")
            
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                logger.info(f"🤖 Generated text length: {len(generated_text)}")
                logger.info(f"🤖 Generated text preview: {generated_text[:100]}...")
                
                if generated_text:
                    logger.info(f"✅ Generated text successfully, length: {len(generated_text)} characters")
                    return generated_text
                else:
                    logger.error("❌ Empty generated text in response")
                    logger.error(f"❌ Result structure: {result['results'][0]}")
                    return ""
            else:
                logger.error(f"❌ Unexpected response format from IBM Granite")
                logger.error(f"❌ Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                logger.error(f"❌ Full response: {result}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error("❌ IBM Granite API timeout (180s)")
            return ""
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection error to IBM Granite API")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error to IBM Granite API: {e}")
            return ""
        except Exception as e:
            logger.error(f"❌ Unexpected error in IBM Granite API call: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return ""
    
    def create_optimized_implementation_prompt(self, ticket_data: Dict, repo_analysis: Optional[Dict] = None, 
                                             attachment_analysis: Optional[Dict] = None, 
                                             discussion_summary: Optional[str] = None) -> str:
        """Create optimized, focused implementation prompt with actionable file changes"""
        
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
        
        # Extract key information only
        framework = "unknown"
        high_priority_files = []
        visual_requirements = []
        doc_requirements = []
        
        # Repository insights (minimal)
        if repo_analysis and repo_analysis.get("success"):
            insights = repo_analysis.get("insights", {}) or {}
            framework = insights.get("framework", "unknown")
            analyzed_files = repo_analysis.get("analyzed_files", []) or []
            
            if analyzed_files and isinstance(analyzed_files, list):
                high_priority_files = [
                    f for f in analyzed_files 
                    if isinstance(f, dict) and f.get('modification_priority') in ['critical', 'high']
                ][:5]  # Limit to top 5 files
        
        # Extract visual insights (concise)
        if attachment_analysis:
            # Image insights
            for img in attachment_analysis.get("image_analysis", []):
                analysis = img.get("analysis", "")
                if analysis and len(analysis) > 100:
                    # Extract key points only
                    visual_requirements.append(analysis[:300] + "...")
            
            # PDF insights
            for pdf in attachment_analysis.get("pdf_analysis", []):
                analysis = pdf.get("analysis", "")
                if analysis and len(analysis) > 100:
                    # Extract key points only
                    doc_requirements.append(analysis[:300] + "...")
        
        # Team insights (minimal)
        team_notes = ""
        if discussion_summary and len(discussion_summary) > 100:
            team_notes = discussion_summary[:200] + "..."

        
        prompt = f"""You are a senior developer. Analyze this ticket and provide SPECIFIC file changes needed.

TICKET: {title}
DESCRIPTION: {description}
FRAMEWORK: {framework}

TARGET FILES TO MODIFY:"""
        
        # Add high priority files
        for i, file_info in enumerate(high_priority_files[:3]):
            file_path = file_info.get('path', 'Unknown')
            file_type = file_info.get('type', 'Unknown')
            prompt += f"\n{i+1}. {file_path} ({file_type})"
        
        # Add visual requirements if any
        if visual_requirements:
            prompt += f"\n\nVISUAL REQUIREMENTS:\n{visual_requirements[0][:200]}..."
        
        # Add document requirements if any
        if doc_requirements:
            prompt += f"\n\nDOCUMENT REQUIREMENTS:\n{doc_requirements[0][:200]}..."
        
        # Add team notes if any
        if team_notes:
            prompt += f"\n\nTEAM NOTES: {team_notes}"
        
        prompt += f"""

PROVIDE ONLY:
1. EXACT file paths to modify
2. SPECIFIC code changes for each file
3. Implementation steps

FORMAT:
FILE: path/to/file.ext
CHANGES:
- Specific change 1
- Specific change 2

IMPLEMENTATION:
1. Step 1
2. Step 2
3. Step 3

Keep response under 1000 words. Focus on actionable changes only."""

        return prompt
    
    async def analyze_ticket_attachments(self, issue_key: str) -> Optional[Dict]:
        """Analyze ticket attachments using vision API"""
        try:
            logger.info(f"🔍 Analyzing attachments for {issue_key}...")
            
            # Get attachments from Jira
            attachments = jira_service.get_issue_attachments(issue_key)
            if not attachments:
                logger.info(f"📎 No attachments found for {issue_key}")
                return None
            
            analysis_results = {
                "total_attachments": len(attachments),
                "image_analysis": [],
                "pdf_analysis": [],
                "unsupported_files": []
            }
            
            for attachment in attachments[:5]:  # Limit to 5 attachments
                attachment_name = attachment.get('filename', '')
                attachment_url = attachment.get('content', '')
                
                logger.info(f"📎 Processing attachment: {attachment_name}")
                
                # Download attachment content
                content = jira_service.download_attachment_content(attachment_url, attachment_name)
                if not content:
                    analysis_results["unsupported_files"].append(attachment_name)
                    continue
                
                # Process based on file type
                if attachment_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Image analysis using vision API
                    try:
                        encoded_image = encode_image_to_base64(content)
                        if encoded_image:
                            context = f"Jira issue {issue_key} attachment analysis"
                            vision_result = vision_api.analyze_image_with_context(
                                encoded_image, context, max_tokens=600
                            )
                            
                            if vision_result:
                                analysis_results["image_analysis"].append({
                                    "filename": attachment_name,
                                    "analysis": vision_result,
                                    "size": len(content)
                                })
                                logger.info(f"✅ Image analysis completed for {attachment_name}")
                    except Exception as e:
                        logger.error(f"❌ Image analysis failed for {attachment_name}: {e}")
                
                elif attachment_name.lower().endswith('.pdf'):
                    # PDF analysis
                    try:
                        pdf_text = extract_pdf_text(content)
                        if pdf_text and len(pdf_text.strip()) > 50:
                            context = f"Jira issue {issue_key} PDF document analysis"
                            pdf_result = vision_api.analyze_pdf_content(
                                pdf_text, context, max_tokens=800
                            )
                            
                            if pdf_result:
                                analysis_results["pdf_analysis"].append({
                                    "filename": attachment_name,
                                    "analysis": pdf_result,
                                    "text_length": len(pdf_text)
                                })
                                logger.info(f"✅ PDF analysis completed for {attachment_name}")
                    except Exception as e:
                        logger.error(f"❌ PDF analysis failed for {attachment_name}: {e}")
                
                else:
                    analysis_results["unsupported_files"].append(attachment_name)
            
            logger.info(f"✅ Attachment analysis completed for {issue_key}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"❌ Attachment analysis failed for {issue_key}: {e}")
            return None
    
    async def analyze_ticket_discussions(self, issue_key: str) -> Optional[str]:
        """Analyze ticket discussions and comments"""
        try:
            logger.info(f"💬 Analyzing discussions for {issue_key}...")
            
            # Get comments from Jira
            comments = jira_service.get_issue_comments(issue_key, max_comments=15)
            if not comments:
                logger.info(f"💬 No comments found for {issue_key}")
                return None
            
            # Generate discussion summary
            summary = summarize_discussions(comments, issue_key)
            
            # Enhance summary with AI if possible
            if summary and len(summary) > 100:
                try:
                    enhanced_prompt = f"""Analyze this Jira issue discussion and extract key implementation insights:

Discussion Content:
{summary}

Please provide:
1. Key clarifications about requirements
2. Important technical decisions made in discussions
3. Any changes to original requirements
4. Developer concerns or questions raised
5. Additional context that affects implementation

Focus on actionable insights that can improve the implementation plan."""

                    enhanced_summary = self.generate(enhanced_prompt, max_tokens=600, temperature=0.2)
                    if enhanced_summary:
                        return enhanced_summary
                
                except Exception as e:
                    logger.warning(f"⚠️ AI enhancement of discussion failed: {e}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Discussion analysis failed for {issue_key}: {e}")
            return None
    
    def create_simplified_implementation_prompt(self, ticket_data: Dict, repo_analysis: Optional[Dict] = None) -> str:
        """Create a simplified implementation prompt for when the complex one fails"""
        
        # Safe field extraction
        title = ticket_data.get('summary') or 'N/A'
        description = ticket_data.get('description') or 'N/A'
        issue_type = 'N/A'
        priority = 'N/A'
        
        if ticket_data.get('issuetype') and isinstance(ticket_data['issuetype'], dict):
            issue_type = ticket_data['issuetype'].get('name', 'N/A')
        if ticket_data.get('priority') and isinstance(ticket_data['priority'], dict):
            priority = ticket_data['priority'].get('name', 'N/A')
        
        # Extract framework info
        framework = "Unknown"
        if repo_analysis and repo_analysis.get("success"):
            insights = repo_analysis.get("insights", {}) or {}
            framework = insights.get('framework', 'Unknown')
        
        prompt = f"""Create implementation plan for: {title}

DESCRIPTION: {description}
FRAMEWORK: {framework if repo_analysis else 'Unknown'}

PROVIDE:
1. Files to modify (exact paths)
2. Specific changes for each file
3. Implementation steps

FORMAT:
FILE: path/to/file.ext
CHANGES:
- Change 1
- Change 2

STEPS:
1. Step 1
2. Step 2

Keep under 500 words. Focus on actionable changes only."""

        return prompt
    
    async def generate_implementation_plan(self, ticket_data: Dict, repo_analysis: Optional[Dict] = None) -> Dict:
        """Generate comprehensive implementation plan with advanced repository context"""
        try:
            logger.info("🔄 Starting implementation plan generation...")
            
            # Create comprehensive prompt with all available context
            logger.info("📝 Creating comprehensive prompt with all analysis...")
            
            # Get enhanced context from attachments and discussions
            attachment_analysis = None
            discussion_summary = None
            
            if ticket_data.get('key'):
                # Analyze attachments and discussions
                attachment_analysis = await self.analyze_ticket_attachments(ticket_data['key'])
                discussion_summary = await self.analyze_ticket_discussions(ticket_data['key'])
            
            prompt = self.create_optimized_implementation_prompt(
                ticket_data, repo_analysis, attachment_analysis, discussion_summary
            )
            logger.info(f"📝 Comprehensive prompt created, length: {len(prompt)} characters")
            
            # Check if prompt is too long
            if len(prompt) > 8000:
                logger.warning(f"⚠️ Prompt is very long ({len(prompt)} chars), truncating...")
                prompt = prompt[:8000] + "\n\nPlease provide specific file changes and implementation steps."
            
            # Try with optimized parameters
            logger.info("🤖 Generating response with IBM Granite...")
            response = self.generate(prompt, max_tokens=1200, temperature=0.1)
            logger.info(f"🤖 Generated response, length: {len(response) if response else 0} characters")
            
            # If no response, try with simpler prompt
            if not response or not response.strip():
                logger.warning("⚠️ No response from complex prompt, trying simplified version...")
                simplified_prompt = self.create_simplified_implementation_prompt(ticket_data, repo_analysis)
                logger.info(f"📝 Simplified prompt length: {len(simplified_prompt)} characters")
                response = self.generate(simplified_prompt, max_tokens=800, temperature=0.2)
                logger.info(f"🤖 Simplified response, length: {len(response) if response else 0} characters")
            
            if response and response.strip():
                logger.info("✅ Implementation plan generated successfully")
                return {
                    "success": True,
                    "implementation_plan": response.strip(),
                    "ticket_key": ticket_data.get('key', 'N/A'),
                    "ticket_summary": ticket_data.get('summary') or 'N/A',
                    "model_used": "ibm/granite-3-8b-instruct",
                    "generated_at": datetime.now().isoformat(),
                    "repository_analyzed": bool(repo_analysis and repo_analysis.get("success")),
                    "context_depth": "advanced_deep_analysis" if repo_analysis else "basic",
                    "files_analyzed": len(repo_analysis.get("analyzed_files", [])) if repo_analysis else 0,
                    "analysis_quality": "comprehensive" if repo_analysis and len(repo_analysis.get("analyzed_files", [])) > 5 else "standard"
                }
            else:
                logger.error("❌ No response generated from IBM Granite after multiple attempts")
                return {
                    "success": False,
                    "error": "Failed to generate implementation plan - empty response from AI after multiple attempts",
                    "ticket_key": ticket_data.get('key', 'N/A'),
                    "troubleshooting": "Please check IBM Granite API configuration and quota limits"
                }
                
        except Exception as e:
            logger.error(f"❌ Exception in generate_implementation_plan: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error generating implementation plan: {str(e)}",
                "ticket_key": ticket_data.get('key', 'N/A')
            }
    
    def check_connection(self) -> Dict:
        """Test connection to IBM Granite API"""
        try:
            logger.info("🔍 Testing IBM Granite API connection...")
            
            # Check configuration
            if not self.api_key or not self.project_id:
                missing = []
                if not self.api_key:
                    missing.append("API_KEY")
                if not self.project_id:
                    missing.append("PROJECT_ID")
                return {
                    "status": "error", 
                    "message": f"IBM Granite configuration incomplete. Missing: {', '.join(missing)}",
                    "configured": False
                }
            
            logger.info("✅ Configuration present, testing token generation...")
            
            # Test token generation
            token = self.get_bearer_token()
            if not token:
                return {
                    "status": "error", 
                    "message": "Failed to generate Bearer token. Check your IBM API key.",
                    "configured": True,
                    "token_generated": False
                }
            
            logger.info("✅ Token generated, testing text generation...")
            
            # Test text generation
            test_response = self.generate("Hello, this is a connection test.", max_tokens=20, temperature=0)
            
            if test_response and test_response.strip():
                logger.info("✅ IBM Granite connection test successful!")
                return {
                    "status": "success",
                    "message": "Successfully connected to IBM Granite",
                    "model": "ibm/granite-3-8b-instruct",
                    "configured": True,
                    "token_generated": True,
                    "response_generated": True,
                    "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
                }
            else:
                logger.error("❌ No response generated from IBM Granite")
                return {
                    "status": "error", 
                    "message": "Failed to generate text response. API connection works but model did not respond.",
                    "configured": True,
                    "token_generated": True,
                    "response_generated": False
                }
                
        except Exception as e:
            logger.error(f"❌ Connection test exception: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                "status": "error", 
                "message": f"Connection test failed: {str(e)}",
                "configured": bool(self.api_key and self.project_id)
            }

# ================================
# PR ANALYSIS FUNCTIONS
# ================================

async def analyze_pull_request(pr_url: str, issue_data: Dict) -> Dict:
    """Comprehensive Pull Request analysis against Jira ticket requirements"""
    try:
        logger.info(f"🔍 Starting comprehensive PR analysis for: {pr_url}")
        
        # Parse PR URL
        pr_info = parse_pr_url(pr_url)
        if not pr_info:
            return {"success": False, "error": "Invalid GitHub PR URL format"}
        
        owner, repo, pr_number = pr_info['owner'], pr_info['repo'], pr_info['pr_number']
        logger.info(f"📋 Analyzing PR #{pr_number} in {owner}/{repo}")
        
        # Get PR details from GitHub
        pr_details = await get_pr_details(owner, repo, pr_number)
        if not pr_details:
            return {"success": False, "error": "Failed to fetch PR details from GitHub"}
        
        # Get PR diff/changes
        pr_diff = await get_pr_diff(owner, repo, pr_number)
        if not pr_diff:
            return {"success": False, "error": "Failed to fetch PR diff from GitHub"}
        
        # Analyze PR against ticket requirements
        analysis_result = await analyze_pr_against_ticket(pr_details, pr_diff, issue_data)
        
        return {
            "success": True,
            "analysis": analysis_result,
            "pr_details": {
                "number": pr_number,
                "title": pr_details.get('title', ''),
                "state": pr_details.get('state', ''),
                "mergeable": pr_details.get('mergeable'),
                "mergeable_state": pr_details.get('mergeable_state', ''),
                "additions": pr_details.get('additions', 0),
                "deletions": pr_details.get('deletions', 0),
                "changed_files": pr_details.get('changed_files', 0),
                "user": pr_details.get('user', {}).get('login', ''),
                "created_at": pr_details.get('created_at', ''),
                "updated_at": pr_details.get('updated_at', '')
            },
            "ticket_info": {
                "key": issue_data.get('key', ''),
                "summary": issue_data.get('summary', ''),
                "description": issue_data.get('description', ''),
                "status": issue_data.get('status', {}).get('name', '') if issue_data.get('status') else '',
                "priority": issue_data.get('priority', {}).get('name', '') if issue_data.get('priority') else ''
            }
        }
        
    except Exception as e:
        logger.error(f"❌ PR analysis failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return {"success": False, "error": f"PR analysis failed: {str(e)}"}

def parse_pr_url(pr_url: str) -> Optional[Dict[str, str]]:
    """Parse GitHub PR URL to extract owner, repo, and PR number"""
    try:
        # Remove trailing slash and split
        pr_url = pr_url.rstrip('/')
        
        # Expected format: https://github.com/owner/repo/pull/123
        if 'github.com' not in pr_url or '/pull/' not in pr_url:
            return None
        
        parts = pr_url.split('/')
        if len(parts) < 6:
            return None
        
        # Find the github.com part
        github_index = -1
        for i, part in enumerate(parts):
            if 'github.com' in part:
                github_index = i
                break
        
        if github_index == -1 or github_index + 4 >= len(parts):
            return None
        
        owner = parts[github_index + 1]
        repo = parts[github_index + 2]
        pr_number = parts[github_index + 4]  # after 'pull'
        
        return {
            'owner': owner,
            'repo': repo,
            'pr_number': pr_number
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to parse PR URL {pr_url}: {e}")
        return None

async def get_pr_details(owner: str, repo: str, pr_number: str) -> Optional[Dict]:
    """Get PR details from GitHub API"""
    try:
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Failed to get PR details: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting PR details: {e}")
        return None

async def get_pr_diff(owner: str, repo: str, pr_number: str) -> Optional[str]:
    """Get PR diff from GitHub API"""
    try:
        headers = {'Accept': 'application/vnd.github.v3.diff'}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"❌ Failed to get PR diff: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting PR diff: {e}")
        return None

async def analyze_pr_against_ticket(pr_details: Dict, pr_diff: str, issue_data: Dict) -> Dict:
    """Analyze PR changes against Jira ticket requirements using IBM Granite"""
    try:
        logger.info("🤖 Analyzing PR against ticket requirements with IBM Granite...")
        
        # Create analysis prompt
        analysis_prompt = create_pr_analysis_prompt(pr_details, pr_diff, issue_data)
        
        # Generate analysis using IBM Granite
        analysis_response = granite_api.generate(analysis_prompt, max_tokens=20000, temperature=0.2)
        
        if not analysis_response or not analysis_response.strip():
            logger.warning("⚠️ No response from IBM Granite, using fallback analysis...")
            return create_fallback_analysis(pr_details, pr_diff, issue_data)
        
        # Parse the analysis response
        parsed_analysis = parse_granite_analysis(analysis_response, pr_details, issue_data)
        
        return parsed_analysis
        
    except Exception as e:
        logger.error(f"❌ Error in PR analysis: {e}")
        return create_fallback_analysis(pr_details, pr_diff, issue_data)

def create_pr_analysis_prompt(pr_details: Dict, pr_diff: str, issue_data: Dict) -> str:
    """Create analysis prompt for IBM Granite"""
    
    # Truncate diff if too long
    if len(pr_diff) > 8000:
        pr_diff = pr_diff[:8000] + "\n\n... (diff truncated for analysis)"
    
    prompt = f"""You are a Senior Code Reviewer analyzing a Pull Request against Jira ticket requirements.

JIRA TICKET INFORMATION:
- Key: {issue_data.get('key', 'N/A')}
- Summary: {issue_data.get('summary', 'N/A')}
- Description: {issue_data.get('description', 'N/A')}
- Priority: {issue_data.get('priority', {}).get('name', 'N/A') if issue_data.get('priority') else 'N/A'}
- Status: {issue_data.get('status', {}).get('name', 'N/A') if issue_data.get('status') else 'N/A'}

PULL REQUEST INFORMATION:
- Title: {pr_details.get('title', 'N/A')}
- Description: {pr_details.get('body', 'N/A')}
- Files Changed: {pr_details.get('changed_files', 0)}
- Additions: {pr_details.get('additions', 0)}
- Deletions: {pr_details.get('deletions', 0)}
- State: {pr_details.get('state', 'N/A')}
- Mergeable: {pr_details.get('mergeable', 'N/A')}

CODE CHANGES (DIFF):
{pr_diff}

ANALYSIS REQUIREMENTS:
Please analyze this PR and provide your assessment in the following format:

VALIDATION_STATUS: [APPROVED|NEEDS_CHANGES|REJECTED]
COMPLETENESS_SCORE: [0-100]
MERGE_RECOMMENDATION: [READY_TO_MERGE|NEEDS_IMPROVEMENTS|MAJOR_CHANGES_REQUIRED]

REQUIREMENT_ANALYSIS:
- [List each requirement from the ticket and whether it's addressed]

MISSING_REQUIREMENTS:
- [List any requirements not addressed in the PR]

SUGGESTIONS:
- [Specific suggestions for improvement]

CODE_QUALITY_ISSUES:
- [Any code quality concerns]

MERGE_BLOCKERS:
- [Any issues that prevent merging]

DETAILED_FEEDBACK:
[Provide detailed feedback about the PR quality, completeness, and alignment with ticket requirements]

Focus on:
1. Does the PR address all ticket requirements?
2. Is the code quality acceptable?
3. Are there any missing features or bugs?
4. Can this PR be safely merged?
5. What improvements are needed?
"""
    
    return prompt

def parse_granite_analysis(analysis_response: str, pr_details: Dict, issue_data: Dict) -> Dict:
    """Parse IBM Granite analysis response into structured format"""
    try:
        # Extract key information from the response
        lines = analysis_response.split('\n')
        
        # Default values
        validation_status = "needs_improvement"
        completeness_score = 50
        merge_recommendation = "needs_improvements"
        missing_requirements = []
        suggestions = []
        code_quality_issues = []
        merge_blockers = []
        feedback = analysis_response
        
        # Parse specific sections
        current_section = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('VALIDATION_STATUS:'):
                status = line.split(':', 1)[1].strip().lower()
                if 'approved' in status:
                    validation_status = "valid"
                elif 'rejected' in status:
                    validation_status = "invalid"
                else:
                    validation_status = "needs_improvement"
                    
            elif line.startswith('COMPLETENESS_SCORE:'):
                try:
                    score = int(''.join(filter(str.isdigit, line.split(':', 1)[1])))
                    completeness_score = max(0, min(100, score))
                except:
                    pass
                    
            elif line.startswith('MERGE_RECOMMENDATION:'):
                rec = line.split(':', 1)[1].strip().lower()
                if 'ready' in rec:
                    merge_recommendation = "ready_to_merge"
                elif 'major' in rec:
                    merge_recommendation = "major_changes_required"
                else:
                    merge_recommendation = "needs_improvements"
                    
            elif line.startswith('MISSING_REQUIREMENTS:'):
                current_section = 'missing'
            elif line.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
            elif line.startswith('CODE_QUALITY_ISSUES:'):
                current_section = 'quality'
            elif line.startswith('MERGE_BLOCKERS:'):
                current_section = 'blockers'
            elif line.startswith('DETAILED_FEEDBACK:'):
                current_section = 'feedback'
                feedback = ""
            elif line.startswith('-') and current_section:
                item = line[1:].strip()
                if item:
                    if current_section == 'missing':
                        missing_requirements.append(item)
                    elif current_section == 'suggestions':
                        suggestions.append(item)
                    elif current_section == 'quality':
                        code_quality_issues.append(item)
                    elif current_section == 'blockers':
                        merge_blockers.append(item)
            elif current_section == 'feedback' and line:
                feedback += line + "\n"
        
        # Determine overall merge status
        can_merge = (
            validation_status == "valid" and
            completeness_score >= 70 and
            merge_recommendation == "ready_to_merge" and
            len(merge_blockers) == 0
        )
        
        return {
            "validation_status": validation_status,
            "completeness_score": completeness_score,
            "merge_recommendation": merge_recommendation,
            "can_merge": can_merge,
            "missing_requirements": missing_requirements,
            "suggestions": suggestions,
            "code_quality_issues": code_quality_issues,
            "merge_blockers": merge_blockers,
            "feedback": feedback.strip() if feedback else analysis_response,
            "analysis_timestamp": datetime.now().isoformat(),
            "pr_summary": {
                "addresses_ticket": completeness_score >= 70,
                "code_quality": "good" if len(code_quality_issues) == 0 else "needs_improvement",
                "ready_for_merge": can_merge,
                "risk_level": "low" if can_merge else ("medium" if completeness_score >= 50 else "high")
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error parsing Granite analysis: {e}")
        return create_fallback_analysis(pr_details, "", issue_data)

def create_fallback_analysis(pr_details: Dict, pr_diff: str, issue_data: Dict) -> Dict:
    """Create fallback analysis when IBM Granite fails"""
    
    # Basic analysis based on PR details
    changed_files = pr_details.get('changed_files', 0)
    additions = pr_details.get('additions', 0)
    deletions = pr_details.get('deletions', 0)
    
    # Simple scoring based on change metrics
    if changed_files > 0:
        completeness_score = min(80, max(30, (changed_files * 10) + (additions // 10)))
    else:
        completeness_score = 20
    
    validation_status = "needs_improvement"
    if completeness_score >= 70:
        validation_status = "valid"
    elif completeness_score < 40:
        validation_status = "invalid"
    
    merge_recommendation = "needs_improvements"
    if completeness_score >= 80 and pr_details.get('mergeable'):
        merge_recommendation = "ready_to_merge"
    elif completeness_score < 40:
        merge_recommendation = "major_changes_required"
    
    can_merge = (
        validation_status == "valid" and
        pr_details.get('mergeable', False) and
        completeness_score >= 70
    )
    
    return {
        "validation_status": validation_status,
        "completeness_score": completeness_score,
        "merge_recommendation": merge_recommendation,
        "can_merge": can_merge,
        "missing_requirements": ["Unable to analyze requirements - IBM Granite AI unavailable"],
        "suggestions": [
            "Review PR manually against ticket requirements",
            "Ensure all acceptance criteria are met",
            "Run tests to verify functionality"
        ],
        "code_quality_issues": [],
        "merge_blockers": [] if can_merge else ["Manual review required"],
        "feedback": f"""
Automated analysis completed with basic heuristics:

PR Summary:
- Files changed: {changed_files}
- Lines added: {additions}
- Lines deleted: {deletions}
- Mergeable: {pr_details.get('mergeable', 'Unknown')}

Recommendation: {"Ready for merge" if can_merge else "Needs manual review"}

Note: Advanced AI analysis was unavailable. Please perform manual code review.
        """.strip(),
        "analysis_timestamp": datetime.now().isoformat(),
        "pr_summary": {
            "addresses_ticket": completeness_score >= 70,
            "code_quality": "unknown",
            "ready_for_merge": can_merge,
            "risk_level": "medium"
        }
    }

# ================================
# GLOBAL SERVICE INSTANCES
# ================================

API_KEY = os.getenv('IBM_GRANITE_API_KEY', '')
PROJECT_ID = os.getenv('IBM_PROJECT_ID', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

granite_api = EnhancedGraniteAPI(API_KEY, PROJECT_ID)
vision_api = EnhancedVisionAPI(API_KEY, PROJECT_ID)
jira_service = EnhancedJiraService()
github_analyzer = AdvancedGitHubAnalyzer(GITHUB_TOKEN)

# ================================
# FASTAPI APPLICATION
# ================================

app = FastAPI(
    title="Ultimate GitHub-Jira AI Assistant - Advanced Edition",
    version="5.0.0",
    description="Advanced AI assistant with intelligent large repository analysis and context-aware implementation plans"
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
        "message": "Ultimate GitHub-Jira AI Assistant - Advanced Large Repository Analysis",
        "version": "5.0.0",
        "services": {
            "granite": "IBM Granite 3-8B Instruct",
            "jira": "Atlassian Jira Cloud API",
            "github": "Advanced Large Repository Analysis API"
        },
        "features": [
            "Intelligent large repository analysis with async processing",
            "Advanced file relevance scoring with ML-like approaches",
            "Smart keyword extraction and context matching",
            "Framework and architecture pattern recognition",
            "Comprehensive code analysis with function/class detection",
            "Priority-based file modification suggestions",
            "Context-aware implementation plans with specific code examples",
            "Scalable analysis for repositories with thousands of files"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    try:
        granite_status = granite_api.check_connection()
        jira_status = {"status": "success", "message": "Jira configured"} if hasattr(jira_service, 'headers') else {"status": "warning", "message": "Jira not configured"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "granite": granite_status,
                "jira": jira_status,
                "github": {"status": "success", "message": "Advanced GitHub analyzer ready with async processing"}
            },
            "configuration": {
                "granite_configured": bool(API_KEY and PROJECT_ID),
                "jira_configured": bool(hasattr(jira_service, 'headers')),
                "github_configured": bool(GITHUB_TOKEN)
            },
            "capabilities": {
                "large_repo_analysis": True,
                "async_processing": True,
                "intelligent_filtering": True,
                "code_pattern_recognition": True,
                "context_aware_suggestions": True
            },
            "version": "5.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/api/test-granite")
async def test_granite_connection():
    """Test IBM Granite API connection and response generation"""
    try:
        logger.info("🧪 Testing IBM Granite API connection...")
        
        # Perform connection test
        result = granite_api.check_connection()
        
        # Additional detailed test
        simple_test = None
        try:
            logger.info("🧪 Testing simple text generation...")
            simple_response = granite_api.generate(
                "Write a simple hello message in one sentence.", 
                max_tokens=50, 
                temperature=0
            )
            simple_test = {
                "success": bool(simple_response and simple_response.strip()),
                "response": simple_response[:100] if simple_response else "",
                "response_length": len(simple_response) if simple_response else 0
            }
        except Exception as e:
            simple_test = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "test_type": "granite_connection",
            "timestamp": datetime.now().isoformat(),
            "connection_test": result,
            "simple_generation_test": simple_test,
            "configuration_status": {
                "api_key_configured": bool(os.getenv('IBM_GRANITE_API_KEY')),
                "project_id_configured": bool(os.getenv('IBM_PROJECT_ID')),
                "api_key_length": len(os.getenv('IBM_GRANITE_API_KEY', '')) if os.getenv('IBM_GRANITE_API_KEY') else 0,
                "project_id_format": "valid" if os.getenv('IBM_PROJECT_ID') and len(os.getenv('IBM_PROJECT_ID', '')) > 10 else "invalid"
            }
        }
    except Exception as e:
        logger.error(f"❌ Granite test failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Granite connection test failed: {str(e)}")

@app.post("/api/test-simple-generation")
async def test_simple_generation(request_data: dict):
    """Test simple text generation with custom prompt"""
    try:
        prompt = request_data.get('prompt', 'Hello, please respond with a simple greeting.')
        max_tokens = request_data.get('max_tokens', 100)
        temperature = request_data.get('temperature', 0.1)
        
        logger.info(f"🧪 Testing simple generation with prompt: {prompt[:50]}...")
        
        response = granite_api.generate(prompt, max_tokens=max_tokens, temperature=temperature)
        
        return {
            "success": bool(response and response.strip()),
            "prompt": prompt,
            "response": response,
            "response_length": len(response) if response else 0,
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Simple generation test failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Simple generation test failed: {str(e)}")

@app.post("/api/test-pr-validation")
async def test_pr_validation(request_data: dict):
    """Test PR validation functionality with sample data"""
    try:
        logger.info("🧪 Testing PR validation functionality...")
        
        # Default test data
        default_jira_key = request_data.get('jira_issue_key', 'TEST-123')
        default_pr_url = request_data.get('pr_url', 'https://github.com/octocat/Hello-World/pull/1')
        
        # Create mock issue data
        mock_issue = {
            'key': default_jira_key,
            'summary': 'Test feature implementation',
            'description': 'Implement new feature as requested',
            'status': {'name': 'In Progress'},
            'priority': {'name': 'Medium'}
        }
        
        # Test PR analysis
        analysis_result = await analyze_pull_request(default_pr_url, mock_issue)
        
        return {
            "test_type": "pr_validation",
            "timestamp": datetime.now().isoformat(),
            "test_inputs": {
                "jira_issue_key": default_jira_key,
                "pr_url": default_pr_url
            },
            "result": analysis_result,
            "status": "success" if analysis_result.get("success") else "failed"
        }
        
    except Exception as e:
        logger.error(f"❌ PR validation test failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PR validation test failed: {str(e)}")

@app.post("/api/test-vision-analysis")
async def test_vision_analysis(request_data: dict):
    """Test vision analysis functionality"""
    try:
        logger.info("🧪 Testing Vision Analysis functionality...")
        
        issue_key = request_data.get('issue_key', 'TEST-123')
        
        # Test attachment analysis
        attachment_result = await granite_api.analyze_ticket_attachments(issue_key)
        
        # Test discussion analysis  
        discussion_result = await granite_api.analyze_ticket_discussions(issue_key)
        
        return {
            "test_type": "vision_analysis",
            "timestamp": datetime.now().isoformat(),
            "issue_key": issue_key,
            "attachment_analysis": {
                "success": bool(attachment_result),
                "result": attachment_result
            },
            "discussion_analysis": {
                "success": bool(discussion_result),
                "result": discussion_result
            },
            "vision_api_status": {
                "configured": bool(vision_api.api_key and vision_api.project_id),
                "model": "meta-llama/llama-3-2-11b-vision-instruct"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Vision analysis test failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Vision analysis test failed: {str(e)}")

@app.get("/api/jira/issue/{issue_key}/attachments")
async def get_issue_attachments(issue_key: str):
    """Get attachments for a specific Jira issue"""
    try:
        attachments = jira_service.get_issue_attachments(issue_key)
        return {
            "issue_key": issue_key,
            "attachments": attachments,
            "total_count": len(attachments)
        }
    except Exception as e:
        logger.error(f"Failed to get attachments for {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jira/issue/{issue_key}/comments")
async def get_issue_comments(issue_key: str):
    """Get comments/discussions for a specific Jira issue"""
    try:
        comments = jira_service.get_issue_comments(issue_key)
        return {
            "issue_key": issue_key,
            "comments": comments,
            "total_count": len(comments)
        }
    except Exception as e:
        logger.error(f"Failed to get comments for {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/analyze-repository")
async def analyze_repository(request_data: dict):
    """Analyze repository structure and patterns"""
    try:
        github_url = request_data.get('github_url')
        ticket_summary = request_data.get('ticket_summary', '')
        ticket_description = request_data.get('ticket_description', '')
        
        if not github_url:
            raise HTTPException(status_code=400, detail="github_url is required")
        
        logger.info(f"🔍 Analyzing repository: {github_url}")
        
        # Perform advanced repository analysis
        analysis_result = await github_analyzer.analyze_large_repository(
            github_url, ticket_summary, ticket_description
        )
        
        if analysis_result.get("success"):
            logger.info(f"✅ Repository analysis completed successfully")
            return analysis_result
        else:
            raise HTTPException(status_code=500, detail=analysis_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate-pr")
async def validate_pr(request_data: dict):
    """Validate Pull Request against Jira ticket requirements"""
    try:
        logger.info("🔍 Starting PR validation...")
        
        jira_issue_key = request_data.get('jira_issue_key')
        pr_url = request_data.get('pr_url')
        
        if not jira_issue_key or not pr_url:
            raise HTTPException(status_code=400, detail="jira_issue_key and pr_url are required")
        
        logger.info(f"🎫 Validating PR for issue: {jira_issue_key}")
        logger.info(f"🔗 PR URL: {pr_url}")
        
        # Get Jira issue details
        issue_data = jira_service.get_issue(jira_issue_key)
        if not issue_data:
            raise HTTPException(status_code=404, detail=f"Jira issue {jira_issue_key} not found")
        
        # Analyze PR
        pr_analysis = await analyze_pull_request(pr_url, issue_data)
        
        if pr_analysis.get("success"):
            logger.info("✅ PR validation completed successfully")
            return pr_analysis
        else:
            raise HTTPException(status_code=500, detail=pr_analysis.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PR validation failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PR validation failed: {str(e)}")

@app.post("/api/generate-implementation-plan")
async def generate_implementation_plan(request_data: dict):
    """Generate advanced implementation plan with comprehensive repository analysis"""
    try:
        logger.info("=" * 80)
        logger.info("🚀 ADVANCED IMPLEMENTATION PLAN REQUEST")
        logger.info(f"📦 Request data keys: {list(request_data.keys()) if request_data else 'No data'}")
        
        issue_key = request_data.get('issue_key')
        github_url = request_data.get('github_url')
        
        logger.info(f"🎫 Issue key: {issue_key}")
        logger.info(f"🔗 GitHub URL: '{github_url}'")
        logger.info("=" * 80)
        
        if not issue_key:
            raise HTTPException(status_code=400, detail="issue_key is required")
        
        logger.info(f"🎯 Generating ADVANCED implementation plan for {issue_key}")
        
        # Get issue details from Jira
        issue_data = jira_service.get_issue(issue_key)
        if issue_data is None:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
        
        # Perform advanced repository analysis if GitHub URL provided
        repo_analysis = None
        if github_url:
            logger.info(f"🔍 Performing ADVANCED large repository analysis: {github_url}")
            try:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Repository analysis timed out")
                
                # Set a 90-second timeout for comprehensive repository analysis
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(90)
                
                try:
                    summary = issue_data.get('summary') or ''
                    description = issue_data.get('description') or ''
                    
                    # Use optimized analysis for faster processing
                    repo_analysis = github_analyzer.analyze_repository_optimized(
                        github_url, summary, description
                    )
                    
                    if repo_analysis.get("success"):
                        logger.info(f"✅ Advanced repository analysis complete:")
                        logger.info(f"   - Repository: {repo_analysis.get('repository', {}).get('name', 'Unknown')}")
                        logger.info(f"   - Framework: {repo_analysis.get('insights', {}).get('framework', 'Unknown')}")
                        logger.info(f"   - Files analyzed: {repo_analysis.get('files_analyzed', 0)}")
                        logger.info(f"   - High priority files: {repo_analysis.get('high_priority_files', 0)}")
                        logger.info(f"   - Total repo files: {repo_analysis.get('total_files_in_repo', 0)}")
                    else:
                        logger.warning(f"Repository analysis failed: {repo_analysis.get('error')}")
                        repo_analysis = None
                
                finally:
                    signal.alarm(0)  # Cancel the alarm
                    
            except TimeoutError:
                logger.warning("⏰ Repository analysis timed out - proceeding with basic analysis")
                repo_analysis = None
            except Exception as e:
                logger.error(f"❌ Repository analysis exception: {e}")
                repo_analysis = None
        
        # Generate advanced implementation plan with error handling
        try:
            plan_result = await granite_api.generate_implementation_plan(issue_data, repo_analysis)
        except Exception as e:
            logger.error(f"❌ Implementation plan generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Implementation plan generation failed: {str(e)}")
        
        if plan_result.get("success"):
            response_data = {
                "success": True,
                "issue_key": issue_key,
                "issue_summary": plan_result.get("ticket_summary"),
                "implementation_plan": plan_result.get("implementation_plan"),
                "model_used": plan_result.get("model_used"),
                "generated_at": plan_result.get("generated_at"),
                "context_depth": plan_result.get("context_depth"),
                "repository_analyzed": plan_result.get("repository_analyzed", False),
                "files_analyzed": plan_result.get("files_analyzed", 0),
                "analysis_quality": plan_result.get("analysis_quality", "standard"),
                "ai_powered": True,
                "approach": "Advanced Large Repository Analysis with Deep Context Integration"
            }
            
            # Include comprehensive repository analysis info
            if repo_analysis and repo_analysis.get("success"):
                response_data["repository_info"] = {
                    "name": repo_analysis.get("repository", {}).get("name"),
                    "language": repo_analysis.get("repository", {}).get("language"),
                    "framework": repo_analysis.get("insights", {}).get("framework"),
                    "tech_stack": repo_analysis.get("insights", {}).get("tech_stack", []),
                    "total_files_in_repo": repo_analysis.get("total_files_in_repo", 0),
                    "files_analyzed": repo_analysis.get("files_analyzed", 0),
                    "high_priority_files": repo_analysis.get("high_priority_files", 0),
                    "architecture_type": repo_analysis.get("insights", {}).get("architecture", "unknown"),
                    "styling_approach": repo_analysis.get("insights", {}).get("styling_approach", "unknown"),
                    "entry_points": repo_analysis.get("entry_points", []),
                    "config_files": repo_analysis.get("config_files", []),
                    "top_relevant_files": [
                        f.get('path') for f in repo_analysis.get("analyzed_files", [])[:8]
                    ]
                }
                
                # Add file modification priorities
                priority_breakdown = {}
                for file_info in repo_analysis.get("analyzed_files", []):
                    priority = file_info.get('modification_priority', 'low')
                    if priority not in priority_breakdown:
                        priority_breakdown[priority] = 0
                    priority_breakdown[priority] += 1
                
                response_data["repository_info"]["priority_breakdown"] = priority_breakdown
            
            logger.info(f"✅ Advanced implementation plan generated successfully for {issue_key}")
            return response_data
        else:
            raise HTTPException(status_code=500, detail=plan_result.get("error"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate advanced implementation plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# APPLICATION STARTUP
# ================================

@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("🚀 Starting Ultimate GitHub-Jira AI Assistant v5.0")
    logger.info("🧠 Advanced large repository analysis with intelligent filtering enabled")
    logger.info("⚡ Async processing and smart keyword extraction active")
    logger.info("🎯 Context-aware implementation plans with specific code suggestions")
    logger.info(f"🤖 IBM Granite configured: {bool(API_KEY and PROJECT_ID)}")
    logger.info(f"📋 Jira configured: {bool(hasattr(jira_service, 'headers'))}")
    logger.info(f"🔗 GitHub configured: {bool(GITHUB_TOKEN)}")
    logger.info("✅ Advanced application startup completed")

# ================================
# RUN APPLICATION
# ================================

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def find_available_port(start_port=8004):
        """Find an available port starting from the given port"""
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
        return None
    
    HOST = "0.0.0.0"
    PORT = int(os.getenv('PORT', '8004'))
    
    # Check if port is available, if not find an alternative
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', PORT))
    except OSError:
        logger.warning(f"Port {PORT} is in use, finding alternative...")
        PORT = find_available_port(8004)
        if PORT is None:
            logger.error("No available ports found in range 8004-8104")
            sys.exit(1)
        logger.info(f"Using alternative port: {PORT}")
    
    print("🚀 Ultimate GitHub-Jira AI Assistant - Advanced v5.0")
    print("🧠 Intelligent Large Repository Analysis with Deep Context Integration")
    print("⚡ Features: Async processing, Smart filtering, Code pattern recognition")
    print(f"📡 Server: http://{HOST}:{PORT}")
    print(f"📖 Docs: http://{HOST}:{PORT}/docs")
    print(f"🔍 Health: http://{HOST}:{PORT}/api/health")
    print()
    
    try:
        uvicorn.run(
            "ultimate_main:app",
            host=HOST,
            port=PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)