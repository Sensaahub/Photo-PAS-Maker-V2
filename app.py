from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
from rembg import remove, new_session
from PIL import Image, ImageEnhance, ImageOps
import cv2
import numpy as np
import io
import os
import zipfile
import uuid
import json

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "static/results"
MAX_CONTENT_LENGTH = 200 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

UKURAN_FOTO = {
    "2x3": (472, 708),
    "3x4": (708, 944),
    "4x6": (944, 1418),
    "9x16": (1200, 1800)
}

WARNA_BACKGROUND = {
    "merah": (139, 0, 0),
    "biru": (30, 80, 200),
    "putih": (255, 255, 255),
}

session_rembg = new_session("u2net_human_seg")
face_net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "face_detector.caffemodel")


def resize_untuk_proses(image, max_size=1500):
    w, h = image.size
    if max(w, h) <= max_size:
        return image
    if w > h:
        new_w = max_size
        new_h = int(h * max_size / w)
    else:
        new_h = max_size
        new_w = int(w * max_size / h)
    return image.resize((new_w, new_h), Image.LANCZOS)


def deteksi_wajah_mp(image):
    img = np.array(image.convert("RGB"))
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    face_net.setInput(blob)
    detections = face_net.forward()
    best = None
    best_conf = 0.6
    for i in range(detections.shape[2]):
        conf = detections[0, 0, i, 2]
        if conf > best_conf:
            best_conf = conf
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            best = (max(0, x1), max(0, y1), x2 - x1, y2 - y1)
    return best


def hapus_background(image, path_rgba_cache=None):
    if path_rgba_cache and os.path.exists(path_rgba_cache):
        return Image.open(path_rgba_cache).convert("RGBA")
    img_kecil = resize_untuk_proses(image, max_size=1500)
    img_bytes = io.BytesIO()
    img_kecil.save(img_bytes, format="PNG")
    result_bytes = remove(img_bytes.getvalue(), session=session_rembg)
    result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
    if img_kecil.size != image.size:
        result = result.resize(image.size, Image.LANCZOS)
    return result


def color_adjustment(image):
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.05)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)
    return image


