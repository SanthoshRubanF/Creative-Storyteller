from google import genai
from google.genai import types
import os
import re
import asyncio
from typing import AsyncIterator
from dotenv import load_dotenv
import inspect

load_dotenv()

# System Instruction for the Storyteller Agent
SYSTEM_INSTRUCTION = """
You are a world-class creative director and storyteller. When given a 
story prompt and style, you craft rich, immersive narratives.

INTERLEAVED OUTPUT RULES — this is critical:
- Every 2-3 paragraphs of narrative, insert an image marker in this 
  exact format on its own line:
  [IMAGE: <very detailed visual description for an AI image generator>]
- The image description must describe exactly what a reader would 
  visualize at that moment in the story
- Be specific: include lighting, colors, mood, characters, setting, 
  art style matching the story's genre
- After the image marker, continue the story seamlessly
- Aim for 4-6 image markers total in a full story
- Also insert audio cue markers occasionally:
  [AUDIO: <ambient sound description, e.g. "rain on temple roof, distant thunder">]

STORY QUALITY:
- Write cinematically — show, don't tell
- Use sensory details: sight, sound, smell, touch
- Build tension and emotion
- Vary sentence rhythm
- End with a satisfying conclusion or a deliberate cliffhanger

STYLE GUIDE:
- Fantasy: epic, mythological, magical realism
- Sci-Fi: technical, wonder-filled, philosophical  
- Horror: dread-building, atmospheric, unexpected
- Children's: warm, playful, simple vocabulary, positive
- Noir: cynical, atmospheric, short sentences
"""

MODEL = "gemini-2.0-flash"

# Client Setup
use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"

if use_vertex:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION")
    )
else:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Regex to find complete markers
marker_pattern = re.compile(r'\[(IMAGE|AUDIO):(.*?)\]', re.DOTALL)

async def generate_story_stream(
    prompt: str, 
    style: str = "fantasy"
) -> AsyncIterator[dict]:
    """
    Streams story content as dicts with type field.
    
    Yields:
      {type: "text",          content: "..."}
      {type: "image_request", prompt: "..."}  
      {type: "audio_cue",     description: "..."}
      {type: "done"}
      {type: "error",         message: "..."}
    """
    full_prompt = f"Style: {style}\n\nStory prompt: {prompt}\n\nWrite the complete story now."
    buffer = ""
    
    try:
        # Use streaming generation with polymorphic await
        stream_call = client.aio.models.generate_content_stream(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.9,
                max_output_tokens=2000,
            )
        )
        
        # If it's a coroutine, await it to get the iterable
        if inspect.iscoroutine(stream_call):
            stream = await stream_call
        else:
            stream = stream_call
            
        async for chunk in stream:
            if chunk.text:
                buffer += chunk.text
                
                while True:
                    match = marker_pattern.search(buffer)
                    if match:
                        # Found a complete marker
                        start, end = match.span()
                        text_before = buffer[:start]
                        if text_before:
                            yield {"type": "text", "content": text_before}
                        
                        m_type = match.group(1)
                        m_content = match.group(2).strip()
                        if m_type == "IMAGE":
                            yield {"type": "image_request", "prompt": m_content}
                        else:
                            yield {"type": "audio_cue", "description": m_content}
                        
                        buffer = buffer[end:]
                        continue # Look for more markers in current buffer
                    
                    # No complete marker found. Check for a partial marker at the end.
                    last_bracket = buffer.rfind('[')
                    if last_bracket != -1:
                        text_to_yield = buffer[:last_bracket]
                        if text_to_yield:
                            yield {"type": "text", "content": text_to_yield}
                        buffer = buffer[last_bracket:]
                        break # Wait for more chunks to complete the marker
                    else:
                        if buffer:
                            yield {"type": "text", "content": buffer}
                        buffer = ""
                        break
                        
    except Exception as e:
        yield {"type": "error", "message": f"STORYTELLER_V11_ERROR (Model: {MODEL}): {str(e)}"}
        return

    # Yield any remaining buffer as text (in case of unclosed markers at the end)
    if buffer:
        yield {"type": "text", "content": buffer}
    
    yield {"type": "done"}
