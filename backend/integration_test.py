#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Comprehensive test to verify that the backend provides exactly what the frontend expects
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"  # Default React dev server

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_backend_health():
    """Test if backend is running and healthy"""
    print_header("BACKEND HEALTH CHECK")
    
    try:
        # Test basic endpoint
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend server running: {data.get('message')}")
            print_info(f"   Jira configured: {data.get('jira_configured')}")
        else:
            print_error(f"Backend health failed: {response.status_code}")
            return False
            
        # Test detailed health
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print_success("Backend health endpoint working")
            print_info(f"   Status: {health.get('status')}")
            
            jira_service = health.get('services', {}).get('jira', {})
            print_info(f"   Jira Status: {jira_service.get('status', 'unknown')}")
            print_info(f"   Jira URL: {health.get('configuration', {}).get('jira_url', 'Not set')}")
            
            if jira_service.get('status') == 'error':
                print_error(f"   Jira Error: {jira_service.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print_error(f"Backend connection failed: {e}")
        return False

def test_frontend_expected_endpoints():
    """Test all endpoints that the frontend expects"""
    print_header("FRONTEND EXPECTED ENDPOINTS")
    
    endpoints_passed = 0
    total_endpoints = 3
    
    # Test 1: Projects endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/api/jira/projects", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/jira/projects - Working")
            print_info(f"   Projects found: {data.get('count', 0)}")
            if data.get('projects'):
                for project in data['projects'][:2]:  # Show first 2
                    print_info(f"   - {project.get('key')}: {project.get('name')}")
            endpoints_passed += 1
        else:
            print_error(f"GET /api/jira/projects - Failed ({response.status_code})")
    except Exception as e:
        print_error(f"GET /api/jira/projects - Error: {e}")
    
    # Test 2: Issues endpoint
    try:
        response = requests.get(f"{BACKEND_URL}/api/jira/issues?project_key=SCRUM", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/jira/issues - Working")
            print_info(f"   Issues found: {data.get('count', 0)}")
            print_info(f"   Project: {data.get('project_key')}")
            
            # Verify data structure matches frontend expectations
            issues = data.get('issues', [])
            if issues:
                issue = issues[0]
                required_fields = ['key', 'fields']
                missing_fields = [field for field in required_fields if field not in issue]
                
                if not missing_fields:
                    print_success("   Data structure matches frontend expectations")
                    
                    # Check nested fields structure
                    fields = issue.get('fields', {})
                    nested_checks = {
                        'summary': fields.get('summary'),
                        'status.name': fields.get('status', {}).get('name') if fields.get('status') else None,
                        'assignee': fields.get('assignee')
                    }
                    
                    for field_path, value in nested_checks.items():
                        if value is not None:
                            print_success(f"   ✓ {field_path}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                        else:
                            print_info(f"   ○ {field_path}: None/Empty")
                    
                    endpoints_passed += 1
                else:
                    print_error(f"   Missing required fields: {missing_fields}")
            else:
                print_info("   No issues found to verify structure")
                endpoints_passed += 1  # Still counts as working
        else:
            print_error(f"GET /api/jira/issues - Failed ({response.status_code})")
            try:
                error_data = response.json()
                print_error(f"   Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
    except Exception as e:
        print_error(f"GET /api/jira/issues - Error: {e}")
    
    # Test 3: Health endpoint (detailed)
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print_success("GET /api/health - Working")
            endpoints_passed += 1
        else:
            print_error(f"GET /api/health - Failed ({response.status_code})")
    except Exception as e:
        print_error(f"GET /api/health - Error: {e}")
    
    print_info(f"\nEndpoints Status: {endpoints_passed}/{total_endpoints} working")
    return endpoints_passed == total_endpoints

def test_implementation_plan_endpoints():
    """Test implementation plan generation endpoints"""
    print_header("IMPLEMENTATION PLAN ENDPOINTS")
    
    endpoints_passed = 0
    total_endpoints = 3
    
    # Test 1: Generate Implementation Plan
    try:
        test_data = {
            "jira_issue_key": "SCRUM-1",
            "github_repo_url": "https://github.com/test/repo"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/generate-implementation-plan", 
                               json=test_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print_success("POST /api/generate-implementation-plan - Working")
            
            # Check response structure
            required_fields = ['plan', 'pdf_url', 'jira_issue_key']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print_success("   Response structure correct")
                plan = data.get('plan', {})
                if 'executive_summary' in plan and 'estimated_hours' in plan:
                    print_success("   Plan structure correct")
                    print_info(f"   Issue: {data.get('jira_issue_key')}")
                    print_info(f"   Hours: {plan.get('estimated_hours')}")
                    endpoints_passed += 1
                else:
                    print_error("   Plan structure incomplete")
            else:
                print_error(f"   Missing fields: {missing_fields}")
        else:
            print_error(f"POST /api/generate-implementation-plan - Failed ({response.status_code})")
            try:
                error_data = response.json()
                print_error(f"   Detail: {error_data.get('detail')}")
            except:
                pass
    except Exception as e:
        print_error(f"POST /api/generate-implementation-plan - Error: {e}")
    
    # Test 2: PR Validation
    try:
        test_data = {
            "jira_issue_key": "SCRUM-1",
            "pr_url": "https://github.com/test/repo/pull/123"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/validate-pr", 
                               json=test_data, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print_success("POST /api/validate-pr - Working")
            
            if 'analysis' in data:
                analysis = data['analysis']
                if 'score' in analysis and 'recommendations' in analysis:
                    print_success("   Analysis structure correct")
                    print_info(f"   Score: {analysis.get('score')}")
                    endpoints_passed += 1
                else:
                    print_error("   Analysis structure incomplete")
            else:
                print_error("   Missing analysis field")
        else:
            print_error(f"POST /api/validate-pr - Failed ({response.status_code})")
    except Exception as e:
        print_error(f"POST /api/validate-pr - Error: {e}")
    
    # Test 3: PDF Download
    try:
        response = requests.get(f"{BACKEND_URL}/api/download-pdf/test.pdf", timeout=10)
        if response.status_code == 200:
            print_success("GET /api/download-pdf - Working")
            print_info(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            endpoints_passed += 1
        else:
            print_error(f"GET /api/download-pdf - Failed ({response.status_code})")
    except Exception as e:
        print_error(f"GET /api/download-pdf - Error: {e}")
    
    print_info(f"\nImplementation Plan Endpoints: {endpoints_passed}/{total_endpoints} working")
    return endpoints_passed == total_endpoints

def test_cors_headers():
    """Test CORS headers for frontend integration"""
    print_header("CORS CONFIGURATION")
    
    try:
        # Test preflight request
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{BACKEND_URL}/api/jira/issues", headers=headers, timeout=5)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        if cors_headers['Access-Control-Allow-Origin']:
            print_success("CORS headers present")
            for header, value in cors_headers.items():
                if value:
                    print_info(f"   {header}: {value}")
        else:
            print_info("CORS headers not detected (may still work)")
        
        return True
        
    except Exception as e:
        print_info(f"CORS test failed: {e} (may still work)")
        return True

def test_agile_endpoint():
    """Test the custom agile endpoint"""
    print_header("AGILE ENDPOINT")
    
    try:
        response = requests.get(f"{BACKEND_URL}/agile/1.0/backlog/issue", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Agile endpoint working")
                print_info(f"   Board ID: {data.get('board_id')}")
                print_info(f"   Issues found: {data.get('backlog_issue_count')}")
                print_info(f"   Branches generated: {data.get('total_branches_found')}")
                return True
            else:
                print_error(f"Agile endpoint error: {data.get('error')}")
                return False
        else:
            print_error(f"Agile endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Agile endpoint error: {e}")
        return False

def check_frontend_running():
    """Check if frontend is running"""
    print_header("FRONTEND STATUS")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print_success(f"Frontend running at {FRONTEND_URL}")
            return True
        else:
            print_error(f"Frontend returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Frontend not accessible: {e}")
        print_info("Make sure to start your frontend with: npm start")
        return False

def generate_integration_report():
    """Generate a summary report"""
    print_header("INTEGRATION TEST SUMMARY")
    
    backend_healthy = test_backend_health()
    endpoints_working = test_frontend_expected_endpoints()
    implementation_plan_ok = test_implementation_plan_endpoints()
    cors_ok = test_cors_headers()
    agile_ok = test_agile_endpoint()
    frontend_running = check_frontend_running()
    
    print_header("FINAL REPORT")
    
    results = {
        "Backend Health": backend_healthy,
        "Frontend Endpoints": endpoints_working,
        "Implementation Plan": implementation_plan_ok,
        "CORS Configuration": cors_ok,
        "Agile Endpoint": agile_ok,
        "Frontend Running": frontend_running
    }
    
    all_good = all(results.values())
    
    for test, passed in results.items():
        if passed:
            print_success(f"{test}")
        else:
            print_error(f"{test}")
    
    print("\n" + "="*60)
    if all_good:
        print("🎉 INTEGRATION STATUS: ALL SYSTEMS GO!")
        print("   Your frontend and backend should work together perfectly.")
        print(f"   Frontend: {FRONTEND_URL}")
        print(f"   Backend: {BACKEND_URL}")
    else:
        print("⚠️  INTEGRATION STATUS: ISSUES DETECTED")
        print("   Check the failed tests above.")
    
    print("\n💡 QUICK TESTS:")
    print(f"   curl \"{BACKEND_URL}/api/jira/issues?project_key=SCRUM\"")
    print(f"   curl \"{BACKEND_URL}/api/health\"")
    print(f"   Open {FRONTEND_URL} in browser")
    
    return all_good

if __name__ == "__main__":
    print("🚀 Frontend-Backend Integration Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = generate_integration_report()
    
    if success:
        print("\n🎯 Ready for development!")
        sys.exit(0)
    else:
        print("\n🔧 Fix the issues above before proceeding.")
        sys.exit(1) 