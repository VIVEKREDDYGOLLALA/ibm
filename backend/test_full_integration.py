#!/usr/bin/env python3
"""
Test Full Integration - Verify Jira + IBM Granite + Frontend Integration
"""

import os
import sys
import base64
import requests
import json
from pathlib import Path

def load_environment():
    """Load environment variables from .env file with proper token handling"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        env_vars = {}
        current_key = None
        current_value = ""
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line and not line.startswith(' '):
                    # Save previous key-value if exists
                    if current_key:
                        env_vars[current_key] = current_value.strip()
                    
                    # Start new key-value
                    key, value = line.split('=', 1)
                    current_key = key.strip()
                    current_value = value.strip()
                else:
                    # Continuation of previous value (for multi-line tokens)
                    if current_key:
                        current_value += line
        
        # Save last key-value
        if current_key:
            env_vars[current_key] = current_value.strip()
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
            
        print(f"✅ Loaded {len(env_vars)} environment variables")
        return env_vars

def test_jira_connection():
    """Test Jira connection with improved token handling"""
    
    print("\n🔍 Testing Jira Connection...")
    print("=" * 50)
    
    # Get credentials
    jira_url = os.getenv('JIRA_URL', '').rstrip('/')
    jira_email = os.getenv('JIRA_EMAIL', '')
    jira_token = os.getenv('JIRA_API_TOKEN', '').strip()  # Strip any whitespace
    
    print(f"Jira URL: {jira_url}")
    print(f"Jira Email: {jira_email}")
    print(f"Token length: {len(jira_token)}")
    print(f"Token preview: {jira_token[:15]}...{jira_token[-10:]}" if len(jira_token) > 25 else f"Token: {jira_token}")
    print()
    
    if not jira_email or not jira_token:
        print("❌ Missing Jira credentials!")
        return False, None
    
    # Create auth headers (exact same as working simple_test.py)
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
            print(f"Email: {user_data.get('emailAddress', 'Unknown')}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False, None
    
    print("\n📊 Testing projects list...")
    try:
        response = requests.get(f"{jira_url}/rest/api/3/project", headers=headers, timeout=30)
        print(f"Projects test status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} projects:")
            for project in projects[:3]:  # Show first 3
                print(f"  - {project.get('key', 'N/A')}: {project.get('name', 'N/A')}")
            
            if projects:
                # Test with first project
                first_project = projects[0]
                project_key = first_project.get('key')
                
                print(f"\n🎫 Testing issues from project {project_key}...")
                
                # Simple JQL query
                params = {
                    'jql': f'project = {project_key}',
                    'maxResults': 5,
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
                    print(f"✅ Found {len(issues)} issues in {project_key}")
                    
                    if issues:
                        print("📋 Sample issues:")
                        for issue in issues[:2]:
                            print(f"  - {issue.get('key')}: {issue['fields'].get('summary', 'No summary')[:50]}...")
                        
                        return True, {
                            'projects': projects,
                            'sample_issues': issues,
                            'headers': headers,
                            'url': jira_url
                        }
                else:
                    print(f"❌ Failed to fetch issues: {response.status_code}")
                    print(f"Response: {response.text[:300]}")
            
        else:
            print(f"❌ Failed to fetch projects: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Projects test error: {e}")
        return False, None
    
    return True, None

def test_granite_connection():
    """Test IBM Granite connection"""
    
    print("\n🤖 Testing IBM Granite Connection...")
    print("=" * 50)
    
    api_key = os.getenv('IBM_GRANITE_API_KEY', '').strip()
    project_id = os.getenv('IBM_PROJECT_ID', '').strip()
    
    print(f"API Key length: {len(api_key)}")
    print(f"Project ID: {project_id}")
    
    if not api_key or not project_id:
        print("❌ Missing IBM Granite credentials!")
        return False
    
    # Test token generation
    print("\n🔑 Testing token generation...")
    token_url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    data = {
        'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
        'apikey': api_key
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
        print(f"Token generation status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            bearer_token = token_data['access_token']
            print(f"✅ Bearer token generated successfully!")
            print(f"Token preview: {bearer_token[:20]}...")
            
            # Test simple text generation
            print("\n📝 Testing text generation...")
            generation_endpoint = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
            
            gen_headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                "input": "Hello, this is a test.",
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": 20,
                    "min_new_tokens": 0,
                    "stop_sequences": [],
                    "repetition_penalty": 1
                },
                "model_id": "ibm/granite-3-8b-instruct",
                "project_id": project_id
            }
            
            response = requests.post(generation_endpoint, headers=gen_headers, json=payload, timeout=60)
            print(f"Text generation status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    generated_text = result['results'][0].get('generated_text', '')
                    print(f"✅ Text generation successful!")
                    print(f"Generated: {generated_text[:100]}...")
                    return True
                else:
                    print(f"❌ Unexpected response format: {result}")
            else:
                print(f"❌ Text generation failed: {response.text[:200]}")
        else:
            print(f"❌ Token generation failed: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Granite test error: {e}")
    
    return False

def test_backend_endpoints():
    """Test if the backend is running and responding"""
    
    print("\n🌐 Testing Backend Endpoints...")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8002"
    
    # Test health endpoint
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        print(f"Health endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is running!")
            print(f"Services status:")
            services = health_data.get('services', {})
            for service, status in services.items():
                status_text = status.get('status', 'unknown')
                print(f"  - {service}: {status_text}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running or not accessible on port 8002")
    except Exception as e:
        print(f"❌ Backend test error: {e}")
    
    return False

def test_frontend_config():
    """Test frontend configuration"""
    
    print("\n🎨 Testing Frontend Configuration...")
    print("=" * 50)
    
    # Check if frontend files exist
    frontend_path = Path(__file__).parent.parent / 'frontend'
    if frontend_path.exists():
        print(f"✅ Frontend directory found: {frontend_path}")
        
        # Check package.json
        package_json = frontend_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                proxy = package_data.get('proxy', 'Not set')
                print(f"Frontend proxy: {proxy}")
                
                if proxy == "http://localhost:8000":
                    print("⚠️ Frontend proxy points to port 8000, but backend runs on 8002")
                    print("   Fix: Update package.json proxy to 'http://localhost:8002'")
                elif proxy == "http://localhost:8002":
                    print("✅ Frontend proxy correctly configured for port 8002")
        
        # Check API configuration
        api_file = frontend_path / 'src' / 'api' / 'api.js'
        if api_file.exists():
            with open(api_file, 'r') as f:
                api_content = f.read()
                if 'http://127.0.0.1:8002' in api_content:
                    print("✅ Frontend API base URL correctly configured")
                elif 'http://127.0.0.1:8000' in api_content:
                    print("⚠️ Frontend API base URL points to port 8000")
                else:
                    print("? Frontend API base URL configuration unclear")
    else:
        print("❌ Frontend directory not found")

def main():
    """Main test function"""
    print("🚀 Full Integration Test - GitHub-Jira AI Assistant")
    print("=" * 60)
    
    # Load environment
    env_vars = load_environment()
    
    # Test each component
    tests = [
        ("Jira Connection", test_jira_connection),
        ("IBM Granite Connection", test_granite_connection),
        ("Backend Endpoints", test_backend_endpoints),
        ("Frontend Configuration", test_frontend_config)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "Jira Connection":
                result, data = test_func()
                results[test_name] = result
                if result and data:
                    results['jira_data'] = data
            else:
                result = test_func()
                results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name in ["Jira Connection", "IBM Granite Connection", "Backend Endpoints", "Frontend Configuration"]:
        status = "✅ PASS" if results.get(test_name) else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    if all(results.get(test, False) for test in ["Jira Connection", "IBM Granite Connection"]):
        print("\n🎉 Core services are working! You can now:")
        print("   1. Start the backend: python3 ultimate_main.py")
        print("   2. Start the frontend: cd frontend && npm start")
        print("   3. Access the app at http://localhost:3000")
    else:
        print("\n🔧 Some services need attention. Check the errors above.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 