def crop_dan_posisikan_dengan_wajah(image_rgba, ukuran, wajah):
    lebar_target, tinggi_target = ukuran
    lebar_asli, tinggi_asli = image_rgba.size

    if wajah is not None:
        fx, fy, fw, fh = wajah
        tinggi_crop = int(fh / 0.35)
        lebar_crop = int(tinggi_crop * lebar_target / tinggi_target)
        if tinggi_crop > tinggi_asli:
            tinggi_crop = tinggi_asli
            lebar_crop = int(tinggi_crop * lebar_target / tinggi_target)
        top = fy - int(tinggi_crop * 0.25)
        left = (fx + fw // 2) - lebar_crop // 2
    else:
        rasio = lebar_target / tinggi_target
        if lebar_asli / tinggi_asli > rasio:
            tinggi_crop = tinggi_asli
            lebar_crop = int(tinggi_asli * rasio)
        else:
            lebar_crop = lebar_asli
            tinggi_crop = int(lebar_asli / rasio)
        left = (lebar_asli - lebar_crop) // 2
        top = 0

    left = max(0, min(left, lebar_asli - lebar_crop))
    top = max(0, min(top, tinggi_asli - tinggi_crop))
    lebar_crop = min(lebar_crop, lebar_asli)
    tinggi_crop = min(tinggi_crop, tinggi_asli)

    init_scale = lebar_target / lebar_crop
    init_offset_x = lebar_target * (lebar_asli - 2 * left - lebar_crop) / (2 * lebar_crop)
    init_offset_y = tinggi_target * (tinggi_asli - 2 * top - tinggi_crop) / (2 * tinggi_crop)

    cropped = image_rgba.crop((left, top, left + lebar_crop, top + tinggi_crop))
    return cropped.resize((lebar_target, tinggi_target), Image.LANCZOS), init_scale, init_offset_x, init_offset_y


def tambah_background(image_rgba, warna):
    background = Image.new("RGBA", image_rgba.size, warna + (255,))
    background.paste(image_rgba, mask=image_rgba.split()[3])
    return background.convert("RGB")


def crop_dengan_params(image_rgba, ukuran, offset_x, offset_y, scale):
    lebar_target, tinggi_target = ukuran
    lebar_asli, tinggi_asli = image_rgba.size
    lebar_scaled = int(lebar_asli * scale)
    tinggi_scaled = int(tinggi_asli * scale)
    image_scaled = image_rgba.resize((lebar_scaled, tinggi_scaled), Image.LANCZOS)
    canvas = Image.new("RGBA", (lebar_target, tinggi_target), (0, 0, 0, 0))
    paste_x = int((lebar_target - lebar_scaled) / 2 + offset_x)
    paste_y = int((tinggi_target - tinggi_scaled) / 2 + offset_y)
    canvas.paste(image_scaled, (paste_x, paste_y), image_scaled)
    return canvas

def crop_photobooth(image_rgba, ukuran):
    lebar_target, tinggi_target = ukuran
    lebar_asli, tinggi_asli = image_rgba.size

    rasio_target = lebar_target / tinggi_target
    rasio_asli = lebar_asli / tinggi_asli

    if rasio_asli > rasio_target:
        tinggi_crop = tinggi_asli
        lebar_crop = int(tinggi_asli * rasio_target)
    else:
        lebar_crop = lebar_asli
        tinggi_crop = int(lebar_asli / rasio_target)

    left = (lebar_asli - lebar_crop) // 2
    top = max(0, (tinggi_asli - tinggi_crop) // 4)

    cropped = image_rgba.crop((left, top, left + lebar_crop, top + tinggi_crop))
    return cropped.resize((lebar_target, tinggi_target), Image.LANCZOS)

def buat_layout_cetak(image, ukuran_key):
    a4_lebar, a4_tinggi = 2480, 3508
    foto_lebar, foto_tinggi = UKURAN_FOTO[ukuran_key]
    margin = 40
    gap = 20
    cols = (a4_lebar - 2 * margin + gap) // (foto_lebar + gap)
    rows = (a4_tinggi - 2 * margin + gap) // (foto_tinggi + gap)
    layout = Image.new("RGB", (a4_lebar, a4_tinggi), (255, 255, 255))
    for row in range(rows):
        for col in range(cols):
            x = margin + col * (foto_lebar + gap)
            y = margin + row * (foto_tinggi + gap)
            if x + foto_lebar <= a4_lebar - margin and y + foto_tinggi <= a4_tinggi - margin:
                layout.paste(image, (x, y))
    return layout


def proses_foto(image, ukuran_key, warna_key, path_rgba_cache=None):
    image = ImageOps.exif_transpose(image)
    image = color_adjustment(image)
    image_rgba = hapus_background(image, path_rgba_cache)

    wajah = deteksi_wajah_mp(image_rgba)
    if wajah is None:
        for angle in [90, 270, 180]:
            rotated = image.rotate(angle, expand=True)
            rotated_rgba = hapus_background(rotated)
            wajah = deteksi_wajah_mp(rotated_rgba)
            if wajah is not None:
                image_rgba = rotated_rgba
                break

    if wajah is None:
        return None, None, None, None

    image_crop, _, _, _ = crop_dan_posisikan_dengan_wajah(image_rgba, UKURAN_FOTO[ukuran_key], wajah)
    image_final = tambah_background(image_crop, WARNA_BACKGROUND[warna_key])
    image_layout = buat_layout_cetak(image_final, ukuran_key)
    return image_final, image_layout, image_crop, image_rgba


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/proses", methods=["POST"])
def proses():
    ukuran_key = request.form.get("ukuran", "3x4")
    warna_key = request.form.get("warna", "merah")
    file = request.files.get("foto")

    if not file:
        return jsonify({"error": "Tidak ada file yang diupload"}), 400

    nama_asli = os.path.splitext(file.filename)[0]
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(RESULT_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    try:
        image = Image.open(file.stream).convert("RGB")
        path_rgba_cache = os.path.join(session_folder, f"{nama_asli}_rgba.png")
        image_final, image_layout, image_crop, image_rgba = proses_foto(image, ukuran_key, warna_key, path_rgba_cache)

        if image_final is None:
            return jsonify({"error": "Wajah tidak terdeteksi"}), 400

        path_final = os.path.join(session_folder, f"{nama_asli}_final.jpg")
        path_layout = os.path.join(session_folder, f"{nama_asli}_layout.jpg")
        path_rgba_crop = os.path.join(session_folder, f"{nama_asli}_rgba_crop.png")

        image_final.save(path_final, "JPEG", quality=100)
        image_layout.save(path_layout, "JPEG", quality=100)
        image_crop.save(path_rgba_crop, "PNG")
        image_rgba.save(path_rgba_cache, "PNG")

        return jsonify({
            "session_id": session_id,
            "nama_asli": nama_asli,
            "foto_final": f"/static/results/{session_id}/{nama_asli}_final.jpg",
            "foto_layout": f"/static/results/{session_id}/{nama_asli}_layout.jpg",
            "foto_rgba_crop": f"/static/results/{session_id}/{nama_asli}_rgba_crop.png",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/proses-adjust", methods=["POST"])
def proses_adjust():
    data = request.json
    session_id = data.get("session_id")
    nama_asli = data.get("nama_asli")
    ukuran_key = data.get("ukuran", "3x4")
    warna_key = data.get("warna", "merah")
    offset_x = float(data.get("offset_x", 0))
    offset_y = float(data.get("offset_y", 0))
    scale = float(data.get("scale", 1.0))

    session_folder = os.path.join(RESULT_FOLDER, session_id)
    path_rgba = os.path.join(session_folder, f"{nama_asli}_rgba_crop.png")

    if not os.path.exists(path_rgba):
        return jsonify({"error": "File tidak ditemukan"}), 404

    try:
        image_rgba = Image.open(path_rgba).convert("RGBA")
        image_crop = crop_dengan_params(image_rgba, UKURAN_FOTO[ukuran_key], offset_x, offset_y, scale)
        image_final = tambah_background(image_crop, WARNA_BACKGROUND[warna_key])
        image_layout = buat_layout_cetak(image_final, ukuran_key)

        path_final = os.path.join(session_folder, f"{nama_asli}_final.jpg")
        path_layout = os.path.join(session_folder, f"{nama_asli}_layout.jpg")
        image_final.save(path_final, "JPEG", quality=100)
        image_layout.save(path_layout, "JPEG", quality=100)

        return jsonify({
            "foto_final": f"/static/results/{session_id}/{nama_asli}_final.jpg?t={uuid.uuid4().hex}",
            "foto_layout": f"/static/results/{session_id}/{nama_asli}_layout.jpg?t={uuid.uuid4().hex}",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/proses-batch", methods=["POST"])
def proses_batch():
    ukuran_key = request.form.get("ukuran", "3x4")
    warna_key = request.form.get("warna", "merah")
    file_zip = request.files.get("foto_zip")

    if not file_zip:
        return jsonify({"error": "Tidak ada file ZIP yang diupload"}), 400

    session_id = str(uuid.uuid4())
    session_folder = os.path.join(RESULT_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    with zipfile.ZipFile(file_zip.stream, "r") as zf:
        nama_file_list = [
            n for n in zf.namelist()
            if n.lower().endswith((".jpg", ".jpeg", ".png"))
            and not n.startswith("__MACOSX")
        ]
        file_data = [(n, zf.read(n)) for n in nama_file_list]

    total = len(file_data)

    def generate():
        hasil = []
        gagal = []

        for i, (nama_file, img_bytes) in enumerate(file_data):
            persen = int((i / total) * 100)
            nama_bersih = os.path.splitext(os.path.basename(nama_file))[0]
            yield f"data: {json.dumps({'type': 'progress', 'persen': persen, 'current': i+1, 'total': total, 'nama': nama_bersih})}\n\n"

            try:
                image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                img_array = np.array(image)
                if img_array.shape[0] < 100 or img_array.shape[1] < 100:
                    gagal.append({"nama": nama_file, "alasan": "Resolusi terlalu rendah"})
                    continue

                path_rgba_cache = os.path.join(session_folder, f"{nama_bersih}_rgba.png")
                image_final, image_layout, image_crop, image_rgba = proses_foto(image, ukuran_key, warna_key, path_rgba_cache)

                if image_final is None:
                    gagal.append({"nama": nama_file, "alasan": "Wajah tidak terdeteksi"})
                    continue

                path_final = os.path.join(session_folder, f"{nama_bersih}_final.jpg")
                path_layout = os.path.join(session_folder, f"{nama_bersih}_layout.jpg")
                path_rgba_crop = os.path.join(session_folder, f"{nama_bersih}_rgba_crop.png")

                image_final.save(path_final, "JPEG", quality=100)
                image_layout.save(path_layout, "JPEG", quality=100)
                image_crop.save(path_rgba_crop, "PNG")
                image_rgba.save(path_rgba_cache, "PNG")

                hasil.append({
                    "nama": nama_bersih,
                    "foto_final": f"/static/results/{session_id}/{nama_bersih}_final.jpg",
                    "foto_layout": f"/static/results/{session_id}/{nama_bersih}_layout.jpg",
                    "foto_rgba_crop": f"/static/results/{session_id}/{nama_bersih}_rgba_crop.png",
                    "session_id": session_id,
                    "ukuran": ukuran_key,
                    "warna": warna_key,
                })

            except Exception as e:
                gagal.append({"nama": nama_file, "alasan": str(e)})

        yield f"data: {json.dumps({'type': 'done', 'persen': 100, 'session_id': session_id, 'hasil': hasil, 'gagal': gagal})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/download-zip/<session_id>")
def download_zip(session_id):
    session_folder = os.path.join(RESULT_FOLDER, session_id)
    if not os.path.exists(session_folder):
        return jsonify({"error": "Session tidak ditemukan"}), 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in os.listdir(session_folder):
            if filename.endswith("_final.jpg"):
                filepath = os.path.join(session_folder, filename)
                nama_download = filename.replace("_final.jpg", ".jpg")
                zf.write(filepath, nama_download)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="hasil_foto.zip")

@app.route("/get-assets")
def get_assets():
    backgrounds = []
    frames = []

    bg_folder = "static/backgrounds"
    for f in sorted(os.listdir(bg_folder)):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            nama = os.path.splitext(f)[0].replace("_", " ").title()
            backgrounds.append({"nama": nama, "file": f, "url": f"/static/backgrounds/{f}"})

    frame_folder = "static/frames"
    for f in sorted(os.listdir(frame_folder)):
        if f.lower().endswith(".png"):
            nama = os.path.splitext(f)[0].replace("_", " ").title()
            frames.append({"nama": nama, "file": f, "url": f"/static/frames/{f}"})

    return jsonify({"backgrounds": backgrounds, "frames": frames})


@app.route("/proses-photobooth", methods=["POST"])
def proses_photobooth():
    ukuran_key = "9x16"
    file = request.files.get("foto")
    bg_file = request.form.get("background")
    frame_file = request.form.get("frame")

    if not file:
        return jsonify({"error": "Tidak ada foto yang diupload"}), 400

    nama_asli = os.path.splitext(file.filename)[0]
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(RESULT_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    try:
        image = Image.open(file.stream).convert("RGB")
        image = ImageOps.exif_transpose(image)
        image = color_adjustment(image)

        path_rgba_cache = os.path.join(session_folder, f"{nama_asli}_rgba.png")
        image_rgba = hapus_background(image, path_rgba_cache)
        image_rgba.save(path_rgba_cache, "PNG")

        wajah = deteksi_wajah_mp(image_rgba)
        if wajah is None:
            for angle in [90, 270, 180]:
                rotated = image.rotate(angle, expand=True)
                rotated_rgba = hapus_background(rotated)
                wajah = deteksi_wajah_mp(rotated_rgba)
                if wajah is not None:
                    image_rgba = rotated_rgba
                    break

        if wajah is None:
            return jsonify({"error": "Wajah tidak terdeteksi"}), 400

        image_crop = crop_photobooth(image_rgba, UKURAN_FOTO[ukuran_key])

        if bg_file:
            bg_path = os.path.join("static/backgrounds", bg_file)
            if os.path.exists(bg_path):
                background = Image.open(bg_path).convert("RGB")
                background = background.resize(UKURAN_FOTO[ukuran_key], Image.LANCZOS)
            else:
                background = Image.new("RGB", UKURAN_FOTO[ukuran_key], (255, 255, 255))
        else:
            background = Image.new("RGB", UKURAN_FOTO[ukuran_key], (255, 255, 255))

        background = background.convert("RGBA")
        background.paste(image_crop, mask=image_crop.split()[3])
        hasil = background.convert("RGB")

        if frame_file:
            frame_path = os.path.join("static/frames", frame_file)
            if os.path.exists(frame_path):
                frame = Image.open(frame_path).convert("RGBA")
                frame = frame.resize(UKURAN_FOTO[ukuran_key], Image.LANCZOS)
                hasil_rgba = hasil.convert("RGBA")
                hasil_rgba.paste(frame, mask=frame.split()[3])
                hasil = hasil_rgba.convert("RGB")

        path_hasil = os.path.join(session_folder, f"{nama_asli}_photobooth.jpg")
        hasil.save(path_hasil, "JPEG", quality=100)

        return jsonify({
            "session_id": session_id,
            "nama_asli": nama_asli,
            "foto_hasil": f"/static/results/{session_id}/{nama_asli}_photobooth.jpg",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload-frame", methods=["POST"])
def upload_frame():
    file = request.files.get("frame")
    if not file:
        return jsonify({"error": "Tidak ada file"}), 400
    if not file.filename.lower().endswith(".png"):
        return jsonify({"error": "Harus file PNG"}), 400

    nama_bersih = str(uuid.uuid4())[:8] + "_" + file.filename.replace(" ", "_")
    path = os.path.join("static/frames", nama_bersih)
    img = Image.open(file.stream).convert("RGBA")
    img = img.resize(UKURAN_FOTO["3x4"], Image.LANCZOS)
    img.save(path, "PNG")

    nama_tampil = os.path.splitext(file.filename)[0].replace("_", " ").title()
    return jsonify({
        "nama": nama_tampil,
        "file": nama_bersih,
        "url": f"/static/frames/{nama_bersih}"
    })

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)
    app.run(debug=True)