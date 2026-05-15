"""
AI Engine Entry Point — Production Multi-Camera Processing
Fetches cameras from backend API, processes via go2rtc RTSP, pushes results back.
Integrated with ai_engine processors: color analysis, OCR, fire detection.
"""

import os
import sys
import time
import signal
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import torch
import httpx
from ultralytics import YOLO
from datetime import datetime, timezone

from ai_engine.utils.color_analyzer import ColorAnalyzer
from ai_engine.config import (
    NUM_COLORS_PERSON, NUM_COLORS_VEHICLE, VEHICLE_CLASSES as AI_VEHICLE_CLASSES,
    CROPPED_DATA_DIR,
)

# Configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://cam-backend:8001")
GO2RTC_HOST = os.getenv("GO2RTC_URL", "go2rtc-server")
GO2RTC_RTSP_PORT = int(os.getenv("GO2RTC_RTSP_PORT", "8554"))
API_KEY = os.getenv("API_KEY", "")
MAX_CAMERAS = int(os.getenv("MAX_CAMERAS", "12"))
SKIP_FRAMES = int(os.getenv("SKIP_FRAMES", "3"))
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.5"))
PERSON_CONF_THRESHOLD = float(os.getenv("PERSON_CONF_THRESHOLD", "0.3"))
HEARTBEAT_INTERVAL = 30
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

# OCR toggle (disable if PaddleOCR not available)
USE_OCR = os.getenv("USE_OCR", "true").lower() == "true"

# Full frame mode — save original frame alongside crop
FULL_FRAME_MODE = os.getenv("FULL_FRAME_MODE", "false").lower() == "true"
FULL_FRAME_INTERVAL = 2.0  # min seconds between full frame saves per camera
_last_full_frame: dict = {}  # cam_id -> {"ts": float, "path": str}

# Global JWT token
_jwt_token = ""

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("ai-engine")

# Graceful shutdown
shutdown_event = threading.Event()


def handle_signal(sig, frame):
    log.info("⏹  Shutdown signal received")
    shutdown_event.set()


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Color analyzers (shared across threads, thread-safe since they create new arrays)
person_color_analyzer = ColorAnalyzer(num_colors=NUM_COLORS_PERSON)
vehicle_color_analyzer = ColorAnalyzer(num_colors=NUM_COLORS_VEHICLE)

# Plate reader (lazy init, optional)
plate_reader = None


def init_plate_reader():
    """Initialize PaddleOCR plate reader if available."""
    global plate_reader
    if not USE_OCR:
        log.info("⏩ OCR disabled via USE_OCR=false")
        return
    try:
        from ai_engine.utils.plate_reader import PlateReader
        plate_reader = PlateReader(use_gpu=False)
        log.info("✓ PaddleOCR plate reader initialized (CPU mode)")
    except ImportError:
        log.warning("⚠ PaddleOCR not installed — license plate OCR disabled")
    except Exception as e:
        log.warning(f"⚠ Plate reader init failed: {e}")


def load_models():
    """Load YOLO models with GPU fallback."""
    device = 0 if torch.cuda.is_available() else "cpu"
    if device == 0:
        log.info(f"✓ GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB)")
    else:
        log.warning("⚠ No GPU — running on CPU (slow)")

    def _load(primary, fallback, label):
        path = primary if os.path.exists(primary) else fallback
        log.info(f"  Loading {label}: {path}")
        model = YOLO(path)
        if device == 0:
            model.to(device)
        return model

    models = {
        "pose": _load("ai_engine/models/yolo11s-pose.pt", "yolov8n-pose.pt", "Person/Pose"),
        "object": _load("ai_engine/models/yolo11s.pt", "yolov8n.pt", "Vehicle/Object"),
    }
    log.info(f"✓ {len(models)} models loaded on {'GPU' if device == 0 else 'CPU'}")
    return models


def login():
    """Login to backend and get JWT token."""
    global _jwt_token
    try:
        r = httpx.post(f"{BACKEND_URL}/api/auth/login", json={
            "username": ADMIN_USER, "password": ADMIN_PASS
        }, timeout=10)
        r.raise_for_status()
        _jwt_token = r.json().get("access_token", "")
        log.info(f"✓ Authenticated as {ADMIN_USER}")
        return True
    except Exception as e:
        log.error(f"✗ Login failed: {e}")
        return False


