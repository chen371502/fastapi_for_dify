from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
from typing import List, Optional, Dict, Any
import logging
import json
import time
import uuid
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
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] Health check request received")
    
    try:
        logger.info(f"[{request_id}] Fetching models from LMStudio...")
        models = await client.models.list()
        
        response_data = {
            "status": "healthy",
            "lmstudio": "connected",
            "models_count": len(models.data) if hasattr(models, 'data') else 0,
            "request_id": request_id,
            "processing_time": time.time() - start_time
        }
        
        logger.info(f"[{request_id}] Health check successful: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        logger.info(f"[{request_id}] Available models: {json.dumps([model.model_dump() for model in models.data], ensure_ascii=False, indent=2) if hasattr(models, 'data') else 'No models data'}")
        
        return response_data
    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "error": str(e),
            "request_id": request_id,
            "processing_time": time.time() - start_time
        }
        
        logger.error(f"[{request_id}] Health check failed: {json.dumps(error_response, ensure_ascii=False, indent=2)}")
        logger.error(f"[{request_id}] Exception details: {type(e).__name__}: {str(e)}")
        
        return error_response

async def generate_stream_response(request: ChatCompletionRequest, request_id: str):
    """Generate streaming response for chat completion"""
    start_time = time.time()
    
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Log complete request details
        request_data = {
            "request_id": request_id,
            "messages": messages,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": True,
            "timestamp": start_time
        }
        
        logger.info(f"[{request_id}] Starting streaming chat completion with full request: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        stream = await client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=True
        )
        
        chunk_count = 0
        total_content = ""
        
        async for chunk in stream:
            chunk_count += 1
            chunk_data = chunk.model_dump()
            
            logger.info(f"[{request_id}] Received streaming chunk #{chunk_count}: {json.dumps(chunk_data, ensure_ascii=False, indent=2)}")
            
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                total_content += content
                logger.info(f"[{request_id}] Chunk #{chunk_count} content: {repr(content)}")
                
            yield f"data: {chunk.model_dump_json()}\n\n"
        
        completion_summary = {
            "chunks_received": chunk_count,
            "total_content_length": len(total_content),
            "total_content": repr(total_content),
            "processing_time": time.time() - start_time
        }
        logger.info(f"[{request_id}] Streaming completed: {json.dumps(completion_summary, ensure_ascii=False, indent=2)}")
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time": time.time() - start_time,
            "request_id": request_id
        }
        
        logger.error(f"[{request_id}] Streaming error: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, fastapi_request: Request):
    """Handle both streaming and non-streaming chat completions"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Log complete request details
        request_data = {
            "request_id": request_id,
            "client_ip": fastapi_request.client.host if fastapi_request.client else "unknown",
            "method": fastapi_request.method,
            "url": str(fastapi_request.url),
            "headers": dict(fastapi_request.headers),
            "request_body": {
                "messages": messages,
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stream": request.stream
            }
        }
        
        logger.info(f"[{request_id}] Chat completion request received: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        if request.stream:
            logger.info(f"[{request_id}] Starting streaming response")
            return StreamingResponse(
                generate_stream_response(request, request_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Request-ID": request_id
                }
            )
        else:
            logger.info(f"[{request_id}] Starting non-streaming chat completion")
            
            # Log the request being sent to LMStudio
            lmstudio_request = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stream": False
            }
            
            logger.info(f"[{request_id}] Sending request to LMStudio: {json.dumps(lmstudio_request, ensure_ascii=False, indent=2)}")
            
            response = await client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=False
            )
            
            # Log complete response from LMStudio
            response_data = response.model_dump()
            logger.info(f"[{request_id}] Received complete response from LMStudio: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # Create response object
            api_response = ChatCompletionResponse(
                id=response.id,
                object=response.object,
                created=response.created,
                model=response.model,
                choices=[choice.model_dump() for choice in response.choices],
                usage=response.usage.model_dump()
            )
            
            # Log final response being sent to client
            final_response = api_response.model_dump()
            logger.info(f"[{request_id}] Sending response to client: {json.dumps(final_response, ensure_ascii=False, indent=2)}")
            logger.info(f"[{request_id}] Request completed in {time.time() - start_time:.2f}s")
            
            return api_response
            
    except Exception as e:
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "request_id": request_id,
            "processing_time": time.time() - start_time
        }
        
        logger.error(f"[{request_id}] Chat completion error: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        logger.error(f"[{request_id}] Exception details: {type(e).__name__}: {str(e)}")
        
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@app.get("/models")
async def list_models(fastapi_request: Request):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] Models list request received from {fastapi_request.client.host if fastapi_request.client else 'unknown'}")
    
    try:
        logger.info(f"[{request_id}] Fetching models from LMStudio...")
        models = await client.models.list()
        
        # Log complete models response
        models_data = models.model_dump()
        logger.info(f"[{request_id}] Models retrieved successfully: {json.dumps(models_data, ensure_ascii=False, indent=2)}")
        
        # Log individual model details
        if hasattr(models, 'data') and models.data:
            for i, model in enumerate(models.data):
                model_info = model.model_dump()
                logger.info(f"[{request_id}] Model {i+1}: {json.dumps(model_info, ensure_ascii=False, indent=2)}")
        
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Models request completed in {processing_time:.2f}s")
        
        return models_data
    except Exception as e:
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "request_id": request_id,
            "processing_time": time.time() - start_time
        }
        
        logger.error(f"[{request_id}] Error fetching models: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        logger.error(f"[{request_id}] Exception details: {type(e).__name__}: {str(e)}")
        
        raise HTTPException(status_code=503, detail=f"Failed to connect to LMStudio: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")