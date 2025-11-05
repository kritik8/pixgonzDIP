"""Flask alternative backend for PixGonz with the same /process endpoint.

Run with:
  python app_flask.py

This is provided so you can pick whichever framework you prefer.
"""
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
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
    saturation_correction_autocorrect,
    image_to_bytes,
)
from history_utils import push_state, undo as history_undo, redo as history_redo

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "PixGonz Backend Running!"

@app.route("/process", methods=["POST"])
def process():
    # phase and operation are sent as form fields
    phase = request.form.get("phase")
    operation = request.form.get("operation")

    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        img = Image.open(file.stream).convert('RGB')
    except Exception as e:
        return jsonify({"error": f"Could not open image: {e}"}), 400

    try:
        out_img = process_image(img, phase, operation)
    except Exception as e:
        return jsonify({"error": f"Processing error: {e}"}), 500

    buf = io.BytesIO()
    out_img.save(buf, format='PNG')
    buf.seek(0)

    # send_file will set appropriate headers for direct download/display
    return send_file(buf, mimetype='image/png', as_attachment=False, download_name='processed.png')


if __name__ == '__main__':
    # debug server for development only
    app.run(host='127.0.0.1', port=5000, debug=True)


@app.route('/phase1/brightness', methods=['POST'])
def phase1_brightness():
    print("phase1_brightness route was called")
    """Adjust brightness.

    Form fields:
    - image: file
    - value: float multiplier (e.g., 1.2)
    - session_id: optional string to store history
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400

    val = request.form.get('value', '1.0')
    try:
        factor = float(val)
    except:
        factor = 1.0

    out = adjust_brightness(img, factor)

    # push to history if provided
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass

    buf = io.BytesIO()
    out.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/contrast', methods=['POST'])
def phase1_contrast():
    """Adjust contrast.

    Fields: image, value (float)
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    val = request.form.get('value', '1.0')
    try:
        factor = float(val)
    except:
        factor = 1.0
    out = adjust_contrast(img, factor)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/rotate', methods=['POST'])
def phase1_rotate():
    """Rotate an image.

    Fields: image, angle (float degrees), expand (optional, true/false)
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    angle = float(request.form.get('angle', '0'))
    expand = request.form.get('expand', 'true').lower() in ('1','true','yes')
    out = rotate_image(img, angle, expand=expand)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/grayscale', methods=['POST'])
def phase1_grayscale():
    """Convert image to grayscale.

    Fields: image, session_id optional
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    out = to_grayscale(img)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/blur', methods=['POST'])
def phase1_blur():
    """Apply Gaussian blur. Fields: image, radius (float)"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    rad = float(request.form.get('radius', '2.0'))
    out = blur_image(img, radius=rad)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/sharpen', methods=['POST'])
def phase1_sharpen():
    """Apply sharpening filter. Fields: image, session_id optional."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    out = sharpen_image(img)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase1/mask', methods=['POST'])
def phase1_mask():
    """Apply a mask file to the uploaded image.

    Fields: image (main), mask (file)
    """
    if 'image' not in request.files or 'mask' not in request.files:
        return jsonify({'error': 'Missing image or mask'}), 400
    f = request.files['image']
    m = request.files['mask']
    try:
        img = Image.open(f.stream).convert('RGB')
        mask_img = Image.open(m.stream)
    except Exception as e:
        return jsonify({'error': f'Could not open files: {e}'}), 400
    out = apply_mask(img, mask_img)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase2/segmentation', methods=['POST'])
def phase2_segmentation():
    """Run a simple segmentation.

    Fields: image, method (optional), threshold (optional)
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    method = request.form.get('method', 'threshold')
    thresh = int(request.form.get('threshold', '128'))
    out = segmentation_simple(img, method=method, threshold=thresh)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase2/color-adjust', methods=['POST'])
def phase2_color_adjust():
    """Adjust brightness/contrast/saturation for Phase 2.

    Fields: image, brightness, contrast, saturation
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    b = float(request.form.get('brightness', '1.0'))
    c = float(request.form.get('contrast', '1.0'))
    s = float(request.form.get('saturation', '1.0'))
    h = float(request.form.get('hue', '0.0'))
    inten = float(request.form.get('intensity', '0.0'))
    out = color_adjust(img, brightness=b, contrast=c, saturation=s, hue=h, intensity=inten)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase2/undo', methods=['POST'])
def phase2_undo():
    """Undo: requires form field session_id. Returns previous image or 404 if none."""
    sid = request.form.get('session_id')
    if not sid:
        return jsonify({'error': 'session_id required for undo'}), 400
    img = history_undo(sid)
    if img is None:
        return jsonify({'error': 'No undo available'}), 404
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase2/redo', methods=['POST'])
def phase2_redo():
    """Redo: requires form field session_id. Returns next image or 404 if none."""
    sid = request.form.get('session_id')
    if not sid:
        return jsonify({'error': 'session_id required for redo'}), 400
    img = history_redo(sid)
    if img is None:
        return jsonify({'error': 'No redo available'}), 404
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/phase3/saturation-correction', methods=['POST'])
def phase3_saturation_correction():
    """Apply a display-based saturation correction.

    Fields: image, session_id optional
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': f'Could not open image: {e}'}), 400
    out = saturation_correction_autocorrect(img)
    sid = request.form.get('session_id')
    if sid:
        try:
            push_state(sid, out)
        except Exception:
            pass
    buf = io.BytesIO(); out.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