def _auth_headers():
    return {"Authorization": f"Bearer {_jwt_token}"} if _jwt_token else {}


def fetch_cameras():
    """Fetch active cameras from backend API."""
    try:
        r = httpx.get(f"{BACKEND_URL}/api/cameras", headers=_auth_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
        cameras = data.get("data", data.get("cameras", data.get("items", [])))
        active = [c for c in cameras if c.get("is_active", True)]
        log.info(f"✓ Fetched {len(active)} active cameras from backend")
        return active[:MAX_CAMERAS]
    except Exception as e:
        log.error(f"✗ Failed to fetch cameras: {e}")
        return []


def push_results(camera_id: str, frame_index: int, persons: list, vehicles: list):
    """Push detection results to backend API."""
    ts = datetime.now(timezone.utc).isoformat()

    try:
        with httpx.Client(timeout=10, headers=_auth_headers()) as client:
            if persons:
                client.post(f"{BACKEND_URL}/api/ai/persons", json={
                    "camera_id": camera_id,
                    "frame_index": frame_index,
                    "timestamp": ts,
                    "persons": persons,
                })

            if vehicles:
                client.post(f"{BACKEND_URL}/api/ai/vehicles", json={
                    "camera_id": camera_id,
                    "frame_index": frame_index,
                    "timestamp": ts,
                    "vehicles": vehicles,
                })
    except Exception as e:
        log.debug(f"Push error ({camera_id}): {e}")


def push_heartbeat(camera_ids: list):
    """Send heartbeat to backend."""
    try:
        httpx.post(f"{BACKEND_URL}/api/ai/heartbeat", json={
            "status": "running",
            "cameras_processing": camera_ids,
            "fps_avg": 0,
            "gpu_usage_percent": 0,
            "models_loaded": ["yolo-pose", "yolo-object", "color-analyzer", "plate-ocr"],
        }, headers=_auth_headers(), timeout=5)
    except Exception:
        pass


# COCO vehicle class IDs
VEHICLE_CLASSES = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def _crop_region(frame: np.ndarray, bbox: list) -> np.ndarray | None:
    """Safely crop a bounding box region from a frame."""
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]
    x1 = max(0, min(x1, w))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h))
    y2 = max(0, min(y2, h))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def _format_colors(color_list: list | None) -> list:
    """Convert ColorAnalyzer output to JSON-serializable format matching backend ColorInfo schema."""
    if not color_list:
        return []
    return [{"rank": c.get("rank", i+1), "name": c["name"], "rgb": list(c["rgb"])} for i, c in enumerate(color_list)]


def _analyze_person_attributes(frame: np.ndarray, bbox: list) -> dict:
    """Analyze person attributes: crop image, detect clothing colors."""
    crop = _crop_region(frame, bbox)
    if crop is None or crop.size == 0:
        return {}

    h, w = crop.shape[:2]
    if h < 20 or w < 10:
        return {}

    attributes = {}

    # Upper body (shirt) — top 50%
    upper = crop[:int(h * 0.5), :]
    shirt_colors = person_color_analyzer.analyze(upper, "shirt")
    attributes["shirt_colors"] = _format_colors(shirt_colors)

    # Lower body (pants) — bottom 50%
    lower = crop[int(h * 0.5):, :]
    pants_colors = person_color_analyzer.analyze(lower, "pants")
    attributes["pants_colors"] = _format_colors(pants_colors)

    # Head (hair) — top 25%
    head = crop[:int(h * 0.25), :]
    hair_colors = person_color_analyzer.analyze(head, "hair")
    attributes["hair_colors"] = _format_colors(hair_colors)

    return attributes


def _analyze_vehicle(frame: np.ndarray, bbox: list, vehicle_type: str) -> tuple:
    """Analyze vehicle: color + license plate OCR."""
    crop = _crop_region(frame, bbox)
    if crop is None or crop.size == 0:
        return [], None

    # Color analysis
    colors = vehicle_color_analyzer.analyze(crop, vehicle_type)
    formatted_colors = _format_colors(colors)

    # License plate OCR (only for car/truck/bus)
    plate_info = None
    if plate_reader and vehicle_type in ("car", "truck", "bus"):
        try:
            plate_info = plate_reader.read_plate(crop)
        except Exception:
            pass

    return formatted_colors, plate_info


