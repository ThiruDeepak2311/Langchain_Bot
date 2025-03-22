from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any, Optional
import json
import os
import logging
import uvicorn
from pathlib import Path
import asyncio
import uuid
import time

# Internal imports
from config import settings, BASE_DIR
from api.routes.chat import router as chat_router
from api.routes.auth import router as auth_router
from core.security import get_current_user
from models.user import User
from services.conversation import ChatManager

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(BASE_DIR / "app.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="An intelligent chatbot that can query data from external sources",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} processed in {process_time:.4f} seconds")
    return response

# Templates and static files setup
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# WebSocket connection manager with enhanced features
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_managers: Dict[str, ChatManager] = {}
        self.last_activity: Dict[str, float] = {}
        self.cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start periodic task to clean up idle connections"""
        self.cleanup_task = asyncio.create_task(self._cleanup_idle_connections())
    
    async def _cleanup_idle_connections(self):
        """Periodically clean up idle connections to prevent memory leaks"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                current_time = time.time()
                idle_threshold = 7200  # 2 hours of inactivity
                
                # Find idle connections
                idle_clients = []
                for client_id, last_active in self.last_activity.items():
                    if current_time - last_active > idle_threshold:
                        idle_clients.append(client_id)
                
                # Disconnect idle clients
                for client_id in idle_clients:
                    logger.info(f"Cleaning up idle connection for client {client_id}")
                    self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error in connection cleanup: {str(e)}")

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.last_activity[client_id] = time.time()
        
        # Create a new chat manager for this connection if it doesn't exist
        if client_id not in self.chat_managers:
            self.chat_managers[client_id] = ChatManager()
            logger.info(f"New chat manager created for client {client_id}")
        else:
            logger.info(f"Reconnected client {client_id} to existing chat manager")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.chat_managers:
            del self.chat_managers[client_id]
        if client_id in self.last_activity:
            del self.last_activity[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
                self.last_activity[client_id] = time.time()
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
                self.disconnect(client_id)

    async def send_typing_indicator(self, client_id: str, is_typing: bool):
        """Send typing indicator to client"""
        if client_id in self.active_connections:
            try:
                await self.send_personal_message(
                    json.dumps({"type": "typing", "status": is_typing}),
                    client_id
                )
            except Exception as e:
                logger.error(f"Error sending typing indicator: {str(e)}")

    async def chat(self, message: str, client_id: str):
        chat_manager = self.chat_managers.get(client_id)
        if not chat_manager:
            await self.send_personal_message(
                json.dumps({"type": "error", "message": "Chat session not found"}),
                client_id
            )
            return
        
        # Update last activity time
        self.last_activity[client_id] = time.time()
        
        # Generate message ID
        message_id = str(uuid.uuid4())
        
        # Show typing indicator
        await self.send_typing_indicator(client_id, True)
        
        # Process message with chat manager
        try:
            # Start response timer
            start_time = time.time()
            
            # We support streaming but it's not implemented in the UI yet
            # For now, just get the full response
            response = await chat_manager.process_message(message, stream=False)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Hide typing indicator
            await self.send_typing_indicator(client_id, False)
            
            # Send the response
            await self.send_personal_message(
                json.dumps({
                    "type": "message", 
                    "role": "assistant", 
                    "content": response,
                    "id": message_id,
                    "metadata": {
                        "response_time": round(response_time, 2)
                    }
                }),
                client_id
            )
            
            logger.info(f"Response sent to client {client_id} in {response_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            # Hide typing indicator
            await self.send_typing_indicator(client_id, False)
            
            # Send error message
            await self.send_personal_message(
                json.dumps({
                    "type": "error", 
                    "message": "Sorry, I encountered an error while processing your message. Please try again."
                }),
                client_id
            )


manager = ConnectionManager()

# Register API routes
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["authentication"]
)

app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["chat"]
)

# Root endpoint to serve the frontend
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if message_data.get("type") == "message":
                    await manager.chat(message_data.get("content", ""), client_id)
                elif message_data.get("type") == "clear_history":
                    # Add support for clearing chat history
                    if client_id in manager.chat_managers:
                        manager.chat_managers[client_id].clear_history()
                        await manager.send_personal_message(
                            json.dumps({"type": "system", "message": "Chat history cleared"}),
                            client_id
                        )
            except json.JSONDecodeError:
                # Fallback to treating the entire data as a message
                await manager.chat(data, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        manager.disconnect(client_id)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting up the application")
    
    # Start the cleanup task for websocket connections
    await manager.start_cleanup_task()
    
    # Log configuration information
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"Application initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down the application")
    
    # Clean up resources
    if manager.cleanup_task and not manager.cleanup_task.done():
        manager.cleanup_task.cancel()
    
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    # For local development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)