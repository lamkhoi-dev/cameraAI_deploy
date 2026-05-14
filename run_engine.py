"""
AI Engine Entry Point — Production Multi-Camera Processing
Fetches cameras from backend API, processes via go2rtc RTSP, pushes results back.
"""

import os
import sys
import time
import signal
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import torch
import httpx
from ultralytics import YOLO
from datetime import datetime, timezone

# Configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://cam-backend:8001")
GO2RTC_HOST = os.getenv("GO2RTC_URL", "go2rtc-server")
GO2RTC_RTSP_PORT = int(os.getenv("GO2RTC_RTSP_PORT", "8554"))
API_KEY = os.getenv("API_KEY", "")
MAX_CAMERAS = int(os.getenv("MAX_CAMERAS", "15"))
SKIP_FRAMES = int(os.getenv("SKIP_FRAMES", "3"))
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.5"))
HEARTBEAT_INTERVAL = 30

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


def load_models():
    """Load YOLO models with GPU fallback."""
    device = 0 if torch.cuda.is_available() else "cpu"
    if device == 0:
        log.info(f"✓ GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f}GB)")
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


def fetch_cameras():
    """Fetch active cameras from backend API."""
    try:
        r = httpx.get(f"{BACKEND_URL}/api/cameras", timeout=10)
        r.raise_for_status()
        data = r.json()
        cameras = data.get("cameras", data.get("items", []))
        active = [c for c in cameras if c.get("is_active", True)]
        log.info(f"✓ Fetched {len(active)} active cameras from backend")
        return active[:MAX_CAMERAS]
    except Exception as e:
        log.error(f"✗ Failed to fetch cameras: {e}")
        return []


def push_results(camera_id: str, persons: list, vehicles: list):
    """Push detection results to backend API."""
    ts = datetime.now(timezone.utc).isoformat()

    try:
        with httpx.Client(timeout=10) as client:
            if persons:
                client.post(f"{BACKEND_URL}/api/ai/persons", json={
                    "camera_id": camera_id,
                    "frame_index": 0,
                    "timestamp": ts,
                    "persons": persons,
                })

            if vehicles:
                client.post(f"{BACKEND_URL}/api/ai/vehicles", json={
                    "camera_id": camera_id,
                    "frame_index": 0,
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
            "models_loaded": ["yolo-pose", "yolo-object"],
        }, timeout=5)
    except Exception:
        pass


# COCO vehicle class IDs
VEHICLE_CLASSES = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


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

            # Skip frames for performance
            if frame_count % SKIP_FRAMES != 0:
                continue

            # Resize for faster inference
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (w // 2, h // 2))

            persons = []
            vehicles = []

            # Person detection
            try:
                pose_results = models["pose"].track(
                    small, persist=True, conf=CONF_THRESHOLD, verbose=False
                )
                if pose_results and pose_results[0].boxes:
                    for box in pose_results[0].boxes:
                        conf = float(box.conf)
                        track_id = int(box.id) if box.id is not None else -1
                        if conf >= CONF_THRESHOLD and track_id >= 0:
                            bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                            persons.append({
                                "track_id": track_id,
                                "confidence": round(conf, 3),
                                "bbox": bbox,
                                "attributes": {},
                            })
            except Exception as e:
                log.debug(f"[{cam_id}] Pose error: {e}")

            # Vehicle detection
            try:
                obj_results = models["object"].predict(
                    small, conf=CONF_THRESHOLD, verbose=False
                )
                if obj_results and obj_results[0].boxes:
                    for box in obj_results[0].boxes:
                        cls_id = int(box.cls)
                        if cls_id in VEHICLE_CLASSES:
                            conf = float(box.conf)
                            bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                            vehicles.append({
                                "track_id": -1,
                                "vehicle_type": VEHICLE_CLASSES[cls_id],
                                "confidence": round(conf, 3),
                                "bbox": bbox,
                                "license_plate": None,
                                "colors": [],
                            })
            except Exception as e:
                log.debug(f"[{cam_id}] Object error: {e}")

            # Push results (throttle: max once per second)
            now = time.time()
            if (persons or vehicles) and (now - last_push) >= 1.0:
                push_results(cam_id, persons, vehicles)
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
    log.info("=" * 60)

    # Load models
    models = load_models()

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
