#!/usr/bin/env python3
"""
Test script to verify GitHub repository analysis functionality
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / 'backend'))

# Import the GitHub analyzer
from ultimate_main import GitHubRepoAnalyzer, load_environment

# Load environment variables
load_environment()

def test_repo_analysis():
    """Test the GitHub repository analysis"""
    
    # Initialize the analyzer
    github_token = os.getenv('GITHUB_TOKEN')
    analyzer = GitHubRepoAnalyzer(github_token)
    
    print("🔍 Testing GitHub Repository Analysis")
    print(f"GitHub Token configured: {'Yes' if github_token else 'No'}")
    print()
    
    # Test with your portfolio repo
    github_url = "https://github.com/VIVEKREDDYGOLLALA/Portfolio"
    ticket_context = "change the color palette to black and purple"
    
    print(f"📋 Analyzing repository: {github_url}")
    print(f"🎯 Ticket context: {ticket_context}")
    print()
    
    # Test URL parsing
    parsed = analyzer.parse_github_url(github_url)
    print(f"✅ URL Parsing: {parsed}")
    
    if not parsed:
        print("❌ URL parsing failed!")
        return
    
    owner, repo = parsed['owner'], parsed['repo']
    print(f"📁 Owner: {owner}, Repo: {repo}")
    
    # Test repository info
    print("\n🔍 Getting repository information...")
    repo_info = analyzer.get_repository_info(owner, repo)
    if repo_info:
        print(f"✅ Repository Info:")
        print(f"   - Name: {repo_info['name']}")
        print(f"   - Description: {repo_info.get('description', 'N/A')}")
        print(f"   - Language: {repo_info.get('language', 'N/A')}")
        print(f"   - Topics: {repo_info.get('topics', [])}")
    else:
        print("❌ Failed to get repository info")
        return
    
    # Test directory contents
    print("\n🔍 Getting directory contents...")
    contents = analyzer.get_directory_contents(owner, repo)
    print(f"✅ Root directory has {len(contents)} items")
    for item in contents[:10]:  # Show first 10 items
        print(f"   - {item['name']} ({item['type']})")
    
    # Test relevant file finding
    print(f"\n🔍 Finding files relevant to: '{ticket_context}'...")
    relevant_files = analyzer.find_relevant_files(owner, repo, ticket_context)
    print(f"✅ Found {len(relevant_files)} relevant files:")
    for file_info in relevant_files:
        print(f"   - {file_info['path']} ({file_info['type']}, {file_info['relevance']} relevance)")
    
    # Test file content retrieval
    if relevant_files:
        print(f"\n🔍 Getting content from first relevant file...")
        first_file = relevant_files[0]
        content = analyzer.get_file_content(owner, repo, first_file['path'])
        if content:
            print(f"✅ File content retrieved ({len(content)} characters)")
            print(f"   First 200 chars: {content[:200]}...")
        else:
            print("❌ Failed to get file content")
    
    # Test full repository analysis
    print(f"\n🔍 Running full repository analysis...")
    analysis = analyzer.analyze_repository(github_url, ticket_context)
    
    if analysis.get("success"):
        print("✅ Full analysis successful!")
        print(f"   - Repository: {analysis['repository']['name']}")
        print(f"   - Language: {analysis['repository']['language']}")
        print(f"   - Total relevant files: {analysis['total_files_found']}")
        print(f"   - Files with content: {len(analysis['file_contents'])}")
        
        print("\n📂 Relevant files found:")
        for file_info in analysis['relevant_files']:
            print(f"   - {file_info['path']} ({file_info['type']}, {file_info['relevance']})")
        
        print("\n📄 File contents analyzed:")
        for file_path in analysis['file_contents'].keys():
            print(f"   - {file_path}")
            
    else:
        print(f"❌ Full analysis failed: {analysis.get('error')}")

if __name__ == "__main__":
    test_repo_analysis() 