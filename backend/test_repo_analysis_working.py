#!/usr/bin/env python3
"""
Test script to verify repository analysis functionality is working correctly
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_repo_analysis():
    """Test the enhanced repository analysis"""
    try:
        # Import the enhanced analyzer
        from ultimate_main import EnhancedGitHubAnalyzer, load_environment
        
        # Load environment
        load_environment()
        
        print("🔍 Testing Enhanced GitHub Repository Analysis")
        print("=" * 60)
        
        # Initialize analyzer
        analyzer = EnhancedGitHubAnalyzer()
        
        # Test repository
        github_url = "https://github.com/VIVEKREDDYGOLLALA/Portfolio"
        ticket_context = "change the color palette to black and purple"
        
        print(f"📋 Repository: {github_url}")
        print(f"🎯 Ticket Context: {ticket_context}")
        print()
        
        # Perform analysis
        print("🔍 Performing comprehensive repository analysis...")
        result = analyzer.analyze_repository(github_url, ticket_context)
        
        if result.get("success"):
            print("✅ Repository analysis SUCCESSFUL!")
            print()
            
            # Print analysis results
            repo_info = result.get("repository", {})
            print(f"📋 Repository: {repo_info.get('name', 'Unknown')}")
            print(f"🔤 Language: {repo_info.get('language', 'Unknown')}")
            print(f"📝 Description: {repo_info.get('description', 'No description')}")
            print(f"⭐ Stars: {repo_info.get('stars', 0)}")
            print()
            
            # Keyword categories
            keyword_categories = result.get("keyword_categories", {})
            print("🎯 KEYWORD CATEGORIES EXTRACTED:")
            for category, keywords in keyword_categories.items():
                if keywords:
                    print(f"   {category}: {', '.join(keywords)}")
            print()
            
            # Relevant files
            relevant_files = result.get("relevant_files", [])
            print(f"📂 RELEVANT FILES FOUND: {len(relevant_files)}")
            print(f"🔥 High Priority Files: {result.get('high_relevance_files', 0)}")
            print()
            
            # Top files
            print("📄 TOP RELEVANT FILES:")
            for i, file_info in enumerate(relevant_files[:8], 1):
                print(f"   {i}. {file_info['path']} ({file_info['type']}, {file_info['relevance']})")
                print(f"      Score: {file_info['score']}, Reasons: {', '.join(file_info['reasons'][:2])}")
            print()
            
            # File contents analysis
            file_contents = result.get("file_contents_analysis", {})
            print(f"💻 FILES WITH CONTENT ANALYZED: {len(file_contents)}")
            for file_path in list(file_contents.keys())[:3]:
                content_info = file_contents[file_path]
                print(f"   📄 {file_path} ({content_info['type']}, {content_info['relevance']})")
                print(f"      Content preview: {content_info['content'][:100]}...")
            print()
            
            # Architecture summary
            architecture = result.get("architecture_summary", "")
            if architecture:
                print("🏗️ ARCHITECTURE ANALYSIS:")
                print(architecture[:500] + "..." if len(architecture) > 500 else architecture)
            
            print("=" * 60)
            print("🎉 REPOSITORY ANALYSIS IS WORKING CORRECTLY!")
            print(f"✅ Found {len(relevant_files)} relevant files")
            print(f"✅ Analyzed {len(file_contents)} file contents")
            print(f"✅ Extracted {len([k for k, v in keyword_categories.items() if v])} keyword categories")
            
            return True
            
        else:
            print(f"❌ Repository analysis FAILED: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_repo_analysis()
    sys.exit(0 if success else 1) 