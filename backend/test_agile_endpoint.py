#!/usr/bin/env python3
"""
Test script for the /agile/1.0/backlog/issue endpoint
This script tests the connectivity and functionality of the new agile API endpoint
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
AGILE_ENDPOINT = f"{BASE_URL}/agile/1.0/backlog/issue"
HEALTH_ENDPOINT = f"{BASE_URL}/api/health"

def test_server_health():
    """Test if the server is running and healthy"""
    print("Testing server health...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Server is healthy")
            print(f"   Jira Status: {health_data.get('services', {}).get('jira', {}).get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_agile_endpoint():
    """Test the agile backlog issue endpoint"""
    print("\nTesting agile backlog endpoint...")
    
    try:
        # Test without board_id (should use first available board)
        response = requests.get(AGILE_ENDPOINT, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Agile endpoint is working!")
            print(f"   Connectivity Status: {data.get('connectivity_status')}")
            print(f"   Board ID: {data.get('board_id')}")
            print(f"   Backlog Issues: {data.get('backlog_issue_count')}")
            print(f"   Total Branches Found: {data.get('total_branches_found')}")
            
            # Display sample branches
            branches = data.get('branches', [])
            if branches:
                print(f"   Sample Branches (showing {len(branches)}):")
                for i, branch in enumerate(branches[:3], 1):
                    print(f"     {i}. Issue: {branch.get('issue_key')} - {branch.get('summary', '')[:50]}...")
                    print(f"        Potential branches: {', '.join(branch.get('potential_branches', [])[:2])}")
            
            return True
            
        elif response.status_code == 503:
            print("❌ Jira service not available")
            print("   Check your Jira configuration in .env file")
            return False
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_with_board_id():
    """Test the endpoint with a specific board ID"""
    print("\nTesting agile endpoint with board_id parameter...")
    
    try:
        # Test with board_id=1 (common default)
        response = requests.get(f"{AGILE_ENDPOINT}?board_id=1", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Board ID parameter works!")
            print(f"   Used Board ID: {data.get('board_id')}")
        else:
            print(f"ℹ️  Board ID 1 not found or accessible (Status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request with board_id failed: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Agile Backlog Issue Endpoint")
    print("=" * 50)
    
    # Test server health first
    if not test_server_health():
        print("\n❌ Server is not healthy. Please start the server first:")
        print("   cd backend && python main.py")
        sys.exit(1)
    
    # Test the main endpoint
    if test_agile_endpoint():
        # Test with board_id parameter
        test_with_board_id()
        
        print("\n🎉 All tests completed!")
        print("\nEndpoint URL:", AGILE_ENDPOINT)
        print("Usage examples:")
        print(f"  GET {AGILE_ENDPOINT}")
        print(f"  GET {AGILE_ENDPOINT}?board_id=1")
        
    else:
        print("\n❌ Main endpoint test failed")
        print("\nTroubleshooting:")
        print("1. Make sure the server is running: python main.py")
        print("2. Check your Jira configuration in .env file")
        print("3. Ensure you have at least one agile board in your Jira instance")
        sys.exit(1)

if __name__ == "__main__":
    main() 