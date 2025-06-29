#!/usr/bin/env python3
"""
Test Jira Connection - Debug the ticket fetching issue
"""

import os
import base64
import requests
import json
from pathlib import Path

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

def test_jira_connection():
    """Test Jira connection step by step"""
    
    print("🔍 Testing Jira Connection...")
    print("=" * 50)
    
    # Get credentials
    jira_url = os.getenv('JIRA_URL', '').rstrip('/')
    jira_email = os.getenv('JIRA_EMAIL', '')
    jira_token = os.getenv('JIRA_API_TOKEN', '')
    
    print(f"Jira URL: {jira_url}")
    print(f"Jira Email: {jira_email}")
    print(f"Token length: {len(jira_token)}")
    print(f"Token starts with: {jira_token[:10]}..." if jira_token else "No token")
    print()
    
    if not jira_email or not jira_token:
        print("❌ Missing Jira credentials!")
        return False
    
    # Clean up the token (remove any extra characters)
    jira_token = jira_token.strip()
    
    # Create auth headers
    auth_string = f"{jira_email}:{jira_token}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("📋 Testing authentication...")
    try:
        response = requests.get(f"{jira_url}/rest/api/3/myself", headers=headers, timeout=10)
        print(f"Auth test status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Authentication successful!")
            print(f"User: {user_data.get('displayName', 'Unknown')}")
            print(f"Account ID: {user_data.get('accountId', 'Unknown')}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    print("\n📊 Testing projects list...")
    try:
        response = requests.get(f"{jira_url}/rest/api/3/project", headers=headers, timeout=30)
        print(f"Projects test status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} projects:")
            for project in projects[:5]:  # Show first 5
                print(f"  - {project.get('key', 'N/A')}: {project.get('name', 'N/A')}")
            
            if projects:
                # Test fetching issues from first project
                first_project = projects[0]
                project_key = first_project.get('key')
                
                print(f"\n🎫 Testing issues from project {project_key}...")
                
                # Build JQL query
                jql = f"project = {project_key} ORDER BY updated DESC"
                params = {
                    'jql': jql,
                    'maxResults': 10,
                    'fields': 'summary,description,status,assignee,created,issuetype,priority'
                }
                
                response = requests.get(
                    f"{jira_url}/rest/api/3/search",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                
                print(f"Issues test status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get("issues", [])
                    print(f"✅ Found {len(issues)} issues in {project_key}:")
                    
                    for issue in issues[:3]:  # Show first 3
                        print(f"  - {issue.get('key')}: {issue['fields'].get('summary', 'No summary')}")
                else:
                    print(f"❌ Failed to fetch issues: {response.status_code}")
                    print(f"Response: {response.text[:300]}")
                    
                    # Try simpler query
                    print("\n🔄 Trying simpler query...")
                    simple_params = {
                        'jql': f"project = {project_key}",
                        'maxResults': 5
                    }
                    
                    response = requests.get(
                        f"{jira_url}/rest/api/3/search",
                        headers=headers,
                        params=simple_params,
                        timeout=30
                    )
                    
                    print(f"Simple query status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        issues = data.get("issues", [])
                        print(f"✅ Simple query found {len(issues)} issues")
                    else:
                        print(f"❌ Simple query also failed: {response.text[:300]}")
            
        else:
            print(f"❌ Failed to fetch projects: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Projects test error: {e}")
        return False
    
    print("\n✅ Jira connection test completed!")
    return True

if __name__ == "__main__":
    test_jira_connection() 