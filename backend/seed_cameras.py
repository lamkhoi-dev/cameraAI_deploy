"""Seed 10 cameras (Batch 1) into the database."""

import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, ".")

from database import async_session, init_db
from models.camera import Camera

BATCH_1_CAMERAS = [
    {
        "camera_id": "cam_01",
        "name": "Sảnh A",
        "location": "Tầng 1 - Sảnh A",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.127:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": True,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_02",
        "name": "Sảnh B",
        "location": "Tầng 1 - Sảnh B",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.207:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": True,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_05",
        "name": "Đường Tự do",
        "location": "Ngoài trời - Đường Tự do",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.4:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": True,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_07",
        "name": "Sảnh văn phòng",
        "location": "Tầng 1 - Sảnh văn phòng",
        "stream_url": "rtsp://admin:admin@192.168.1.31:554/cam/realmonitor?channel=1&subtype=0",
        "brand": "Pana+Dahua",
        "ai_detect_person": True,
        "ai_detect_vehicle": False,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_10",
        "name": "Nhìn lối ra sảnh C",
        "location": "Tầng 1 - Sảnh C",
        "stream_url": "rtsp://admin:admin@192.168.1.33:554/cam/realmonitor?channel=1&subtype=0",
        "brand": "Pana+Dahua",
        "ai_detect_person": True,
        "ai_detect_vehicle": True,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_11",
        "name": "B2 nhìn dốc T1 xuống hầm",
        "location": "Hầm B2 - Dốc xuống",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.201:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": True,
        "ai_detect_fire": True,
    },
    {
        "camera_id": "cam_12",
        "name": "Cửa BQL nhìn cửa TM B2",
        "location": "Hầm B2 - BQL",
        "stream_url": "rtsp://admin:admin@192.168.1.192:554/cam/realmonitor?channel=1&subtype=0",
        "brand": "Pana+Dahua",
        "ai_detect_person": True,
        "ai_detect_vehicle": False,
        "ai_detect_fire": False,
    },
    {
        "camera_id": "cam_16",
        "name": "Sân vườn",
        "location": "Ngoài trời - Sân vườn",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.128:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": False,
        "ai_detect_fire": True,
    },
    {
        "camera_id": "cam_20",
        "name": "Sạc pin Lithium",
        "location": "Khu vực sạc pin",
        "stream_url": "rtsp://admin:admin@192.168.1.2:554/cam/realmonitor?channel=1&subtype=0",
        "brand": "Pana+Dahua",
        "ai_detect_person": False,
        "ai_detect_vehicle": False,
        "ai_detect_fire": True,
    },
    {
        "camera_id": "cam_21",
        "name": "Thang máy cư dân 1",
        "location": "Thang máy - Cư dân 1",
        "stream_url": "rtsp://admin:abcd1357@192.168.1.234:554/Streaming/Channels/101",
        "brand": "Hikvision",
        "ai_detect_person": True,
        "ai_detect_vehicle": False,
        "ai_detect_fire": False,
    },
]


async def seed():
    await init_db()

    async with async_session() as db:
        for cam_data in BATCH_1_CAMERAS:
            result = await db.execute(
                select(Camera).where(Camera.camera_id == cam_data["camera_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ⏭ {cam_data['camera_id']} ({cam_data['name']}) — already exists")
                continue

            camera = Camera(
                camera_id=cam_data["camera_id"],
                name=cam_data["name"],
                location=cam_data["location"],
                stream_url=cam_data["stream_url"],
                protocol="rtsp",
                brand=cam_data["brand"],
                fps=25,
                go2rtc_stream_name=cam_data["camera_id"],
                ai_detect_person=cam_data["ai_detect_person"],
                ai_detect_vehicle=cam_data["ai_detect_vehicle"],
                ai_detect_fire=cam_data["ai_detect_fire"],
            )
            db.add(camera)
            layers = []
            if cam_data["ai_detect_person"]:
                layers.append("👤")
            if cam_data["ai_detect_vehicle"]:
                layers.append("🚗")
            if cam_data["ai_detect_fire"]:
                layers.append("🔥")
            print(f"  ✅ {cam_data['camera_id']} ({cam_data['name']}) — {' '.join(layers)}")

        await db.commit()
        print(f"\n{'='*50}")
        print(f"Seeded {len(BATCH_1_CAMERAS)} cameras (Batch 1)")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(seed())
