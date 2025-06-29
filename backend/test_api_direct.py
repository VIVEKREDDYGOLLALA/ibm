#!/usr/bin/env python3
"""
Direct API Test - Test the implementation plan generation endpoint
"""

import requests
import json

def test_implementation_plan_api():
    """Test the implementation plan generation API directly"""
    
    print("🧪 Testing Implementation Plan API Directly")
    print("=" * 50)
    
    # Backend URL - adjust port if needed
    backend_url = "http://127.0.0.1:8003"
    
    # Test health first
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        print(f"   Health status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Backend is healthy")
            print(f"   Services: {list(health_data.get('services', {}).keys())}")
        else:
            print(f"   ❌ Health check failed")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to backend: {e}")
        return
    
    # Test implementation plan generation
    print("\n2. Testing implementation plan generation...")
    
    # Test data - using one of your actual Jira tickets
    test_data = {
        "issue_key": "SCRUM-2",  # Your actual ticket about color palette
        "github_repo_url": "https://github.com/facebook/react"  # Example repo
    }
    
    try:
        print(f"   Sending request: {test_data}")
        response = requests.post(
            f"{backend_url}/api/generate-implementation-plan",
            json=test_data,
            timeout=60  # Allow time for AI generation
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Implementation plan generated successfully!")
            print("\n   📋 Response structure:")
            for key in result.keys():
                print(f"     - {key}: {type(result[key])}")
            
            # Show the actual plan
            if 'implementation_plan' in result:
                plan = result['implementation_plan']
                print(f"\n   📝 Plan preview (first 300 chars):")
                print(f"     {plan[:300]}...")
            elif 'analysis' in result:
                plan = result['analysis']
                print(f"\n   📝 Analysis preview (first 300 chars):")
                print(f"     {plan[:300]}...")
            else:
                print("   ⚠️ No implementation plan found in response")
                
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text}")
                
    except Exception as e:
        print(f"   ❌ API test failed: {e}")

def test_jira_projects():
    """Test Jira projects endpoint"""
    
    print("\n3. Testing Jira projects endpoint...")
    backend_url = "http://127.0.0.1:8003"
    
    try:
        response = requests.get(f"{backend_url}/api/jira/projects", timeout=30)
        print(f"   Projects status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            print(f"   ✅ Found {len(projects)} projects")
            for project in projects[:2]:
                print(f"     - {project.get('key')}: {project.get('name')}")
        else:
            print(f"   ❌ Projects call failed")
            
    except Exception as e:
        print(f"   ❌ Projects test failed: {e}")

def test_jira_issues():
    """Test Jira issues endpoint"""
    
    print("\n4. Testing Jira issues endpoint...")
    backend_url = "http://127.0.0.1:8003"
    
    try:
        # Use the SCRUM project
        response = requests.get(f"{backend_url}/api/jira/issues?project_key=SCRUM", timeout=30)
        print(f"   Issues status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            print(f"   ✅ Found {len(issues)} issues")
            for issue in issues[:2]:
                print(f"     - {issue.get('key')}: {issue.get('fields', {}).get('summary', 'No summary')[:50]}...")
        else:
            print(f"   ❌ Issues call failed")
            
    except Exception as e:
        print(f"   ❌ Issues test failed: {e}")

if __name__ == "__main__":
    print("🚀 Direct API Testing for Implementation Plan Generation")
    print("🔧 Make sure your backend is running on port 8003")
    print("=" * 60)
    
    test_implementation_plan_api()
    test_jira_projects()
    test_jira_issues()
    
    print("\n" + "=" * 60)
    print("✅ API testing completed!")
    print("\nIf the implementation plan generation worked, the frontend should now display it correctly.") 