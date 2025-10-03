## Sharko

An end-to-end project for predicting and visualizing shark presence and habitat using NASA/Copernicus-derived features, a FastAPI backend with ML models, a React + Vite frontend with Mapbox visualizations and 3D storytelling, and a companion RAG microservice that answers questions about the project.

## Live Link: https://sharko-omega.vercel.app/

## Presentation Video: https://drive.google.com/file/d/1IsNZZ3q8TSQd3eiAo95H24Cfs7m0ztZB/view?usp=sharing

### Monorepo Structure

- `frontend/`: React 18 + TypeScript + Vite app with Tailwind CSS. Renders prediction polygons from the backend and provides a cinematic, multi-chapter experience plus an AI assistant UI.
- `sharko-api/`: FastAPI service exposing prediction endpoints backed by pre-trained models (`joblib`). Returns GeoJSON suitable for map overlays.
- `sharo-rag-agent/`: FastAPI RAG service using LangChain + Chroma + sentence-transformers and Gemini to answer project questions based on local docs.
- `dataset & model/`: Data processing scripts, notebooks, and documentation for dataset creation and model training.

---

## Quickstart

You can run each service independently. Default local ports below can be changed as you wish.

### Prerequisites

- Node.js 18+ and npm (or pnpm/yarn) for `frontend`
- Python 3.10+ for `sharko-api` and `sharo-rag-agent`
- Mapbox access token (only if you replace the embedded token in `frontend`)
- Optional: `uvicorn`, `virtualenv`

---

## Frontend (React + Vite)

Path: `frontend/`

Key technologies:

- React 18, TypeScript, Vite
- Tailwind CSS
- Mapbox GL JS
- React Router v7

Install and run (Windows PowerShell):

```bash
cd frontend
npm install
npm run dev
```

Build:

```bash
npm run build
npm run preview
```

Notes:

- The Mapbox token is currently hardcoded in `frontend/src/components/Mapbox.tsx` (`accessToken`). For production, you should use an environment variable or a proxy.
- The app fetches prediction data from the API endpoints. In the current code, production URLs point to a Hugging Face Space (e.g., `https://midul914-sharko-api.hf.space`). For local development you can update these to your local API address (e.g., `http://localhost:8000`).

Routes:

- `/` renders the video hero chapters and the map view (switchable)
- `/tag` shows the proposed sensor/tag design visualization

---

## Backend API (FastAPI)

Path: `sharko-api/`

Purpose: Serve prediction endpoints and return GeoJSON for presence and habitat polygons.

Key files:

- `app.py`: FastAPI app with routes:
  - `GET /` health banner
  - `GET /health` loads models and reports availability
  - `GET /predict/presence?date=YYYY-MM-DD` returns presence polygons (GeoJSON in `presence_geojson_data`)
  - `GET /predict/habitat?date=YYYY-MM-DD&shark_name=Great%20White` returns habitat polygons (GeoJSON in `habitat_geojson_data`)
  - `GET /predict/location?lat=..&lon=..&date=YYYY-MM-DD` returns a single-point prediction with features
- `index.py`: Model loading and prediction logic (imported by `app.py`)
- `models/*.joblib`: Pretrained estimators
- `requirements.txt`: Python dependencies (FastAPI, Geo stack, sklearn, LightGBM, etc.)

Run locally (Windows PowerShell):

```bash
cd "sharko-api"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Model assets:

- Ensure the required `.joblib` files exist under `sharko-api/models/`. If you host them elsewhere, update the load paths in `index.py` accordingly.

CORS:

- CORS is permissive by default (`allow_origins=["*"]`). For production, restrict to your frontend origin.

---

## RAG Agent (FastAPI + LangChain)

Path: `sharo-rag-agent/`

Purpose: Provide `POST /ask` to answer questions about the project using a local knowledge base and Gemini.

Data sources:

- `sharo-rag-agent/data/{frontend.txt, backend.txt, dataset.txt, model_traning.txt}` are loaded, chunked, and embedded into a local Chroma store.

Environment:

- Requires `GOOGLE_API_KEY` in environment (Gemini)

Install and run:

```bash
cd "sharo-rag-agent"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:GOOGLE_API_KEY = "YOUR_KEY_HERE"  # PowerShell
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

Request example:

```bash
curl -X POST http://localhost:8010/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"context\": [], \"question\": \"How do predictions flow to the frontend?\"}"
```

---

## Dataset & Model

Path: `dataset & model/`

Contains notebooks and scripts to build the dataset, engineer features, and train/validate models. Notable items:

- `Model Codes/Sharko.ipynb`: Notebook for model training and evaluation
- Various scripts to assemble SST/SSH/Chlorophyll inputs and generate final datasets
- A comprehensive README with the research narrative and architecture overview

This folder is not an executable service; use it for research and reproducibility.

---

## Local Integration Tips

- If running `sharko-api` locally, update the fetch URLs in `frontend/src/components/Mapbox.tsx` to point to `http://localhost:8000` endpoints.
- Place your model `.joblib` files in `sharko-api/models/` and ensure `index.py` references are correct.
- Swap the hardcoded Mapbox token in `Mapbox.tsx` for an environment-driven approach before production.

---

## Deployment

Options:

- Frontend: Any static host (Netlify, Vercel, Cloudflare). The sample frontend README references a Netlify deployment.
- Backend: Hugging Face Spaces, Fly.io, Render, or any VM/container platform.
- RAG Agent: Similar to backend; requires `GOOGLE_API_KEY` and persistent/ephemeral storage for Chroma.

Docker: Both `sharko-api` and `sharo-rag-agent` include `Dockerfile`s you can adapt for your infra.

---

## Troubleshooting

- Empty polygons or errors in the map:
  - Check API availability (`GET /health`).
  - Verify date parameters produce valid predictions for your model domain.
  - Inspect browser console for CORS or network errors.
- Model loading errors:
  - Verify `.joblib` file names and paths under `sharko-api/models/`.
  - Ensure versions in `requirements.txt` match training environment where needed.
- RAG errors:
  - Ensure all text files in `sharo-rag-agent/data/` are present and UTF-8 or Latin-1 decodable.
  - Set `GOOGLE_API_KEY` and confirm network egress is allowed.

---
