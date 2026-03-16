from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import asyncio
import json
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv() # Load from current or parent dir

# Import local modules
from storyteller import generate_story_stream
from image_gen import generate_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("storyteller-api")

# Concurrency limit
MAX_CONCURRENT_STORIES = 3
active_generations = asyncio.Semaphore(MAX_CONCURRENT_STORIES)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Gemini Creative Storyteller...")
    logger.info("Models: gemini-2.0-flash, imagegeneration@006")
    yield
    # Shutdown logic
    logger.info("Shutting down Gemini Creative Storyteller...")

app = FastAPI(title="Gemini Creative Storyteller", lifespan=lifespan)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class StoryRequest(BaseModel):
    prompt: str
    style: str = "fantasy"

class ImageRequest(BaseModel):
    prompt: str

# Endpoints
@app.get("/")
async def get_index():
    index_path = os.path.join(os.getcwd(), "frontend", "index.html")
    if not os.path.exists(index_path):
        # Local development fallback
        index_path = os.path.join(os.getcwd(), "frontend", "index.html")
    return FileResponse(index_path, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})

@app.get("/story/stream")
async def story_stream(prompt: str, style: str = "Fantasy"):
    """SSE endpoint for story generation (GET for better SSE support)."""
    
    async def event_generator():
        # Immediate yield to establish connection
        yield { "event": "status", "data": json.dumps({"type": "status", "message": "Connected v11..."}) }
        
        queue = asyncio.Queue()
        
        async def image_worker(img_prompt: str):
            try:
                # Use local reference to avoid closure issues
                logger.info(f"Image Worker: {img_prompt[:30]}")
                b64 = await generate_image(img_prompt)
                await queue.put({
                    "event": "image",
                    "data": json.dumps({"type": "image", "data": b64, "alt": img_prompt})
                })
            except Exception as e:
                logger.error(f"Image Worker Error: {e}")

        async def producer():
            try:
                async with active_generations:
                    await queue.put({ "event": "status", "data": json.dumps({"type": "status", "message": "Writing..."}) })
                    
                    # Store image tasks to await them at the end
                    img_tasks = []
                    
                    async for chunk in generate_story_stream(prompt, style):
                        if chunk["type"] == "text":
                            await queue.put({ "event": "story", "data": json.dumps({"text": chunk["content"]}) })
                        elif chunk["type"] == "image_request":
                            await queue.put({ "event": "status", "data": json.dumps({"type": "image_loading", "alt": chunk["prompt"]}) })
                            img_tasks.append(asyncio.create_task(image_worker(chunk["prompt"])))
                        elif chunk["type"] == "audio_cue":
                            await queue.put({ "event": "audio_cue", "data": json.dumps({"type": "audio_cue", "description": chunk["description"]}) })
                        elif chunk["type"] == "done":
                            if img_tasks:
                                await asyncio.gather(*img_tasks, return_exceptions=True)
                            await queue.put({ "event": "done", "data": json.dumps({"type": "done"}) })
                            break
                        elif chunk["type"] == "error":
                            await queue.put({ "event": "error", "data": json.dumps({"type": "error", "message": chunk["message"]}) })
                            break
            except Exception as e:
                logger.exception("Producer failed")
                await queue.put({ "event": "error", "data": json.dumps({"type": "error", "message": f"STORYTELLER_V11_ERROR: {str(e)}"}) })
            finally:
                await queue.put(None)

        # Heartbeat task
        async def heartbeat():
            while True:
                await asyncio.sleep(15)
                await queue.put({ "event": "ping", "data": "pulse" })

        p_task = asyncio.create_task(producer())
        h_task = asyncio.create_task(heartbeat())
        
        try:
            while True:
                item = await queue.get()
                if item is None: break
                yield item
        finally:
            p_task.cancel()
            h_task.cancel()

    return EventSourceResponse(event_generator())

@app.post("/image/generate")
async def standalone_image_gen(request: ImageRequest):
    try:
        image_b64 = await generate_image(request.prompt)
        return {"image": image_b64, "prompt": request.prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model": "gemini-2.0-flash",
        "image_model": "imagegeneration@006",
        "version": "1.0.0"
    }

@app.get("/styles")
async def get_styles():
    return [
        {"id": "fantasy", "name": "Fantasy", "description": "Epic, mythological, magical"},
        {"id": "sci-fi",  "name": "Sci-Fi",   "description": "Futuristic, technical, wonder"},
        {"id": "horror",  "name": "Horror",   "description": "Atmospheric, dread-building"},
        {"id": "children","name": "Children's", "description": "Warm, playful, simple"},
        {"id": "noir",    "name": "Noir",     "description": "Cynical, atmospheric, dark"}
    ]

# Mount static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
