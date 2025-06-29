# src/services/granite_service.py - Enhanced IBM Granite Implementation
import asyncio
import logging
import json
import aiohttp
import re
import time
from typing import Dict, Any, List, Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

class GraniteService:
    def __init__(self):
        self.api_key = settings.IBM_GRANITE_API_KEY
        self.project_id = getattr(settings, 'IBM_PROJECT_ID', None)
        self.base_url = "https://eu-de.ml.cloud.ibm.com"
        self.generation_endpoint = f"{self.base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
        
        if not self.api_key:
            logger.error("❌ IBM Granite API key missing!")
            raise Exception("IBM Granite configuration is REQUIRED. Please set IBM_GRANITE_API_KEY in .env file")
        
        logger.info("🤖 Enhanced IBM Granite service initialized")
        logger.info(f"📡 Endpoint: {self.generation_endpoint}")
    
    async def get_bearer_token(self) -> str:
        """Get IBM Cloud IAM Bearer token from API key"""
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
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, headers=headers, data=data, timeout=30) as response:
                    logger.info(f"Token request status: {response.status}")
                    
                    if response.status == 200:
                        token_data = await response.json()
                        self.bearer_token = token_data['access_token']
                        expires_in = token_data.get('expires_in', 3600)
                        
                        # Set expiration time (refresh 5 minutes early)
                        self.token_expires_at = time.time() + expires_in - 300
                        
                        logger.info(f"✅ Bearer token generated! Expires in {expires_in//60} minutes")
                        return self.bearer_token
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Error generating Bearer token: {error_text}")
                        raise Exception(f"IBM Cloud authentication failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Exception generating Bearer token: {e}")
            raise Exception(f"IBM Cloud authentication failed: {str(e)}")

    async def generate_text(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.7) -> str:
        """Generate text using IBM Granite Text Generation API"""
        try:
            bearer_token = await self.get_bearer_token()
            if not bearer_token:
                raise Exception("Failed to get Bearer token")
            
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
                "moderations": {
                    "hap": {
                        "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                        "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
                    },
                    "pii": {
                        "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                        "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
                    },
                    "granite_guardian": {"input": {"enabled": False, "threshold": 1}}
                }
            }
            
            # Add project_id if available
            if self.project_id:
                payload["project_id"] = self.project_id
            
            # Add temperature only for sampling mode
            if payload["parameters"]["decoding_method"] == "sample":
                payload["parameters"]["temperature"] = temperature
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generation_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=120
                ) as response:
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        raise Exception(f"IBM Granite API failed: {response.status}")
                        
                    result = await response.json()
                    logger.debug(f"API Response keys: {list(result.keys())}")
                    
                    # Handle text generation API response format
                    if 'results' in result and len(result['results']) > 0:
                        generated_text = result['results'][0].get('generated_text', '')
                        logger.info(f"Generated text length: {len(generated_text)} characters")
                        return generated_text.strip()
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        raise Exception("IBM Granite returned unexpected response format")
                        
        except Exception as e:
            logger.error(f"❌ IBM Granite request failed: {e}")
            raise Exception(f"IBM Granite text generation failed: {str(e)}")

    async def generate_crystal_clear_implementation_plan(self, repo_analysis: Dict, issue_data: Dict, code_files: List[Dict]) -> Dict[str, Any]:
        """Generate crystal clear implementation plan with specific code changes"""
        
        logger.info(f"🚀 Generating crystal clear implementation plan for: {issue_data.get('summary', 'Unknown Issue')}")
        
        # Prepare comprehensive context
        repo_context = self._prepare_repository_context(repo_analysis, code_files)
        code_context = self._format_code_files_for_analysis(code_files)
        
        # Create enhanced prompt for crystal clear implementation
        implementation_prompt = f"""You are an expert software engineer creating a crystal clear implementation plan. 
Analyze the repository and provide SPECIFIC, ACTIONABLE steps with exact code changes.

REPOSITORY ANALYSIS:
{repo_context}

ISSUE TO IMPLEMENT:
Summary: {issue_data.get('summary', '')}
Description: {issue_data.get('description', '')}
Issue Key: {issue_data.get('key', '')}

CODE FILES FOR CONTEXT:
{code_context}

GENERATE A CRYSTAL CLEAR IMPLEMENTATION PLAN:

## EXECUTIVE SUMMARY
[2-3 sentences describing exactly what will be implemented and how]

## TECHNICAL APPROACH
[Describe the technical strategy, architecture patterns to follow, and integration points]

## SPECIFIC FILE CHANGES
[List each file with exact modifications needed]

### File: [exact file path]
**Purpose**: [What this file does and why it needs to change]
**Changes**:
- Line [X]: [Specific change needed]
- Add function: [exact function name and purpose]
- Modify: [exact existing code to change]

### File: [next file path]
**Purpose**: [What this file does]
**Changes**:
- [Specific changes with line numbers when possible]

## IMPLEMENTATION STEPS
1. [First specific step with exact commands/actions]
2. [Second step with detailed instructions]
3. [Continue with precise, executable steps]

## CODE EXAMPLES
[Provide actual code snippets showing before/after or new code to add]

```language
// Exact code to implement
```

## TESTING REQUIREMENTS
[Specific test files to create/modify with exact test scenarios]

## DEPENDENCIES
[List any new packages/libraries needed with exact versions]

## DEPLOYMENT CONSIDERATIONS
[Specific deployment steps or configuration changes needed]

Be extremely specific with file paths, function names, line numbers, and exact code changes. 
Provide implementable, actionable instructions that a developer can follow step-by-step."""

        try:
            # Generate implementation plan using IBM Granite
            granite_response = await self.generate_text(implementation_prompt, max_tokens=2000, temperature=0.2)
            
            # Parse and structure the response
            parsed_plan = self._parse_implementation_response(granite_response)
            
            # Add metadata
            parsed_plan.update({
                "granite_powered": True,
                "analysis_confidence": 0.95,
                "model_used": "ibm/granite-3-8b-instruct",
                "files_analyzed": len(code_files),
                "repository_type": repo_analysis.get('type', 'unknown'),
                "analysis_method": "IBM_GRANITE_ENHANCED",
                "full_granite_response": granite_response
            })
            
            logger.info(f"✅ Crystal clear implementation plan generated - {len(parsed_plan.get('file_changes', []))} file changes identified")
            return parsed_plan
            
        except Exception as e:
            logger.error(f"❌ Implementation plan generation failed: {e}")
            raise Exception(f"IBM Granite implementation plan generation failed: {str(e)}")

    def _prepare_repository_context(self, repo_analysis: Dict, code_files: List[Dict]) -> str:
        """Prepare comprehensive repository context for analysis"""
        context = f"""Repository Type: {repo_analysis.get('type', 'Unknown')}
Technology Stack: {', '.join([str(tech) for tech in repo_analysis.get('tech_stack', [])])}
Primary Languages: {', '.join(list(repo_analysis.get('languages', {}).keys())[:3])}
Architecture Patterns: {', '.join(repo_analysis.get('architecture_patterns', []))}
Complexity Score: {repo_analysis.get('complexity_score', 0)}/100
Total Files: {repo_analysis.get('performance_metrics', {}).get('file_count', 0)}

Key Dependencies:
{self._format_dependencies_concise(repo_analysis.get('dependencies', {}))}

Directory Structure Overview:
{self._format_directory_structure_concise(repo_analysis.get('structure', {}))}

Code Files Available for Analysis:
{self._format_available_files(code_files)}"""
        
        return context

    def _format_code_files_for_analysis(self, code_files: List[Dict]) -> str:
        """Format code files for detailed analysis"""
        if not code_files:
            return "No code files available for analysis"
        
        formatted_files = []
        for file_info in code_files[:5]:  # Limit to 5 most important files
            content = file_info.get('content', '')
            if content:
                # Truncate very long files but keep structure
                lines = content.split('\n')
                if len(lines) > 50:
                    content_preview = '\n'.join(lines[:30]) + '\n... [file continues] ...\n' + '\n'.join(lines[-10:])
                else:
                    content_preview = content
                
                formatted_files.append(f"""
### {file_info.get('name', 'Unknown')} ({file_info.get('path', 'unknown path')})
Size: {file_info.get('lines', 0)} lines | Priority: {file_info.get('priority', 'medium')}

```
{content_preview}
```""")
        
        return '\n'.join(formatted_files)

    def _format_dependencies_concise(self, dependencies: Dict) -> str:
        """Format dependencies in a concise way"""
        if not dependencies:
            return "No dependencies found"
        
        formatted = []
        for dep_type, deps in dependencies.items():
            if deps and isinstance(deps, list):
                formatted.append(f"- {dep_type}: {', '.join(deps[:4])}")
        
        return '\n'.join(formatted) if formatted else "No dependencies found"

    def _format_directory_structure_concise(self, structure: Dict) -> str:
        """Format directory structure in a concise way"""
        if not structure:
            return "No structure information available"
        
        dirs = list(structure.get('directories', {}).keys())[:8]
        files_count = len(structure.get('files', []))
        
        return f"Key Directories: {', '.join(dirs)}\nRoot Files: {files_count} files"

    def _format_available_files(self, code_files: List[Dict]) -> str:
        """Format list of available code files"""
        if not code_files:
            return "No code files analyzed"
        
        file_list = []
        for file_info in code_files:
            file_list.append(f"- {file_info.get('path', 'unknown')}: {file_info.get('lines', 0)} lines ({file_info.get('priority', 'medium')} priority)")
        
        return '\n'.join(file_list)

    def _parse_implementation_response(self, response: str) -> Dict[str, Any]:
        """Parse IBM Granite implementation response into structured format"""
        
        # Extract sections using improved parsing
        sections = {
            "executive_summary": self._extract_section_content(response, "EXECUTIVE SUMMARY"),
            "technical_approach": self._extract_section_content(response, "TECHNICAL APPROACH"),
            "file_changes": self._extract_file_changes(response),
            "implementation_steps": self._extract_implementation_steps_from_response(response),
            "code_examples": self._extract_code_examples(response),
            "testing_requirements": self._extract_section_content(response, "TESTING REQUIREMENTS"),
            "dependencies": self._extract_section_content(response, "DEPENDENCIES"),
            "deployment_considerations": self._extract_section_content(response, "DEPLOYMENT CONSIDERATIONS")
        }
        
        return {
            "crystal_clear_plan": response,
            "executive_summary": sections["executive_summary"] or "Implementation plan generated by IBM Granite",
            "technical_approach": sections["technical_approach"] or "Technical approach analyzed by IBM Granite",
            "file_changes": sections["file_changes"],
            "implementation_steps": sections["implementation_steps"],
            "code_examples": sections["code_examples"],
            "testing_strategy": sections["testing_requirements"] or "Testing strategy by IBM Granite",
            "dependencies": self._extract_dependencies_list(sections["dependencies"]),
            "deployment_strategy": sections["deployment_considerations"] or "Deployment considerations by IBM Granite",
            "detailed_analysis": sections
        }

    def _extract_section_content(self, text: str, section_name: str) -> str:
        """Extract content of a specific section"""
        lines = text.split('\n')
        in_section = False
        content = []
        
        for line in lines:
            # Check for section header
            if section_name.upper() in line.upper() and ('##' in line or line.strip().startswith('#')):
                in_section = True
                continue
            elif in_section:
                # Stop at next section header
                if line.strip().startswith('##') or line.strip().startswith('#'):
                    break
                content.append(line)
        
        return '\n'.join(content).strip()

    def _extract_file_changes(self, response: str) -> List[Dict[str, str]]:
        """Extract file changes from response"""
        file_changes = []
        lines = response.split('\n')
        
        current_file = None
        current_changes = []
        
        for line in lines:
            # Look for file specifications
            if line.startswith('### File:') or 'File:' in line:
                # Save previous file if exists
                if current_file:
                    file_changes.append({
                        "file": current_file,
                        "change": '\n'.join(current_changes)
                    })
                
                # Extract new file path
                current_file = line.replace('### File:', '').replace('File:', '').strip()
                current_changes = []
            elif current_file and line.strip():
                current_changes.append(line)
        
        # Save last file
        if current_file and current_changes:
            file_changes.append({
                "file": current_file,
                "change": '\n'.join(current_changes)
            })
        
        return file_changes

    def _extract_implementation_steps_from_response(self, response: str) -> List[str]:
        """Extract implementation steps from response"""
        lines = response.split('\n')
        steps = []
        in_steps_section = False
        
        for line in lines:
            if "IMPLEMENTATION STEPS" in line.upper():
                in_steps_section = True
                continue
            elif in_steps_section:
                if line.strip().startswith('##'):
                    break
                elif re.match(r'^\d+\.', line.strip()):
                    steps.append(line.strip())
        
        return steps

    def _extract_code_examples(self, response: str) -> List[str]:
        """Extract code examples from response"""
        code_blocks = re.findall(r'```(?:\w+)?\n?(.*?)```', response, re.DOTALL)
        return [block.strip() for block in code_blocks if block.strip()]

    def _extract_dependencies_list(self, dependencies_text: str) -> List[str]:
        """Extract dependencies as a list"""
        if not dependencies_text:
            return []
        
        deps = []
        for line in dependencies_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                deps.append(line)
        
        return deps

    # Main interface method for compatibility
    async def generate_implementation_plan(self, repo_analysis: Dict, issue_data: Dict, code_files: List[Dict]) -> Dict[str, Any]:
        """Generate implementation plan using IBM Granite - Main interface method"""
        
        logger.info("🤖 IBM Granite implementation plan generation starting")
        
        granite_analysis = await self.generate_crystal_clear_implementation_plan(
            repo_analysis,
            issue_data,
            code_files
        )
        
        # Format for main application compatibility
        return {
            "crystal_clear_plan": granite_analysis["crystal_clear_plan"],
            "file_analyses": [{"analysis": granite_analysis["technical_approach"], "granite_powered": True}],
            "repository_insights": granite_analysis["detailed_analysis"],
            "implementation_confidence": granite_analysis.get("analysis_confidence", 0.95),
            "estimated_complexity": self._estimate_complexity_from_analysis(granite_analysis),
            "detailed_file_changes": granite_analysis["file_changes"],
            "code_examples": granite_analysis["code_examples"],
            "testing_requirements": [granite_analysis["testing_strategy"]]
        }

    def _estimate_complexity_from_analysis(self, analysis: Dict) -> str:
        """Estimate complexity from analysis results"""
        file_changes = len(analysis.get("file_changes", []))
        plan_text = analysis.get("crystal_clear_plan", "").lower()
        
        # Check for complexity indicators
        high_complexity_indicators = ['complex', 'architecture', 'refactor', 'database', 'migration', 'api changes']
        medium_complexity_indicators = ['moderate', 'multiple files', 'integration', 'testing']
        
        high_score = sum(1 for indicator in high_complexity_indicators if indicator in plan_text)
        medium_score = sum(1 for indicator in medium_complexity_indicators if indicator in plan_text)
        
        if file_changes > 5 or high_score > 2:
            return 'high'
        elif file_changes > 2 or medium_score > 1 or high_score > 0:
            return 'medium'
        else:
            return 'low'

    # Legacy compatibility method
    async def analyze_code_file(self, file_path: str, file_content: str, issue_context: str) -> Dict[str, Any]:
        """Analyze single file using IBM Granite"""
        prompt = f"""Analyze this code file for the given issue context.

FILE: {file_path}
ISSUE: {issue_context}

CODE:
```
{file_content[:2000]}
```

Provide specific analysis:
1. File purpose and functionality
2. How it relates to the issue
3. Exact changes needed
4. Dependencies that might be affected

Be specific and actionable."""

        analysis = await self.generate_text(prompt, max_tokens=800, temperature=0.2)
        return {
            "file_path": file_path,
            "analysis": analysis,
            "granite_powered": True,
            "confidence_score": 0.95
        }