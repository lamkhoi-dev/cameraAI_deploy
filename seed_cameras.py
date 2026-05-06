"""Seed 25 cameras from the building camera list."""
import requests
import sys

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"

CAMERAS = [
    {"stt": 1,  "name": "Sảnh A",                          "brand": "Hikvision",  "ip": "192.168.1.127", "user": "admin", "pass": "abcd1357"},
    {"stt": 2,  "name": "Sảnh B",                          "brand": "Hikvision",  "ip": "192.168.1.207", "user": "admin", "pass": "abcd1357"},
    {"stt": 3,  "name": "Sảnh B nhìn bốt",                 "brand": "Hikvision",  "ip": "192.168.1.203", "user": "admin", "pass": "abcd1357"},
    {"stt": 4,  "name": "Sảnh C",                          "brand": "Hikvision",  "ip": "192.168.1.237", "user": "admin", "pass": "abcd1357"},
    {"stt": 5,  "name": "Đường Tự do",                     "brand": "Hikvision",  "ip": "192.168.1.4",   "user": "admin", "pass": "abcd1357"},
    {"stt": 6,  "name": "Sảnh cư dân",                     "brand": "Hikvision",  "ip": "192.168.1.157", "user": "admin", "pass": "abcd1357"},
    {"stt": 7,  "name": "Sảnh văn phòng",                  "brand": "Dahua",      "ip": "192.168.1.31",  "user": "admin", "pass": "admin"},
    {"stt": 8,  "name": "Nhìn Lễ tân + Thang máy",         "brand": "Hikvision",  "ip": "192.168.1.244", "user": "admin", "pass": "abcd1357"},
    {"stt": 9,  "name": "Thang bộ B1 nhìn Thang máy T1",   "brand": "Hikvision",  "ip": "192.168.1.39",  "user": "admin", "pass": "abcd1357"},
    {"stt": 10, "name": "Nhìn lối ra sảnh C",              "brand": "Dahua",      "ip": "192.168.1.33",  "user": "admin", "pass": "admin"},
    {"stt": 11, "name": "B2 nhìn dốc T1 xuống hầm",       "brand": "Hikvision",  "ip": "192.168.1.201", "user": "admin", "pass": "abcd1357"},
    {"stt": 12, "name": "Cửa BQL nhìn cửa TM B2",         "brand": "Dahua",      "ip": "192.168.1.192", "user": "admin", "pass": "admin"},
    {"stt": 13, "name": "Sảnh TM cư dân B2",               "brand": "Hikvision",  "ip": "192.168.1.38",  "user": "admin", "pass": "admin"},
    {"stt": 14, "name": "Bể XLNT nhìn cửa TM CD + VP B2",  "brand": "Hikvision",  "ip": "192.168.1.95",  "user": "admin", "pass": "abcd1357"},
    {"stt": 15, "name": "Sảnh TM văn phòng B2",            "brand": "Dahua",      "ip": "192.168.1.32",  "user": "admin", "pass": "admin"},
    {"stt": 16, "name": "Sân vườn",                        "brand": "Hikvision",  "ip": "192.168.1.128", "user": "admin", "pass": "abcd1357"},
    {"stt": 17, "name": "B3 nhìn cửa thang máy",           "brand": "Dahua",      "ip": "192.168.1.93",  "user": "admin", "pass": "admin"},
    {"stt": 18, "name": "Sảnh TM cư dân B3",               "brand": "Dahua",      "ip": "192.168.1.9",   "user": "admin", "pass": "admin"},
    {"stt": 19, "name": "B3 nhìn sau cửa TM (TL)",         "brand": "Dahua",      "ip": "192.168.1.104", "user": "admin", "pass": "admin"},
    {"stt": 20, "name": "Sạc pin Lithium",                 "brand": "Hikvision",  "ip": "192.168.1.2",   "user": "admin", "pass": "abcd1357"},
    {"stt": 21, "name": "Thang máy cư dân 1",              "brand": "Hikvision",  "ip": "192.168.1.234", "user": "admin", "pass": "abcd1357"},
    {"stt": 22, "name": "Thang máy cư dân 2",              "brand": "Hikvision",  "ip": "192.168.1.235", "user": "admin", "pass": "abcd1357"},
    {"stt": 23, "name": "Thang máy cư dân 3",              "brand": "Hikvision",  "ip": "192.168.1.236", "user": "admin", "pass": "abcd1357"},
    {"stt": 24, "name": "Thang máy cư dân 4",              "brand": "Hikvision",  "ip": "192.168.1.233", "user": "admin", "pass": "abcd1357"},
    {"stt": 25, "name": "Thang hàng",                      "brand": "Hikvision",  "ip": "192.168.1.232", "user": "admin", "pass": "abcd1357"},
]


def build_rtsp_url(cam):
    """Build RTSP URL based on camera brand."""
    user, pwd, ip = cam["user"], cam["pass"], cam["ip"]
    if cam["brand"] == "Hikvision":
        return f"rtsp://{user}:{pwd}@{ip}:554/Streaming/Channels/101"
    else:  # Dahua / Panasonic
        return f"rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=0"


def seed():
    ok, fail = 0, 0
    for cam in CAMERAS:
        cam_id = f"cam_{cam['stt']:02d}"
        rtsp_url = build_rtsp_url(cam)
        payload = {
            "camera_id": cam_id,
            "name": cam["name"],
            "location": cam["name"],
            "stream_url": rtsp_url,
            "protocol": "rtsp",
            "brand": cam["brand"],
            "username": cam["user"],
            "password": cam["pass"],
            "is_active": True,
            "enable_detection": True,
        }
        try:
            r = requests.post(f"{API}/api/cameras", json=payload, timeout=5)
            if r.status_code in (200, 201):
                print(f"  ✅ {cam_id} — {cam['name']} ({cam['ip']})")
                ok += 1
            else:
                print(f"  ⚠️  {cam_id} — {r.status_code}: {r.text[:80]}")
                fail += 1
        except Exception as e:
            print(f"  ❌ {cam_id} — {e}")
            fail += 1

    print(f"\nDone: {ok} added, {fail} failed")


if __name__ == "__main__":
    print(f"Seeding {len(CAMERAS)} cameras to {API}...\n")
    seed()
