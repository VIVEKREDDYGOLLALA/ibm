#!/usr/bin/env python3
# basic_jira_test.py - Test basic Jira connectivity

import requests
import base64
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Jira configuration
JIRA_URL = os.getenv("JIRA_URL", "https://iiitdm-team.atlassian.net/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "cs22b1097@iiitdm.ac.in")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

def create_auth_header():
    """Create basic auth header for Jira"""
    auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    return f"Basic {auth_b64}"

def test_jira_connection():
    """Test basic Jira connection with multiple endpoints"""
    
    print("🔍 Testing Jira Connection")
    print("=" * 50)
    print(f"JIRA URL: {JIRA_URL}")
    print(f"JIRA EMAIL: {JIRA_EMAIL}")
    print(f"API TOKEN: {'Set' if JIRA_API_TOKEN else 'Not Set'}")
    print("=" * 50)
    
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        print("❌ Missing Jira configuration!")
        return False
    
    # Create headers
    headers = {
        'Authorization': create_auth_header(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test endpoints
    test_endpoints = [
        {
            'name': 'Server Info',
            'url': f"{JIRA_URL}rest/api/3/serverInfo",
            'method': 'GET'
        },
        {
            'name': 'Current User',
            'url': f"{JIRA_URL}rest/api/3/myself",
            'method': 'GET'
        },
        {
            'name': 'Projects',
            'url': f"{JIRA_URL}rest/api/3/project",
            'method': 'GET'
        },
        {
            'name': 'Agile Boards',
            'url': f"{JIRA_URL}rest/agile/1.0/board",
            'method': 'GET'
        },
        {
            'name': 'Issues (JQL)',
            'url': f"{JIRA_URL}rest/api/3/search?jql=project=ibm",
            'method': 'GET'
        }
    ]
    
    results = []
    
    for test in test_endpoints:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = requests.request(
                method=test['method'],
                url=test['url'],
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ SUCCESS - Status: {response.status_code}")
                data = response.json()
                
                # Show relevant info for each endpoint
                if test['name'] == 'Server Info':
                    print(f"   Server: {data.get('serverTitle', 'Unknown')}")
                    print(f"   Version: {data.get('version', 'Unknown')}")
                
                elif test['name'] == 'Current User':
                    print(f"   User: {data.get('displayName', 'Unknown')}")
                    print(f"   Email: {data.get('emailAddress', 'Unknown')}")
                
                elif test['name'] == 'Projects':
                    projects = data if isinstance(data, list) else data.get('values', [])
                    print(f"   Projects found: {len(projects)}")
                    for project in projects[:3]:  # Show first 3
                        print(f"     - {project.get('key', 'Unknown')}: {project.get('name', 'Unknown')}")
                
                elif test['name'] == 'Agile Boards':
                    boards = data.get('values', [])
                    print(f"   Boards found: {len(boards)}")
                    for board in boards[:3]:  # Show first 3
                        print(f"     - {board.get('name', 'Unknown')} (ID: {board.get('id', 'Unknown')})")
                
                elif test['name'] == 'Issues (JQL)':
                    issues = data.get('issues', [])
                    print(f"   Issues found: {len(issues)}")
                    for issue in issues[:3]:  # Show first 3
                        fields = issue.get('fields', {})
                        print(f"     - {issue.get('key', 'Unknown')}: {fields.get('summary', 'No summary')}")
                
                results.append({"test": test['name'], "status": "success", "data": data})
                
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                results.append({"test": test['name'], "status": "failed", "error": response.text})
                
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR - Cannot reach Jira server")
            results.append({"test": test['name'], "status": "connection_error"})
            
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT - Server not responding")
            results.append({"test": test['name'], "status": "timeout"})
            
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            results.append({"test": test['name'], "status": "error", "error": str(e)})
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 SUMMARY")
    print(f"{'='*50}")
    
    success_count = len([r for r in results if r['status'] == 'success'])
    total_count = len(results)
    
    print(f"Tests passed: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All tests passed! Jira connection is working perfectly.")
        return True
    elif success_count > 0:
        print("⚠️  Some tests passed. Partial connectivity.")
        return True
    else:
        print("💀 All tests failed. Check your configuration.")
        return False

def test_specific_ticket():
    """Test getting SCRUM-1 ticket specifically"""
    print(f"\n{'='*50}")
    print("🎫 Testing Specific Ticket: SCRUM-1")
    print(f"{'='*50}")
    
    headers = {
        'Authorization': create_auth_header(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Get specific issue
    url = f"{JIRA_URL}rest/api/3/issue/SCRUM-1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully retrieved SCRUM-1")
            data = response.json()
            fields = data.get('fields', {})
            
            print(f"Key: {data.get('key', 'Unknown')}")
            print(f"Summary: {fields.get('summary', 'No summary')}")
            print(f"Status: {fields.get('status', {}).get('name', 'Unknown')}")
            print(f"Issue Type: {fields.get('issuetype', {}).get('name', 'Unknown')}")
            print(f"Priority: {fields.get('priority', {}).get('name', 'Unknown')}")
            print(f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}")
            
            description = fields.get('description', '')
            if description:
                print(f"Description: {str(description)[:100]}...")
            
            return True
        else:
            print(f"❌ Failed to get SCRUM-1: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting SCRUM-1: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Jira Connection Tests")
    
    # Test basic connection
    basic_success = test_jira_connection()
    
    # Test specific ticket if basic connection works
    if basic_success:
        test_specific_ticket()
    
    print(f"\n{'='*50}")
    print("🏁 Testing Complete!")
    print(f"{'='*50}")