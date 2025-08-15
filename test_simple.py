#!/usr/bin/env python3
"""
Simple test script for the LMStudio FastAPI wrapper
"""
import requests
import json
import sys

def test_connection():
    """Test basic connection"""
    try:
        # Test if FastAPI server is running
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server. Please start it first:")
        print("   python main.py")
        return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False
    
    try:
        # Test health check
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        health_data = response.json()
        print(f"   Status: {health_data}")
        
        if health_data.get('status') != 'healthy':
            print("⚠️  LMStudio might not be running or accessible")
            print("   Please check if LMStudio is running at http://192.168.10.41:1234")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Health check timed out - LMStudio might not be running")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    return True

def test_chat():
    """Test chat completion"""
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello, are you working?"}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False
        }
        
        print("🔄 Testing chat completion...")
        response = requests.post(
            "http://localhost:8000/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"✅ Chat completion: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print(f"   Reply: {reply}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Chat completion timed out")
    except Exception as e:
        print(f"❌ Chat completion error: {e}")

if __name__ == "__main__":
    print("🔍 Testing LMStudio FastAPI wrapper...")
    print("=" * 50)
    
    if test_connection():
        print("\n" + "=" * 50)
        test_chat()
    else:
        print("\n❌ Stopping tests due to connection issues")