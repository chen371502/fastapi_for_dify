#!/usr/bin/env python3
"""
Test script for streaming chat completion
"""
import requests
import json
import time

def test_streaming_chat():
    """Test streaming chat completion"""
    print("🔄 Testing streaming chat completion...")
    
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "请写一段Python的快速排序代码"}
            ],
            "temperature": 0.7,
            "max_tokens": 200,
            "stream": True
        }
        
        # 使用 stream=True 来接收流式响应
        response = requests.post(
            "http://localhost:8000/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=60
        )
        
        print(f"✅ Streaming response status: {response.status_code}")
        
        if response.status_code == 200:
            print("📨 Streaming content:")
            print("-" * 50)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # 去掉 'data: ' 前缀
                        if data != '[DONE]':
                            try:
                                chunk = json.loads(data)
                                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_response += content
                            except json.JSONDecodeError:
                                continue
            
            print("\n" + "-" * 50)
            print("✅ Streaming completed")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Streaming request timed out")
        return False
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Streaming Chat Completion")
    print("=" * 50)
    test_streaming_chat()