def _save_crop(crop_img: np.ndarray, category: str, identifier: str) -> str:
    """Save cropped detection image to disk."""
    try:
        save_dir = CROPPED_DATA_DIR / category
        save_dir.mkdir(parents=True, exist_ok=True)
        path = save_dir / f"{identifier}.jpg"
        cv2.imwrite(str(path), crop_img)
        return str(path)
    except Exception:
        return ""


def _save_full_frame(frame: np.ndarray, cam_id: str, frame_count: int) -> str:
    """Save full camera frame (rate-limited). Returns path ONLY when freshly saved
    to guarantee bbox-frame alignment."""
    if not FULL_FRAME_MODE:
        return ""
    now = time.time()
    last = _last_full_frame.get(cam_id, {"ts": 0})
    if now - last["ts"] < FULL_FRAME_INTERVAL:
        return ""  # Don't return stale path — bbox would mismatch
    try:
        save_dir = CROPPED_DATA_DIR / "full_frames"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{cam_id}_{frame_count}.jpg"
        cv2.imwrite(str(save_dir / filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        rel_path = str(CROPPED_DATA_DIR / "full_frames" / filename)
        _last_full_frame[cam_id] = {"ts": now, "path": rel_path}
        return rel_path
    except Exception:
        return ""


def process_camera(camera: dict, models: dict):
    """Process a single camera stream in its own thread."""
    cam_id = camera.get("camera_id", "unknown")
    rtsp_url = f"rtsp://{GO2RTC_HOST}:{GO2RTC_RTSP_PORT}/{cam_id}"

    log.info(f"📷 [{cam_id}] Connecting: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        log.error(f"✗ [{cam_id}] Cannot open stream")
        return

    log.info(f"✓ [{cam_id}] Stream connected")

    frame_count = 0
    fps_start = time.time()
    fps_count = 0
    last_push = 0

    try:
        while not shutdown_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.5)
                cap.release()
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue

            frame_count += 1

            # Log frame resolution once on first processed frame
            if frame_count == 1:
                h0, w0 = frame.shape[:2]
                log.info(f"[{cam_id}] 📐 Stream resolution: {w0}x{h0}")

            # Skip frames for performance
            if frame_count % SKIP_FRAMES != 0:
                continue

            # Use full resolution frame (no resize)
            proc_frame = frame

            persons = []
            vehicles = []

            # Person detection + attribute analysis
            try:
                pose_results = models["pose"].track(
                    proc_frame, persist=True, conf=PERSON_CONF_THRESHOLD, verbose=False
                )
                if pose_results and pose_results[0].boxes:
                    for i, box in enumerate(pose_results[0].boxes):
                        conf = float(box.conf)
                        track_id = int(box.id) if box.id is not None else -(i + 1)
                        if conf >= PERSON_CONF_THRESHOLD:
                            bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()

                            # Analyze attributes (colors) on the full-res frame
                            attributes = _analyze_person_attributes(frame, bbox)

                            if attributes:
                                log.info(f"[{cam_id}] 🎨 Person t{track_id} attrs: shirt={attributes.get('shirt_colors', [])[:1]}")
                            else:
                                log.info(f"[{cam_id}] ⚠ Person t{track_id} bbox={bbox} — attrs empty (too small?)")

                            # Save crop
                            crop = _crop_region(frame, bbox)
                            crop_path = ""
                            if crop is not None:
                                crop_path = _save_crop(crop, "persons", f"{cam_id}_p{track_id}_{frame_count}")

                            persons.append({
                                "track_id": track_id,
                                "confidence": round(conf, 3),
                                "bbox": bbox,
                                "attributes": attributes or {},
                                "image_path": crop_path,
                            })
            except Exception as e:
                log.debug(f"[{cam_id}] Pose error: {e}")

            # Vehicle detection + color + OCR
            try:
                obj_results = models["object"].predict(
                    proc_frame, conf=CONF_THRESHOLD, verbose=False
                )
                if obj_results and obj_results[0].boxes:
                    for box in obj_results[0].boxes:
                        cls_id = int(box.cls)
                        if cls_id in VEHICLE_CLASSES:
                            conf = float(box.conf)
                            bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                            vehicle_type = VEHICLE_CLASSES[cls_id]

                            # Analyze color + OCR on original frame
                            colors, plate_info = _analyze_vehicle(frame, bbox, vehicle_type)

                            # Save crop
                            crop = _crop_region(frame, bbox)
                            crop_path = ""
                            if crop is not None:
                                crop_path = _save_crop(crop, "vehicles", f"{cam_id}_v{cls_id}_{frame_count}")

                            vehicles.append({
                                "track_id": -1,
                                "vehicle_type": vehicle_type,
                                "confidence": round(conf, 3),
                                "bbox": bbox,
                                "license_plate": plate_info.get("text") if plate_info else None,
                                "colors": colors,
                                "image_path": crop_path,
                            })
            except Exception as e:
                log.debug(f"[{cam_id}] Object error: {e}")

            # Save full frame ONLY when detections exist — guarantees bbox-frame sync
            if persons or vehicles:
                full_frame_path = _save_full_frame(frame, cam_id, frame_count)

                # Attach full_frame_path to all detections from THIS frame
                if full_frame_path:
                    for p in persons:
                        p["attributes"]["full_frame_path"] = full_frame_path
                    for v in vehicles:
                        if v.get("attributes"):
                            v["attributes"]["full_frame_path"] = full_frame_path
                        else:
                            v["attributes"] = {"full_frame_path": full_frame_path}

            # Push results (throttle: max once per second)
            now = time.time()
            if (persons or vehicles) and (now - last_push) >= 1.0:
                push_results(cam_id, frame_count, persons, vehicles)
                last_push = now

            # FPS logging
            fps_count += 1
            elapsed = time.time() - fps_start
            if elapsed >= 30:
                fps = fps_count / elapsed
                log.info(
                    f"📊 [{cam_id}] {fps:.1f} FPS | "
                    f"👤 {len(persons)} persons | 🚗 {len(vehicles)} vehicles"
                )
                fps_count = 0
                fps_start = time.time()

    except Exception as e:
        log.error(f"✗ [{cam_id}] Fatal: {e}")
    finally:
        cap.release()
        log.info(f"⏹ [{cam_id}] Stream closed")


def main():
    log.info("=" * 60)
    log.info("🚀 AI Engine — Multi-Camera Production Mode")
    log.info("   + Color Analysis | + License Plate OCR")
    log.info("=" * 60)

    # Load models
    models = load_models()

    # Initialize plate reader (optional)
    init_plate_reader()

    # Authenticate with backend
    for attempt in range(5):
        if login():
            break
        log.warning(f"Login attempt {attempt+1}/5 failed, retrying in 10s...")
        time.sleep(10)

    # Fetch cameras
    cameras = fetch_cameras()
    if not cameras:
        log.error("✗ No cameras found. Retrying in 30s...")
        time.sleep(30)
        cameras = fetch_cameras()
        if not cameras:
            log.error("✗ Still no cameras. Exiting.")
            sys.exit(1)

    camera_ids = [c["camera_id"] for c in cameras]
    log.info(f"🎯 Processing {len(cameras)} cameras: {camera_ids}")

    # Start heartbeat thread
    def heartbeat_loop():
        while not shutdown_event.is_set():
            push_heartbeat(camera_ids)
            shutdown_event.wait(HEARTBEAT_INTERVAL)

    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

    # Process cameras concurrently (one thread per camera)
    with ThreadPoolExecutor(max_workers=MAX_CAMERAS, thread_name_prefix="cam") as pool:
        futures = []
        for cam in cameras:
            f = pool.submit(process_camera, cam, models)
            futures.append(f)
            time.sleep(0.5)  # Stagger connections

        log.info(f"✓ All {len(futures)} camera threads started")

        # Wait for shutdown
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            shutdown_event.set()

    log.info("✓ AI Engine shutdown complete")


if __name__ == "__main__":
    main()
