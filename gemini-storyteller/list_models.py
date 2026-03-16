from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    print(f"Using Vertex AI: {use_vertex}")
    
    if use_vertex:
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION")
        )
    else:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    print("Available models:")
    try:
        for model in client.models.list():
            print(f"- {model.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
