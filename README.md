PixGonz – Web-Based Image Editing App

PixGonz is a React + FastAPI digital image processing application inspired by Gonzalez & Woods.
It provides phase-wise image enhancement, segmentation, and display-based correction tools with a clean glass-dark UI and theory mapping for learning-based usage.

Features

Phase 1: Brightness & contrast, rotate, grayscale, blur, sharpen, masking

Phase 2: Segmentation, color adjustments, undo/redo

Phase 3: Display-based intensity & saturation correction

Chapter-linked explanations for every feature

Project Structure
/frontend → React UI
/backend → FastAPI server (image processing)

Setup

- Backend (FastAPI)
  cd backend
  python -m venv .venv

# Windows

.venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000

- Frontend (React)
  cd frontend
  npm install
  npm start

Backend: http://127.0.0.1:8000
Frontend: http://localhost:3000

Repo Link

🔗 GitHub: https://github.com/kritik8/pixgonzDIP

Developers
Kritik Jain | Durwesh Tirpude
