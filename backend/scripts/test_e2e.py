"""End-to-end smoke test for the backend display flow.

Usage: run this locally when backend is running (uvicorn) on default host:port.
It will:
 - create a tiny JPEG into the backend crops folder
 - login as admin (default seeded user expected)
 - create a camera via API
 - POST an AI persons payload referencing the created crop
 - GET the display_image endpoint and verify an AI image result is returned

Adjust `BASE_URL` if your backend runs on a different host/port.
"""
import base64
import io
import json
import os
from datetime import datetime

import requests
from PIL import Image

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def make_test_image(path: str):
    im = Image.new("RGB", (320, 240), (255, 0, 0))
    im.save(path, format="JPEG")


def login(username: str, password: str):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def create_camera(token: str, camera_id: str):
    payload = {
        "camera_id": camera_id,
        "name": "e2e-test-camera",
        "stream_url": "rtsp://example.local/test",
        "display_interval_seconds": 3,
        "fallback_seconds": 3,
    }
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/api/cameras", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()


def post_persons(token: str, camera_id: str, image_path: str):
    payload = {
        "camera_id": camera_id,
        "timestamp": datetime.utcnow().isoformat(),
        "persons": [
            {
                "track_id": 1,
                "confidence": 0.98,
                "bbox": [10, 10, 100, 200],
                "image_path": os.path.basename(image_path),
            }
        ],
    }
    r = requests.post(f"{BASE_URL}/api/ai/persons", json=payload)
    r.raise_for_status()
    return r.json()


def get_display(camera_id: str):
    r = requests.get(f"{BASE_URL}/api/cameras/{camera_id}/display_image")
    return r


def main():
    # Prepare image in backend crops dir
    crops_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cropped_data")
    os.makedirs(crops_dir, exist_ok=True)
    img_name = "e2e_person_test.jpg"
    img_path = os.path.join(crops_dir, img_name)
    make_test_image(img_path)

    print("Created test image:", img_path)

    token = login("admin", "admin123")
    print("Logged in, token len:", len(token))

    camera_id = "e2e_test_cam_1"
    create_camera(token, camera_id)
    print("Created camera", camera_id)

    post_persons(token, camera_id, img_path)
    print("Posted AI persons payload")

    r = get_display(camera_id)
    if r.status_code == 200:
        data = r.json()
        print("Display returned:", data)
        if data.get("type") == "ai":
            print("E2E success: AI image returned")
        else:
            print("E2E warning: expected AI type, got", data.get("type"))
    elif r.status_code == 204:
        print("No image yet (204) — worker may need to run or timings differ")
    else:
        print("Display endpoint returned status", r.status_code, r.text)


if __name__ == "__main__":
    main()
