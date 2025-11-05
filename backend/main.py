"""FastAPI backend for PixGonz - simple /process endpoint.

Usage:
  uvicorn main:app --reload --port 8000

Endpoint expects multipart form data with fields:
- image: file
- phase: str (e.g., "phase1")
- operation: str (e.g., "brightness_increase")

Returns processed image bytes (PNG) or JSON error.
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

from image_utils import (
    process_image,
    adjust_brightness,
    adjust_contrast,
    
    rotate_image,
    to_grayscale,
    blur_image,
    sharpen_image,
    apply_mask,
    segmentation_simple,
    color_adjust,
    calibrate_display,
    saturation_correction_autocorrect,
    image_to_bytes,
)
from history_utils import push_state, undo as history_undo, redo as history_redo

app = FastAPI(title="PixGonz Backend - FastAPI")

# Allow local frontends to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process")
async def process(phase: str = Form(...), operation: str = Form(...), image: UploadFile = File(...)):
    """Receive an uploaded image and process it according to phase/operation.

    - phase: a label describing the processing phase (for your app logic)
    - operation: operation name to perform on the image
    - image: uploaded image file

    Returns image bytes (PNG). Change to return URLs if you later store files.
    """
    # Basic validation
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image uploaded")

    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")

    # Do processing (put your per-phase logic in image_utils.process_image)
    try:
        out_img = process_image(img, phase, operation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

    # Prepare response bytes
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")


@app.post('/phase1/brightness')
async def phase1_brightness(image: UploadFile = File(...), value: float = Form(1.0), session_id: str = Form(None)):
    """Adjust brightness. Fields: image(file), value(float), session_id(optional)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = adjust_brightness(img, value)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/contrast')
async def phase1_contrast(image: UploadFile = File(...), value: float = Form(1.0), session_id: str = Form(None)):
    """Adjust contrast. Fields: image(file), value(float)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = adjust_contrast(img, value)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/rotate')
async def phase1_rotate(image: UploadFile = File(...), angle: float = Form(0.0), expand: bool = Form(True), session_id: str = Form(None)):
    """Rotate image. Fields: image(file), angle(float), expand(bool)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = rotate_image(img, angle, expand=expand)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/grayscale')
async def phase1_grayscale(image: UploadFile = File(...), session_id: str = Form(None)):
    """Convert image to grayscale. Fields: image(file), session_id(optional)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = to_grayscale(img)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/blur')
async def phase1_blur(image: UploadFile = File(...), radius: float = Form(2.0), session_id: str = Form(None)):
    """Apply Gaussian blur. Fields: image(file), radius(float)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = blur_image(img, radius=radius)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/sharpen')
async def phase1_sharpen(image: UploadFile = File(...), session_id: str = Form(None)):
    """Apply sharpen. Fields: image(file), session_id(optional)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = sharpen_image(img)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase1/mask')
async def phase1_mask(image: UploadFile = File(...), mask: UploadFile = File(...), session_id: str = Form(None)):
    """Apply mask. Fields: image(file), mask(file)"""
    contents = await image.read()
    mask_contents = await mask.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
        mask_img = Image.open(io.BytesIO(mask_contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open files: {e}")
    out = apply_mask(img, mask_img)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase2/segmentation')
async def phase2_segmentation(image: UploadFile = File(...), method: str = Form('threshold'), threshold: int = Form(128), session_id: str = Form(None)):
    """Simple segmentation. Fields: image(file), method, threshold"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = segmentation_simple(img, method=method, threshold=threshold)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase2/color-adjust')
async def phase2_color_adjust(image: UploadFile = File(...), brightness: float = Form(1.0), contrast: float = Form(1.0), saturation: float = Form(1.0), hue: float = Form(0.0), intensity: float = Form(0.0), session_id: str = Form(None)):
    """Adjust brightness/contrast/saturation/hue/intensity. Fields: image, brightness, contrast, saturation, hue (deg), intensity (percent)"""
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")
    out = color_adjust(img, brightness=brightness, contrast=contrast, saturation=saturation, hue=hue, intensity=intensity)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')


@app.post('/phase2/undo')
async def phase2_undo(session_id: str = Form(...)):
    """Undo: requires session_id"""
    img = history_undo(session_id)
    if img is None:
        raise HTTPException(status_code=404, detail='No undo available')
    return Response(content=image_to_bytes(img), media_type='image/png')


@app.post('/phase2/redo')
async def phase2_redo(session_id: str = Form(...)):
    """Redo: requires session_id"""
    img = history_redo(session_id)
    if img is None:
        raise HTTPException(status_code=404, detail='No redo available')
    return Response(content=image_to_bytes(img), media_type='image/png')


@app.post('/phase3/saturation-correction')
async def phase3_saturation_correction(image: UploadFile = File(...), display_type: str = Form(None), session_id: str = Form(None)):
    """Display-based saturation correction.

    Fields:
    - image: uploaded image file (required)
    - display_type: optional target display type (one of LCD, LED Backlit, OLED, QLED, E-Paper)
    - session_id: optional session id for undo history

    If `display_type` is provided the server applies the calibrated pipeline:
      1. Saturation adjustment according to display type
      2. Gamma correction (gamma=2.2)
      3. Color temperature adjustment to 6500K

    If `display_type` is omitted, the endpoint falls back to the simple
    `saturation_correction_autocorrect` behavior (autocontrast + small boost).
    """
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {e}")

    if display_type:
        try:
            out = calibrate_display(img, display_type)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Calibration error: {e}")
    else:
        out = saturation_correction_autocorrect(img)
    if session_id:
        try:
            push_state(session_id, out)
        except Exception:
            pass
    return Response(content=image_to_bytes(out), media_type='image/png')
