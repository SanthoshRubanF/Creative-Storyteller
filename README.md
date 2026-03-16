# Gemini Storyteller 🖋️✨

A world-class creative storytelling agent built for the Gemini Live Agent Challenge. This agent crafts immersive narratives using Gemini 2.0 Flash and illustrates them in real-time with Imagen 3.

## 🌟 Features

- **Interleaved Narratives**: Gemini generates a rich story and automatically inserts image generation markers.
- **Typewriter Streaming**: The story feels alive as it's typed out char-by-char with natural rhythms.
- **Animated Shimmers**: Large, animated placeholders maintain layout during image generation.
- **Imagen 3 Integration**: Detailed visual prompts are sent to Imagen 3 (Vertex AI) for cinematic illustrations.
- **Editorial UI**: A professional dual-panel reader with a classic book-like feel.

---

## 🚀 Local Setup

### 1. Prerequisites

- Python 3.11+
- A Google Cloud Project with Vertex AI enabled.

### 2. Configuration

Create a `backend/.env` file:

```env
GOOGLE_API_KEY=your_genai_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### 3. Install & Run

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start the server
python backend/main.py
```

Visit `http://localhost:8000` in your browser.

---

## ☁️ Deployment to Google Cloud Run

We use a containerized approach with Cloud Build for a seamless CI/CD experience.

### 1. Initial Setup (One-time)

Run these commands to authenticate and set your project:

```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

### 2. Run Automation Script

We provided a script that enables APIs, sets up IAM, and deploys the service:

```bash
chmod +x deploy.sh
./deploy.sh
```

### ⚠️ Manual IAM Configuration

If you prefer manual setup, ensure your Cloud Run service account has these roles:

- `roles/aiplatform.user`
- `roles/ml.developer`

### 🌐 Frontend URL Update

The Dockerfile is configured to serve the frontend directly. If you host the frontend separately, ensure `frontend/index.html` references your Cloud Run URL in the `fetch()` call.
