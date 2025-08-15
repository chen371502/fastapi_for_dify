from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import List, Optional, Dict, Any, AsyncGenerator
import logging
import json
from openai import AsyncOpenAI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LMStudio Chat Completion API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境请限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LMStudio configuration - adjust for your setup
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://192.168.10.41:1234/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-coder-30b")

# Initialize OpenAI client for LMStudio
client = AsyncOpenAI(
    base_url=LMSTUDIO_BASE_URL,
    api_key="lm-studio"  # LMStudio doesn't require a real API key
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = MODEL_NAME
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "LMStudio Chat Completion API is running"}

@app.get("/health")
async def health_check():
    try:
        models = await client.models.list()
        return {"status": "healthy", "lmstudio": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

async def generate_stream_response(request: ChatCompletionRequest):
    """Generate streaming response for chat completion"""
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        logger.info(f"Starting streaming chat completion with model: {request.model}")
        
        stream = await client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield f"data: {chunk.model_dump_json()}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Handle both streaming and non-streaming chat completions"""
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        if request.stream:
            logger.info("Starting streaming response")
            return StreamingResponse(
                generate_stream_response(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            logger.info("Starting non-streaming chat completion")
            
            response = await client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=False
            )
            
            logger.info(f"Received non-streaming response: {response.choices[0].message.content[:100]}...")
            
            return ChatCompletionResponse(
                id=response.id,
                object=response.object,
                created=response.created,
                model=response.model,
                choices=[choice.model_dump() for choice in response.choices],
                usage=response.usage.model_dump()
            )
            
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@app.get("/models")
async def list_models():
    try:
        models = await client.models.list()
        return models.model_dump()
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to LMStudio: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")