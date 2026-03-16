import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import base64
import os
import asyncio
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Initialize Vertex AI
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION")
)

async def generate_image(prompt: str) -> str:
    """
    Generate an image from a text prompt using Imagen 3.
    Returns base64-encoded PNG string.
    Falls back to a placeholder colored rectangle if generation fails.
    """
    
    # Enhance the prompt for better story illustration quality
    enhanced_prompt = f"""
    Digital illustration, cinematic quality, detailed, 
    story book art style: {prompt}
    """
    
    try:
        # Run synchronous Imagen call in thread pool (it's not async)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            _generate_sync,
            enhanced_prompt
        )
        return result
    except Exception as e:
        print(f"Image generation failed: {e}")
        return _placeholder_image(prompt)

# Global model cache
_model_cache = None

def _get_model():
    global _model_cache
    if _model_cache is None:
        from vertexai.preview.vision_models import ImageGenerationModel
        _model_cache = ImageGenerationModel.from_pretrained("imagegeneration@006")
    return _model_cache

def _generate_sync(prompt: str) -> str:
    """Synchronous wrapper for Imagen."""
    model = _get_model()
    
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        language="en",
        aspect_ratio="1:1",
        safety_filter_level="block_few",
        person_generation="allow_all",
    )
    
    if response and response.images:
        img = response.images[0]
        # Return base64 string
        return base64.b64encode(img._image_bytes).decode("utf-8")
    
    raise Exception("No image generated")

def _placeholder_image(prompt: str) -> str:
    """Return a simple colored placeholder PNG as base64 when Imagen fails."""
    from PIL import Image, ImageDraw
    # Create a nice dark-themed placeholder
    img = Image.new("RGB", (800, 450), color=(30, 30, 50))
    draw = ImageDraw.Draw(img)
    
    # Draw placeholder text
    msg = "Image generating..."
    draw.text((400, 200), msg, fill=(150, 150, 180), anchor="mm")
    
    subtext = prompt[:60] + "..." if len(prompt) > 60 else prompt
    draw.text((400, 230), subtext, fill=(100, 100, 120), anchor="mm")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

async def generate_cover_image(story_title: str, style: str) -> str:
    """Generate a cover/header image for the story."""
    cover_prompt = f"Book cover art, {style} genre, dramatic, cinematic: {story_title}"
    return await generate_image(cover_prompt)
