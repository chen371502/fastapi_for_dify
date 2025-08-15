#!/usr/bin/env python3
"""
Test script for the LMStudio FastAPI wrapper
"""
import requests
import json

def test_health():
    """Test health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print("Health check:", response.status_code)
        if response.status_code == 200:
            print("Health response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print("Health check failed:", str(e))
        return False

def test_chat_completion():
    """Test chat completion endpoint"""
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello, can you help me with Python?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(
            "http://localhost:8000/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print("Chat completion:", response.status_code)
        if response.status_code == 200:
            result = response.json()
            print("Response:", result["choices"][0]["message"]["content"])
            return True
        else:
            print("Error:", response.text)
            return False
    except Exception as e:
        print("Chat completion failed:", str(e))
        return False

def test_models():
    """Test models endpoint"""
    try:
        response = requests.get("http://localhost:8000/models")
        print("Models endpoint:", response.status_code)
        if response.status_code == 200:
            models = response.json()
            print("Available models:", models)
        return response.status_code == 200
    except Exception as e:
        print("Models check failed:", str(e))
        return False

if __name__ == "__main__":
    print("Testing LMStudio FastAPI wrapper...")
    
    # Test endpoints
    test_health()
    test_models()
    test_chat_completion()