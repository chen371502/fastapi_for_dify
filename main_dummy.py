from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
import time
import uuid
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dummy Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "dummy-model"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "dummy": "running"}

async def generate_streaming_poetry(request_id: str, user_message: str):
    """Generate streaming response with 将进酒 poem"""
    poem_lines = [
        "君不见，黄河之水天上来，奔流到海不复回。",
        "君不见，高堂明镜悲白发，朝如青丝暮成雪。",
        "人生得意须尽欢，莫使金樽空对月。",
        "天生我材必有用，千金散尽还复来。",
        "烹羊宰牛且为乐，会须一饮三百杯。",
        "岑夫子，丹丘生，将进酒，杯莫停。",
        "与君歌一曲，请君为我倾耳听。",
        "钟鼓馔玉不足贵，但愿长醉不复醒。",
        "古来圣贤皆寂寞，惟有饮者留其名。",
        "陈王昔时宴平乐，斗酒十千恣欢谑。",
        "主人何为言少钱，径须沽取对君酌。",
        "五花马，千金裘，呼儿将出换美酒，",
        "与尔同销万古愁。"
    ]
    
    logger.info(f"[{request_id}] Starting poetry streaming")
    
    for i, line in enumerate(poem_lines):
        chunk = {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "dummy-model",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": line + "\n"
                    },
                    "finish_reason": None
                }
            ]
        }
        
        yield f"data: {json.dumps(chunk)}\n\n"
        
        # Small delay for realistic streaming effect
        import asyncio
        await asyncio.sleep(0.5)
    
    # 添加空行和用户输入回显
    echo_chunk = {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "dummy-model",
        "choices": [
            {
                "index": 0,
                "delta": {
                    "content": "\n\n您刚才输入的内容是: " + user_message
                },
                "finish_reason": "stop"
            }
        ]
    }
    yield f"data: {json.dumps(echo_chunk)}\n\n"
    
    # 最终结束chunk
    final_echo_chunk = {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "dummy-model",
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }
    yield f"data: {json.dumps(final_echo_chunk)}\n\n"
    yield "data: [DONE]\n\n"
    
    logger.info(f"[{request_id}] Poetry streaming completed with user input echo")

@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle chat completions with dummy responses"""
    request_id = str(uuid.uuid4())
    
    # Log request received
    logger.info(f"[{request_id}] Chat completion request received - stream: {request.stream}")
    
    try:
        if request.stream:
            # 获取用户最后一条消息用于回显
            user_message = request.messages[-1].content if request.messages else ""
            logger.info(f"[{request_id}] Starting streaming response (将进酒), user input: {user_message}")
            return StreamingResponse(
                generate_streaming_poetry(request_id, user_message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            logger.info(f"[{request_id}] Returning non-streaming response (pong)")
            
            response_data = {
                "id": f"chatcmpl-{request_id}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model or "dummy-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "pong."
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(str(request.messages)),
                    "completion_tokens": 1,
                    "total_tokens": len(str(request.messages)) + 1
                }
            }
            
            logger.info(f"[{request_id}] Response sent: pong")
            return response_data
            
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")