# 📹 Camera Management System Setup Guide

## 개요 (Overview)

Hệ thống quản lý camera hoàn chỉnh với hỗ trợ RTSP/HTTPS streams, live monitoring, và tích hợp detection.

## ✨ Tính Năng

✅ **Multiple Cameras** - Quản lý nhiều camera cùng lúc
✅ **RTSP/HTTPS Streaming** - Hỗ trợ RTSP, HTTPS, HTTP, WebSocket
✅ **Live Monitoring** - Xem livestream trực tiếp
✅ **Frame Capture** - Lấy frame hiện tại
✅ **Camera Status** - Theo dõi kết nối camera
✅ **Auto-Reconnect** - Tự động kết nối lại khi mất kết nối
✅ **Real-time Updates** - WebSocket real-time
✅ **Detection Integration** - Tích hợp YOLO detection

---

## 🚀 Quick Start

### 1. Cài đặt OpenCV (nếu chưa có)

```bash
pip install opencv-python opencv-contrib-python
```

### 2. Khởi tạo Database mới (có Camera table)

```bash
python init_db.py
```

### 3. Chạy Flask Server

```bash
python app.py
```

### 4. Mở Dashboard

```
http://localhost:5000/dashboard
```

---

## 📹 Thêm Camera

### Via Web Dashboard

1. Mở Dashboard: `http://localhost:5000/dashboard`
2. Vào tab **"Cameras"**
3. Click **"+ Add Camera"**
4. Điền thông tin camera

### Via API

```bash
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "camera_001",
    "name": "Main Gate Camera",
    "location": "Main Gate",
    "stream_url": "rtsp://admin:password@192.168.1.100:554/stream1",
    "protocol": "rtsp",
    "fps": 30,
    "resolution": "1920x1080",
    "brand": "Hikvision",
    "model": "DS-2CD2143G0-I",
    "username": "admin",
    "password": "password"
  }'
```

### Via Python

```python
from db_integration import DetectionDataUploader

uploader = DetectionDataUploader('http://localhost:5000')

# Add camera directly to database
from models import db, Camera

camera = Camera(
    camera_id='camera_001',
    name='Main Gate',
    location='Main Gate',
    stream_url='rtsp://admin:pass@192.168.1.100:554/stream1',
    protocol='rtsp',
    fps=30
)
db.session.add(camera)
db.session.commit()
```

---

## 🎥 Stream URL Examples

### RTSP (Hikvision)
```
rtsp://admin:12345@192.168.1.100:554/stream1
```

### RTSP (Other brands)
```
rtsp://username:password@192.168.1.100:554/live
rtsp://192.168.1.100:554/axis-media/media.amp?videocodec=h264
```

### HTTPS
```
https://192.168.1.100:443/video.mjpg
https://camera.example.com:8443/stream
```

### HTTP with credentials
```
http://admin:password@192.168.1.100:8000/video.cgi
```

### Localhost test (OpenCV test source)
```
rtsp://localhost:8554/test
```

---

## 📊 API Endpoints - Cameras

### List all cameras
```bash
curl http://localhost:5000/api/cameras
```

Response:
```json
{
  "data": [
    {
      "id": 1,
      "camera_id": "camera_001",
      "name": "Main Gate",
      "location": "Main Gate",
      "stream_url": "rtsp://...",
      "protocol": "rtsp",
      "fps": 30,
      "is_active": true,
      "is_connected": true,
      "last_frame_timestamp": "2024-01-15T10:30:00"
    }
  ],
  "total": 1,
  "pages": 1,
  "current_page": 1
}
```

### Get camera details
```bash
curl http://localhost:5000/api/cameras/camera_001
```

### Get current frame (JPEG)
```bash
# Returns JPEG binary data
curl http://localhost:5000/api/cameras/camera_001/frame > frame.jpg
```

### Get live stream (MJPEG)
```bash
# Motion JPEG stream - playable in HTML5 video tag
curl http://localhost:5000/api/cameras/camera_001/stream
```

### Get camera status
```bash
curl http://localhost:5000/api/cameras/camera_001/status
```

Response:
```json
{
  "camera": { ... },
  "stream_status": {
    "camera_id": "camera_001",
    "is_running": true,
    "is_connected": true,
    "frame_count": 450,
    "error_count": 0
  }
}
```

### Start camera stream
```bash
curl -X POST http://localhost:5000/api/cameras/camera_001/start
```

### Stop camera stream
```bash
curl -X POST http://localhost:5000/api/cameras/camera_001/stop
```

### Update camera
```bash
curl -X PUT http://localhost:5000/api/cameras/camera_001 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Gate Updated",
    "location": "New Location"
  }'
```

### Delete camera
```bash
curl -X DELETE http://localhost:5000/api/cameras/camera_001
```

---

## 🔗 Tích hợp với Detection System

### Cách 1: Đọc Camera Stream + YOLO Detection

```python
from camera_manager import camera_manager
from db_integration import DetectionDataUploader
import cv2

# Setup
camera_manager.add_camera(
    'camera_001',
    'rtsp://admin:pass@192.168.1.100:554/stream1',
    fps=30
)
camera_manager.start_camera('camera_001')

uploader = DetectionDataUploader('http://localhost:5000')

# Get frames từ camera
while True:
    frame_jpeg = camera_manager.get_frame_jpeg('camera_001')
    
    if frame_jpeg:
        # Convert JPEG to frame
        import numpy as np
        frame = cv2.imdecode(np.frombuffer(frame_jpeg, np.uint8), cv2.IMREAD_COLOR)
        
        # Run YOLO detection
        results = model_yolo.predict(frame)
        
        # Upload results
        for detection in results:
            uploader.upload_person(
                person_id=...,
                location='camera_001',
                confidence=...,
                frame_index=...
            )
    
    time.sleep(0.033)  # 30 FPS
```

