import os
import json
import requests
import sys

# Add parent dir so we can import the in-memory credentials loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from googleDrive.credentials_loader import get_env_var

def main():
    api_key = get_env_var("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Let's test with llama-3.3-70b-versatile
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": "Respond with a JSON object: {\"status\": \"ok\", \"message\": \"hello from llama 3.3\"}"}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    print("Testing llama-3.3-70b-versatile...")
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"Error: {e}")
        
    # Let's test with openai/gpt-oss-120b
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "user", "content": "Respond with a JSON object: {\"status\": \"ok\", \"message\": \"hello from gpt-oss-120b\"}"}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    print("\nTesting openai/gpt-oss-120b...")
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
