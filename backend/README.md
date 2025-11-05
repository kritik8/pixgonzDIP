# PixGonz Backend

This folder contains a simple starter backend for the PixGonz image editor.

Two options are provided:

- FastAPI implementation (recommended): `main.py`
- Flask alternative: `app_flask.py`

Both use Pillow (PIL) for image operations and a shared `image_utils.py` for processing logic.

Quick setup (PowerShell):

1. Create and activate a venv (PowerShell):

```powershell
python -m venv .venv
# If you see an ExecutionPolicy error, run this first in the same shell:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies (choose one):

- FastAPI:

```powershell
pip install -r requirements-fastapi.txt
```

- Flask:

```powershell
pip install -r requirements-flask.txt
```

3. Run FastAPI (recommended):

```powershell
# from inside backend/
uvicorn main:app --reload --port 8000
```

Then test the endpoint with curl (or use Postman):

```bash
curl -X POST "http://127.0.0.1:8000/process" \
  -F "phase=brightness" \
  -F "operation=increase" \
  -F "image=@/full/path/to/your/image.jpg" --output out.png
```

PowerShell (Invoke-WebRequest / Invoke-RestMethod) can be used too but `curl` is straightforward if available.

Flask run (alternative):

```powershell
python app_flask.py
```

Files in this folder:

- `main.py` - FastAPI server
- `app_flask.py` - Flask alternative server
- `image_utils.py` - image processing functions to expand later
- `requirements-fastapi.txt`, `requirements-flask.txt` - dependency lists

Folder structure example (project root):

```
/project-root
  /frontend   (React app - your current React project)
  /backend    (this folder - Python backend)
```

Notes:

- The `/process` endpoint accepts a form `image` file and form fields `phase` and `operation`.
- Right now the processing functions include simple placeholders for brightness, contrast, segmentation, and display correction. Add new operations inside `image_utils.py`.

## Phase 3: Saturation calibration endpoint

The FastAPI endpoint `/phase3/saturation-correction` accepts an image and an optional `display_type` form field. When `display_type` is provided the server applies a calibrated pipeline:

- Saturation adjustment (per-display mapping)
- Gamma correction (gamma = 2.2)
- Color temperature adjustment to 6500K

Supported `display_type` values: `LCD`, `LED Backlit`, `OLED`, `QLED`, `E-Paper` (case-insensitive aliases allowed).

Examples (curl):

1. Simple autocontrast/autocolor fallback (no display type):

```bash
curl -X POST "http://127.0.0.1:8000/phase3/saturation-correction" \
  -F "image=@/full/path/to/image.jpg" --output out.png
```

2. Calibrated for OLED:

```bash
curl -X POST "http://127.0.0.1:8000/phase3/saturation-correction" \
  -F "image=@/full/path/to/image.jpg" \
  -F "display_type=OLED" --output out_oled.png
```

If an unsupported `display_type` is provided the endpoint responds with HTTP 400 and an explanatory message.