### Cách 2: Stream URL → Main.py

Update main.py để sử dụng stream URLs từ database:

```python
# Get cameras from database
cameras = Camera.query.filter_by(is_active=True).all()

for camera in cameras:
    cap = cv2.VideoCapture(camera.stream_url)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # YOLO detection
        # ...
        
        # Upload results with camera location
        uploader.upload_person(
            person_id=...,
            location=camera.location,  # ← từ camera
            confidence=...,
            frame_index=...
        )
```

---

## 🖥️ Dashboard Features

### Tabs

1. **Dashboard** - Overview thống kê
2. **Cameras** - Quản lý camera, xem livestream
3. **Persons** - Danh sách người phát hiện
4. **Vehicles** - Danh sách xe phát hiện
5. **Alerts** - Cảnh báo hệ thống

### Camera Card Features

- 📺 Live frame display
- 🟢 Connection status indicator
- ⚙️ Camera info (location, FPS, resolution, brand)
- 🎮 Start/Stop/Delete buttons
- 📊 Real-time status

### Detection Tables

- Type badge (Person/Vehicle)
- ID, Location, Colors (shirt/pants/hair)
- Confidence score
- Detected timestamp
- Quick actions

---

## 📡 Camera Manager Class

```python
from camera_manager import camera_manager

# Add camera
camera_manager.add_camera(
    'camera_001',
    'rtsp://admin:pass@192.168.1.100:554/stream1',
    username='admin',
    password='password',
    fps=30
)

# Start streaming
camera_manager.start_camera('camera_001')

# Get current frame (JPEG bytes)
frame_jpeg = camera_manager.get_frame_jpeg('camera_001')

# Get frame as base64
frame_base64 = camera_manager.get_frame_base64('camera_001')

# Get status
status = camera_manager.get_camera_status('camera_001')
print(status)  # {is_running, is_connected, frame_count, ...}

# Stop camera
camera_manager.stop_camera('camera_001')

# Remove camera
camera_manager.remove_camera('camera_001')

# Get all cameras
cameras = camera_manager.get_all_cameras()

# Get all status
all_status = camera_manager.get_all_status()

# Start/Stop all
camera_manager.start_all()
camera_manager.stop_all()
```

---

## 🔧 Troubleshooting

### Camera không connect

**Vấn đề**: RTSP stream không open
**Giải pháp**:
1. Kiểm tra URL: `ffmpeg -rtsp_transport tcp -i "rtsp://..." -f null -`
2. Kiểm tra credentials
3. Kiểm tra firewall
4. Kiểm tra camera online

### Frame không update

**Vấn đề**: Camera đã connect nhưng frame không thay đổi
**Giải pháp**:
1. Kiểm tra FPS setting
2. Kiểm tra frame buffer
3. Kiểm tra resolution (quá lớn = timeout)

### Memory leak

**Vấn đề**: RAM tăng liên tục
**Giải pháp**:
1. Giảm resolution (1280x720 thay vì 1920x1080)
2. Giảm FPS
3. Kiểm tra frame buffer size

### Lag/Latency cao

**Vấn đề**: Stream có độ trễ
**Giải pháp**:
1. Tăng buffer size (cẩn thận - tăng latency)
2. Giảm resolution
3. Kiểm tra network
4. Kiểm tra camera load

---

## 📊 Database Schema - Cameras Table

```sql
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    stream_url VARCHAR(500) NOT NULL,
    protocol VARCHAR(20) DEFAULT 'rtsp',
    resolution VARCHAR(50),
    fps INTEGER DEFAULT 30,
    brand VARCHAR(100),
    model VARCHAR(100),
    username VARCHAR(100),
    password VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_recording BOOLEAN DEFAULT FALSE,
    last_frame_timestamp TIMESTAMP,
    last_connection_status VARCHAR(20) DEFAULT 'unknown',
    enable_detection BOOLEAN DEFAULT TRUE,
    enable_recording BOOLEAN DEFAULT FALSE,
    recording_path VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 Best Practices

1. **FPS Setting** - 30 FPS tốt nhất cho đa số trường hợp
2. **Resolution** - 1280x720 cân bằng quality/performance
3. **Buffer** - Giữ nhỏ để giảm latency
4. **Authentication** - Lưu password an toàn (encrypt in DB)
5. **Monitoring** - Kiểm tra status camera định kỳ
6. **Recording** - Enable khi cần, tắt khi không dùng
7. **Network** - Đảm bảo bandwidth đủ (30 FPS 1280x720 ≈ 5-10 Mbps)

---

## 📚 File References

- `camera_manager.py` - Camera streaming manager
- `models.py` - Camera database model
- `app.py` - Camera API endpoints
- `templates/dashboard.html` - Web dashboard
- `.env.camera.example` - Camera configuration example

---

## 🔗 Related Documentation

- [Main README](README.md) - System documentation
- [QUICKSTART](QUICKSTART.md) - Quick setup guide
- [INTEGRATION_GUIDE](INTEGRATION_GUIDE.py) - Integration guide

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: ✅ Production Ready
