from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class JiraStory(BaseModel):
    key: str
    summary: str
    description: str
    acceptance_criteria: List[str]
    story_points: Optional[int]
    assignee: Optional[str]
    status: str
    created: datetime
    updated: datetime

class RepoInfo(BaseModel):
    name: str
    url: str
    main_language: str
    structure: Dict[str, List[str]]  # directory -> files
    readme_content: Optional[str]
    tech_stack: List[str]

class ImplementationPlan(BaseModel):
    jira_key: str
    title: str
    executive_summary: str
    technical_approach: str
    file_changes: List[Dict[str, str]]  # file -> description
    dependencies: List[str]
    testing_strategy: str
    estimated_hours: int
    risk_assessment: List[str]
    generated_at: datetime

class ValidationStatus(str, Enum):
    VALID = "valid"
    NEEDS_IMPROVEMENT = "needs_improvement"
    INVALID = "invalid"

class PRAnalysis(BaseModel):
    pr_url: str
    jira_key: str
    validation_status: ValidationStatus
    completeness_score: float  # 0-100
    matches_requirements: Dict[str, bool]
    missing_requirements: List[str]
    suggestions: List[str]
    improved_code: Optional[str]
    feedback: str
    analyzed_at: datetime 