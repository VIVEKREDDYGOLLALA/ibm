#!/usr/bin/env python3
"""
Test Enhanced Repository Analysis - Verify that the implementation plan generation now analyzes actual code
"""

import requests
import json

def test_enhanced_analysis():
    """Test the enhanced implementation plan generation with repository analysis"""
    
    print("🚀 Testing Enhanced Repository Analysis")
    print("=" * 60)
    
    backend_url = "http://127.0.0.1:8003"
    
    # Test with your actual Jira ticket and a real repository
    test_cases = [
        {
            "name": "Color Palette Change (Your SCRUM-2 ticket)",
            "issue_key": "SCRUM-2",
            "github_repo_url": "https://github.com/vercel/next.js"
        },
        {
            "name": "Navigation Change (Your SCRUM-1 ticket)", 
            "issue_key": "SCRUM-1",
            "github_repo_url": "https://github.com/facebook/react"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 50)
        
        try:
            print(f"📋 Issue: {test_case['issue_key']}")
            print(f"🔗 Repository: {test_case['github_repo_url']}")
            
            response = requests.post(
                f"{backend_url}/api/generate-implementation-plan",
                json={
                    "issue_key": test_case['issue_key'],
                    "github_repo_url": test_case['github_repo_url']
                },
                timeout=120  # Allow more time for repository analysis
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                plan = result.get('implementation_plan', '')
                
                print(f"✅ Plan generated successfully!")
                print(f"📝 Plan length: {len(plan)} characters")
                
                # Check if the plan mentions specific repository details
                repo_specific_indicators = [
                    'package.json', 'next.config', 'tailwind.config', 
                    'tsconfig', 'components/', 'pages/', 'src/',
                    'index.js', 'index.tsx', '_app.js', '_app.tsx'
                ]
                
                found_indicators = [indicator for indicator in repo_specific_indicators 
                                  if indicator.lower() in plan.lower()]
                
                if found_indicators:
                    print(f"🎯 Repository-specific content found: {found_indicators}")
                    print("✅ Enhanced analysis is working!")
                else:
                    print("⚠️ Plan seems generic - repository analysis may not be working")
                
                # Show a preview of the plan
                print(f"\n📋 Plan Preview (first 500 chars):")
                print("-" * 40)
                print(plan[:500] + "..." if len(plan) > 500 else plan)
                print("-" * 40)
                
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_github_analysis_directly():
    """Test GitHub repository analysis directly"""
    
    print(f"\n🔍 Testing GitHub Analysis Directly")
    print("=" * 50)
    
    # This would test the GitHubRepoAnalyzer class directly
    # For now, just check if the API can access GitHub
    try:
        test_repo = "https://github.com/vercel/next.js"
        print(f"Testing repository access: {test_repo}")
        
        # Try to access the GitHub API directly
        import os
        github_token = os.getenv('GITHUB_TOKEN')
        
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
            print("✅ GitHub token found")
        else:
            print("⚠️ No GitHub token - API rate limited")
        
        headers['Accept'] = 'application/vnd.github.v3+json'
        
        response = requests.get(
            "https://api.github.com/repos/vercel/next.js",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ GitHub API accessible")
            print(f"📂 Repository: {repo_data.get('name')}")
            print(f"🔤 Language: {repo_data.get('language')}")
            print(f"📝 Description: {repo_data.get('description', 'No description')[:100]}...")
        else:
            print(f"❌ GitHub API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ GitHub test error: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced Repository Analysis Test")
    print("🔧 Make sure your backend is running on port 8003")
    print("=" * 60)
    
    test_enhanced_analysis()
    test_github_analysis_directly()
    
    print("\n" + "=" * 60)
    print("✅ Enhanced analysis testing completed!")
    print("\nIf repository-specific content was found in the plans,")
    print("then the enhanced analysis is working correctly!") 