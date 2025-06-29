#!/usr/bin/env python3
"""
IBM Granite Document Summarization Test Script
This script demonstrates document chunking and summarization using IBM Granite models.
"""

import os
import requests
import json
from typing import List, Dict, Iterator
from transformers import AutoTokenizer

# IBM Granite API Configuration
class GraniteAPI:
    def __init__(self, api_key: str, project_id: str, base_url: str = "https://eu-de.ml.cloud.ibm.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url
        self.generation_endpoint = f"{base_url}/ml/v1/text/generation?version=2023-05-29"
        self.bearer_token = None
        self.token_expires_at = 0
    
    def get_bearer_token(self):
        """Generate Bearer token from IBM API key"""
        import time
        
        # Check if we have a valid token
        if self.bearer_token and time.time() < self.token_expires_at:
            return self.bearer_token
        
        print("🔄 Generating new Bearer token from API key...")
        
        token_url = "https://iam.cloud.ibm.com/identity/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': self.api_key
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            print(f"Token request status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.bearer_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                
                # Set expiration time (refresh 5 minutes early)
                self.token_expires_at = time.time() + expires_in - 300
                
                print(f"✅ Bearer token generated! Expires in {expires_in//60} minutes")
                print(f"Bearer token: {self.bearer_token[:20]}...")
                
                return self.bearer_token
            else:
                print(f"❌ Error generating Bearer token: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception generating Bearer token: {e}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Generate text using IBM Granite Text Generation API"""
        bearer_token = self.get_bearer_token()
        if not bearer_token:
            print("Failed to get Bearer token")
            return ""
        
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "input": prompt,
            "parameters": {
                "decoding_method": "sample" if temperature > 0 else "greedy",
                "max_new_tokens": max_tokens,
                "min_new_tokens": 0,
                "stop_sequences": [],
                "repetition_penalty": 1
            },
            "model_id": "ibm/granite-3-8b-instruct",
            "project_id": self.project_id,
            "moderations": {
                "hap": {
                    "input": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    },
                    "output": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    }
                },
                "pii": {
                    "input": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    },
                    "output": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    }
                },
                "granite_guardian": {
                    "input": {
                        "enabled": False,
                        "threshold": 1
                    }
                }
            }
        }
        
        # Add temperature only for sampling mode
        if payload["parameters"]["decoding_method"] == "sample":
            payload["parameters"]["temperature"] = temperature
        
        try:
            print(f"Making request to: {self.generation_endpoint}")
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return ""
                
            result = response.json()
            print(f"API Response keys: {list(result.keys())}")
            
            # Handle text generation API response format
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0].get('generated_text', '')
                print(f"Generated text length: {len(generated_text)} characters")
                return generated_text
            else:
                print(f"Unexpected response format: {result}")
                return ""
                
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Error response: {e.response.text}")
            return ""

