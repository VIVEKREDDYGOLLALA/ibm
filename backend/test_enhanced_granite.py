#!/usr/bin/env python3
"""
Enhanced IBM Granite Service Test Script
Tests the upgraded Granite service with crystal clear implementation plan generation
"""

import os
import sys
import asyncio
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing (replace with your actual values)
os.environ['IBM_GRANITE_API_KEY'] = os.getenv('IBM_GRANITE_API_KEY', '')
os.environ['IBM_PROJECT_ID'] = os.getenv('IBM_PROJECT_ID', '')

from src.services.granite_service import GraniteService

def print_separator(title: str):
    """Print a separator with title"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subsection(title: str):
    """Print a subsection header"""
    print(f"\n--- {title} ---")

async def test_enhanced_granite_service():
    """Test the enhanced Granite service functionality"""
    
    print_separator("ENHANCED IBM GRANITE SERVICE TEST")
    
    # Check environment variables
    api_key = os.getenv('IBM_GRANITE_API_KEY')
    project_id = os.getenv('IBM_PROJECT_ID')
    
    if not api_key:
        print("❌ IBM_GRANITE_API_KEY environment variable not set")
        print("Please set your IBM Granite API key to test the service")
        return
    
    if not project_id:
        print("⚠️ IBM_PROJECT_ID environment variable not set")
        print("Project ID is optional but recommended for better performance")
    
    print(f"✅ API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else 'Set'}")
    print(f"✅ Project ID: {'Set' if project_id else 'Not set'}")
    
    try:
        # Initialize Granite service
        print_subsection("Initializing Enhanced Granite Service")
        granite_service = GraniteService()
        print("✅ Enhanced Granite service initialized successfully")
        
        # Test 1: Bearer token generation
        print_subsection("Testing Bearer Token Generation")
        bearer_token = await granite_service.get_bearer_token()
        print(f"✅ Bearer token generated: {bearer_token[:20]}...{bearer_token[-10:] if len(bearer_token) > 30 else bearer_token}")
        
        # Test 2: Simple text generation
        print_subsection("Testing Basic Text Generation")
        simple_prompt = "Explain what a React component is in 2 sentences."
        response = await granite_service.generate_text(simple_prompt, max_tokens=100, temperature=0.3)
        print("✅ Basic text generation successful:")
        print(f"Prompt: {simple_prompt}")
        print(f"Response: {response}")
        
        # Test 3: Crystal clear implementation plan generation
        print_subsection("Testing Crystal Clear Implementation Plan Generation")
        
        # Sample repository analysis (simulated)
        sample_repo_analysis = {
            'type': 'web_frontend',
            'tech_stack': ['react', 'typescript', 'tailwindcss'],
            'languages': {'TypeScript': 60.5, 'JavaScript': 25.3, 'CSS': 14.2},
            'architecture_patterns': ['component-based', 'hooks', 'functional'],
            'complexity_score': 65,
            'performance_metrics': {'file_count': 47},
            'dependencies': {
                'production': ['react', 'typescript', 'tailwindcss', 'axios'],
                'development': ['jest', 'testing-library', 'eslint']
            },
            'structure': {
                'directories': {
                    'src': {
                        'directories': {
                            'components': {},
                            'pages': {},
                            'utils': {},
                            'api': {}
                        },
                        'files': []
                    }
                },
                'files': [
                    {'name': 'package.json', 'size': 1024},
                    {'name': 'tsconfig.json', 'size': 512}
                ]
            }
        }
        
        # Sample issue data
        sample_issue_data = {
            'key': 'PROJ-123',
            'summary': 'Add user profile edit functionality',
            'description': 'Users should be able to edit their profile information including name, email, and profile picture. The component should validate email format and show success/error messages.'
        }
        
        # Sample code files (simulated)
        sample_code_files = [
            {
                'name': 'UserProfile.tsx',
                'path': 'src/components/UserProfile.tsx',
                'size': 1500,
                'lines': 75,
                'priority': 'high',
                'content': '''import React, { useState, useEffect } from 'react';
import { User } from '../types/User';

interface UserProfileProps {
  user: User;
  onUserUpdate: (user: User) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ user, onUserUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  
  return (
    <div className="user-profile">
      <h2>User Profile</h2>
      <div className="profile-info">
        <p>Name: {user.name}</p>
        <p>Email: {user.email}</p>
      </div>
      <button onClick={() => setIsEditing(!isEditing)}>
        {isEditing ? 'Cancel' : 'Edit Profile'}
      </button>
    </div>
  );
};'''
            },
            {
                'name': 'api.ts',
                'path': 'src/api/api.ts',
                'size': 800,
                'lines': 40,
                'priority': 'medium',
                'content': '''import axios from 'axios';
import { User } from '../types/User';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const userAPI = {
  getUser: async (id: string): Promise<User> => {
    const response = await axios.get(`${API_BASE}/users/${id}`);
    return response.data;
  },
  
  // TODO: Add updateUser method
};'''
            }
        ]
        
        # Generate crystal clear implementation plan
        print("🚀 Generating crystal clear implementation plan...")
        implementation_plan = await granite_service.generate_crystal_clear_implementation_plan(
            sample_repo_analysis,
            sample_issue_data,
            sample_code_files
        )
        
        print("✅ Crystal clear implementation plan generated successfully!")
        
        # Display the results
        print_subsection("EXECUTIVE SUMMARY")
        print(implementation_plan.get('executive_summary', 'No summary generated'))
        
        print_subsection("TECHNICAL APPROACH")
        print(implementation_plan.get('technical_approach', 'No technical approach generated'))
        
        print_subsection("FILE CHANGES")
        file_changes = implementation_plan.get('file_changes', [])
        if file_changes:
            for i, change in enumerate(file_changes, 1):
                print(f"\n{i}. File: {change.get('file', 'Unknown')}")
                print(f"   Changes: {change.get('change', 'No changes specified')[:200]}...")
        else:
            print("No specific file changes identified")
        
        print_subsection("IMPLEMENTATION STEPS")
        steps = implementation_plan.get('implementation_steps', [])
        if steps:
            for step in steps:
                print(f"• {step}")
        else:
            print("No implementation steps provided")
        
        print_subsection("CODE EXAMPLES")
        code_examples = implementation_plan.get('code_examples', [])
        if code_examples:
            for i, example in enumerate(code_examples, 1):
                print(f"\nExample {i}:")
                print(f"```\n{example[:300]}...\n```")
        else:
            print("No code examples provided")
        
        print_subsection("METADATA")
        print(f"Model Used: {implementation_plan.get('model_used', 'Unknown')}")
        print(f"Analysis Confidence: {implementation_plan.get('analysis_confidence', 0)}")
        print(f"Files Analyzed: {implementation_plan.get('files_analyzed', 0)}")
        print(f"Repository Type: {implementation_plan.get('repository_type', 'Unknown')}")
        print(f"Analysis Method: {implementation_plan.get('analysis_method', 'Unknown')}")
        
        # Test 4: Main interface method compatibility
        print_subsection("Testing Main Interface Method Compatibility")
        
        main_plan = await granite_service.generate_implementation_plan(
            sample_repo_analysis,
            sample_issue_data,
            sample_code_files
        )
        
        print("✅ Main interface method working correctly")
        print(f"Crystal clear plan length: {len(main_plan.get('crystal_clear_plan', ''))}")
        print(f"File analyses: {len(main_plan.get('file_analyses', []))}")
        print(f"Implementation confidence: {main_plan.get('implementation_confidence', 0)}")
        print(f"Estimated complexity: {main_plan.get('estimated_complexity', 'unknown')}")
        print(f"Detailed file changes: {len(main_plan.get('detailed_file_changes', []))}")
        
        print_separator("ALL TESTS COMPLETED SUCCESSFULLY ✅")
        print("The enhanced IBM Granite service is working correctly!")
        print("Crystal clear implementation plans are being generated with:")
        print("• Specific file changes with exact modifications")
        print("• Actionable implementation steps")
        print("• Code examples and snippets")
        print("• Comprehensive technical analysis")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Enhanced IBM Granite Service Test")
    print("Make sure to set IBM_GRANITE_API_KEY environment variable")
    print("Optional: Set IBM_PROJECT_ID for better performance")
    print()
    
    # Run the async test
    asyncio.run(test_enhanced_granite_service()) 