# Deploying Live for $0/month (Hugging Face Spaces + Vercel)

This guide deploys the **PyTorch + FastAPI forensic backend** on **Hugging Face Spaces** (free 2 vCPU / **16 GB RAM** Docker container) and the **Next.js forensic dashboard** on **Vercel** (free Hobby tier).

---

## Step 1: Deploy Backend API to Hugging Face Spaces (Free 16 GB RAM)

1. Sign in at https://huggingface.co/new-space and create a new Space:
   - **Space name:** `ai-forensics-inspector-api`
   - **License:** MIT
   - **SDK:** Select **Docker** → **Blank**
   - **Hardware:** **CPU basic — 2 vCPU • 16 GB RAM • Free**
   - **Visibility:** Public (required so your Vercel frontend can reach the API without auth headers)

2. Push your repository to your new Hugging Face Space (replace `<YOUR_HF_USERNAME>` with your HF username):
   ```bash
   cd /Users/macbook/mini_project
   git remote add hf https://huggingface.co/spaces/<YOUR_HF_USERNAME>/ai-forensics-inspector-api
   ```
   *(Hugging Face Spaces uses a YAML header in `README.md` to detect the Docker SDK. Create a lightweight Space branch or add the HF header directly inside the Space's `README.md` via the HF web UI:)*

   In your Hugging Face Space → **Files** → edit `README.md` so the top has:
   ```yaml
   ---
   title: AI-Image & Deepfake Forensics API
   emoji: 🔍
   colorFrom: blue
   colorTo: indigo
   sdk: docker
   app_port: 7860
   pinned: false
   license: mit
   ---
   ```

   Then push the pre-configured `hf-space` branch to Hugging Face:
   ```bash
   git push hf hf-space:main
   ```

3. Wait ~3–5 minutes for Hugging Face to build the Docker image (it pre-caches `Organika/sdxl-detector` during build!).
4. Verify your live backend URL:
   - **Health Check:** `https://<YOUR_HF_USERNAME>-ai-forensics-inspector-api.hf.space/api/health`
   - **Swagger Docs:** `https://<YOUR_HF_USERNAME>-ai-forensics-inspector-api.hf.space/docs`

---

## Step 2: Deploy Frontend Dashboard to Vercel (Free Hobby Tier)

1. Go to https://vercel.com/new and import your GitHub repository:
   `garv2214/AI-Image-Deepfake-Forensics-Inspector`
2. Configure the project settings:
   - **Framework Preset:** `Next.js` (auto-detected)
   - **Root Directory:** Click **Edit** and select **`frontend`**
3. Add **Environment Variable**:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://<YOUR_HF_USERNAME>-ai-forensics-inspector-api.hf.space` *(no trailing slash)*
4. Click **Deploy**.

Within ~60 seconds, Vercel will give you a live HTTPS URL (e.g., `https://ai-image-deepfake-forensics-inspector.vercel.app`) connected directly to your 4-layer PyTorch backend!

---

## Optional: Test the Docker Container Locally Before Pushing

```bash
docker build -t forensics-api .
docker run -p 7860:7860 forensics-api
# Open http://localhost:7860/docs
```

---

## Troubleshooting Tips

- **First request after 48h idle (HF Free Tier):** Free HF Spaces sleep after 48 hours of inactivity and wake up automatically in ~15–20 seconds when visited. Because our `Dockerfile` pre-caches `Organika/sdxl-detector` inside the image, wake-up never re-downloads weights.
- **CORS:** The FastAPI backend already enables cross-origin requests from your Vercel domain out of the box.
- **Swap AI Model:** Set `FORENSICS_HF_MODEL_ID` in HF Space Settings → Variables if you want to deploy a different Hugging Face classifier.