# Simple document chunker (simplified version without docling dependency)
class SimpleChunker:
    def __init__(self, max_chunk_size: int = 3000):
        self.max_chunk_size = max_chunk_size
    
    def chunk_text(self, text: str, title: str = "Document") -> List[Dict[str, str]]:
        """Split text into chunks of approximately max_chunk_size characters"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_id = 1
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and current_chunk:
                chunks.append({
                    'doc_id': str(chunk_id),
                    'title': f"{title} - Part {chunk_id}",
                    'text': current_chunk.strip()
                })
                current_chunk = paragraph
                chunk_id += 1
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append({
                'doc_id': str(chunk_id),
                'title': f"{title} - Part {chunk_id}",
                'text': current_chunk.strip()
            })
        
        return chunks

def create_summarization_prompt(documents: List[Dict[str, str]], instruction: str) -> str:
    """Create a prompt with documents for summarization"""
    prompt = f"{instruction}\n\n"
    
    for doc in documents:
        prompt += f"Document: {doc['title']}\n"
        prompt += f"Content: {doc['text']}\n\n"
    
    return prompt

def test_granite_summarization():
    """Test IBM Granite model for document summarization"""
    
    # Configuration - Using your environment variables
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("Please set your IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return
    
    # Initialize components
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    chunker = SimpleChunker(max_chunk_size=2000)
    
    # Initialize tokenizer for token counting
    model_path = "ibm-granite/granite-3.3-8b-instruct"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        print(f"Loaded tokenizer for {model_path}")
    except Exception as e:
        print(f"Could not load tokenizer: {e}")
        tokenizer = None
    
    # Sample document for testing
    sample_text = """
    Artificial Intelligence and Machine Learning Revolution
    
    Artificial Intelligence (AI) has emerged as one of the most transformative technologies of the 21st century. From its humble beginnings in the 1950s as a theoretical concept, AI has evolved into a practical reality that touches nearly every aspect of our daily lives.
    
    The foundation of modern AI lies in machine learning, a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. Machine learning algorithms can identify patterns in data, make predictions, and adapt their behavior based on new information.
    
    Deep Learning Revolution
    
    Deep learning, inspired by the structure and function of the human brain, represents a significant breakthrough in machine learning. Neural networks with multiple layers can process complex data such as images, speech, and text with unprecedented accuracy.
    
    Applications in Healthcare
    
    In healthcare, AI is revolutionizing diagnosis and treatment. Machine learning models can analyze medical images to detect cancer, predict patient outcomes, and assist doctors in making more accurate diagnoses. AI-powered drug discovery is accelerating the development of new treatments.
    
    Business and Industry Impact
    
    Businesses across industries are leveraging AI to optimize operations, enhance customer experiences, and drive innovation. From recommendation systems in e-commerce to autonomous vehicles in transportation, AI is reshaping how we work and live.
    
    Ethical Considerations
    
    As AI becomes more powerful and pervasive, ethical considerations become increasingly important. Issues such as bias in algorithms, privacy concerns, and the impact on employment require careful consideration and regulation.
    
    Future Prospects
    
    The future of AI holds immense promise. Advances in quantum computing, neuromorphic chips, and artificial general intelligence could lead to breakthroughs we can barely imagine today. However, realizing this potential while addressing associated challenges will require collaboration between technologists, policymakers, and society as a whole.
    """
    
    print("=" * 60)
    print("IBM GRANITE DOCUMENT SUMMARIZATION TEST")
    print("=" * 60)
    
    # Step 1: Chunk the document
    print("\n1. Chunking document...")
    chunks = chunker.chunk_text(sample_text, "AI Revolution Article")
    print(f"Created {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        token_count = len(tokenizer.tokenize(chunk['text'])) if tokenizer else len(chunk['text'].split())
        print(f"  Chunk {i+1}: {chunk['title']} ({token_count} {'tokens' if tokenizer else 'words'})")
    
    # Step 2: Summarize each chunk
    print("\n2. Summarizing individual chunks...")
    chunk_summaries = []
    
    for i, chunk in enumerate(chunks):
        print(f"\nSummarizing chunk {i+1}/{len(chunks)}: {chunk['title']}")
        
        instruction = """Using only the provided document, create a concise summary that captures the key points and main ideas. Your response should only include the summary without any additional explanation."""
        
        prompt = create_summarization_prompt([chunk], instruction)
        
        if tokenizer:
            token_count = len(tokenizer.tokenize(prompt))
            print(f"Input prompt: {token_count} tokens")
        
        summary = granite_api.generate(prompt, max_tokens=500, temperature=0.7)
        
        if summary:
            chunk_summaries.append({
                'doc_id': str(i+1),
                'title': f"Summary of {chunk['title']}",
                'text': summary.strip()
            })
            print(f"Generated summary ({len(summary.split())} words)")
        else:
            print("Failed to generate summary")
    
    # Step 3: Create final unified summary
    if chunk_summaries:
        print(f"\n3. Creating unified summary from {len(chunk_summaries)} chunk summaries...")
        
        instruction = """Using the provided chapter summaries, create a single, comprehensive summary that unifies all the key points into a coherent overview. Your response should only include the unified summary without any additional explanation."""
        
        final_prompt = create_summarization_prompt(chunk_summaries, instruction)
        
        if tokenizer:
            token_count = len(tokenizer.tokenize(final_prompt))
            print(f"Final prompt: {token_count} tokens")
        
        final_summary = granite_api.generate(final_prompt, max_tokens=800, temperature=0.7)
        
        print("\n" + "=" * 60)
        print("FINAL UNIFIED SUMMARY")
        print("=" * 60)
        print(final_summary.strip())
        print("=" * 60)
    else:
        print("No chunk summaries were generated, cannot create final summary")

def test_simple_generation():
    """Test basic text generation with IBM Granite"""
    API_KEY = os.getenv('IBM_GRANITE_API_KEY')
    PROJECT_ID = os.getenv('IBM_PROJECT_ID')
    
    if not API_KEY or not PROJECT_ID:
        print("Please set your IBM_GRANITE_API_KEY and IBM_PROJECT_ID environment variables")
        return
    
    granite_api = GraniteAPI(API_KEY, PROJECT_ID)
    
    prompt = "Explain quantum computing in simple terms."
    
    print("Testing basic text generation...")
    response = granite_api.generate(prompt, max_tokens=300)
    
    if response:
        print("Success! Generated response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
    else:
        print("Failed to generate response")

if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded environment variables from .env file")
    except ImportError:
        print("python-dotenv not installed. Make sure environment variables are set manually.")
        print("Install with: pip install python-dotenv")
    
    print("IBM Granite API Test Script")
    print("Using environment variables: IBM_GRANITE_API_KEY and IBM_PROJECT_ID")
    print()
    
    # Uncomment the test you want to run:
    
    # Test 1: Simple generation test
    test_simple_generation()
    
    # Test 2: Full document summarization test
    # test_granite_summarization()