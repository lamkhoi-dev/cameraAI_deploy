# 📌 Developer Quick Reference

## 🚀 Quick Commands

### Setup (First Time)
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start server
python app.py
```

### Dashboard
```
http://localhost:5000/dashboard
```

### API Base URL
```
http://localhost:5000/api
```

---

## 📹 Camera API

### Add Camera
```bash
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "cam001",
    "name": "Main Gate",
    "location": "Gate 1",
    "stream_url": "rtsp://admin:pass@192.168.1.1:554/stream",
    "protocol": "rtsp",
    "fps": 30
  }'
```

### Get Cameras
```bash
curl http://localhost:5000/api/cameras
```

### Get Frame (JPEG)
```bash
curl http://localhost:5000/api/cameras/cam001/frame > frame.jpg
```

### Stream (MJPEG)
```bash
curl http://localhost:5000/api/cameras/cam001/stream
```

### Camera Control
```bash
# Start
curl -X POST http://localhost:5000/api/cameras/cam001/start

# Stop
curl -X POST http://localhost:5000/api/cameras/cam001/stop

# Status
curl http://localhost:5000/api/cameras/cam001/status

# Delete
curl -X DELETE http://localhost:5000/api/cameras/cam001
```

---

## 👤 Person API

### Add Person
```bash
curl -X POST http://localhost:5000/api/persons \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "person_001",
    "location": "Gate 1",
    "confidence": 0.95,
    "shirt_colors": [{"rank": 1, "name": "red"}],
    "pants_colors": [{"rank": 1, "name": "blue"}],
    "hair_colors": [{"rank": 1, "name": "black"}]
  }'
```

### Search Persons
```bash
# By location
curl "http://localhost:5000/api/persons?location=Gate%201"

# By time range
curl "http://localhost:5000/api/persons?start_time=2024-01-01&end_time=2024-01-31"

# Pagination
curl "http://localhost:5000/api/persons?page=1&per_page=20"
```

---

## 🚗 Vehicle API

### Add Vehicle
```bash
curl -X POST http://localhost:5000/api/vehicles \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "vehicle_001",
    "vehicle_type": "car",
    "license_plate": "ABC123",
    "location": "Gate 1",
    "confidence": 0.92,
    "vehicle_colors": [{"rank": 1, "name": "red"}]
  }'
```

### Search Vehicles
```bash
curl "http://localhost:5000/api/vehicles?license_plate=ABC123"
curl "http://localhost:5000/api/vehicles?vehicle_type=car"
curl "http://localhost:5000/api/vehicles?location=Gate%201"
```

---

## 🚨 Alert API

### Create Alert
```bash
curl -X POST http://localhost:5000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "fire",
    "description": "Fire detected at gate",
    "location": "Gate 1",
    "severity": "critical",
    "status": "active"
  }'
```

### Get Alerts
```bash
curl http://localhost:5000/api/alerts

# By status
curl "http://localhost:5000/api/alerts?status=active"

# By severity
curl "http://localhost:5000/api/alerts?severity=critical"
```

### Update Alert Status
```bash
curl -X PUT http://localhost:5000/api/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}'
```

---

## 📊 System API

### Statistics
```bash
curl http://localhost:5000/api/statistics
```

Response:
```json
{
  "total_persons": 42,
  "total_vehicles": 15,
  "active_alerts": 3,
  "recent_persons": [...],
  "recent_vehicles": [...]
}
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

---

## 🔌 Python Integration

### Upload Person
```python
from db_integration import DetectionDataUploader

uploader = DetectionDataUploader('http://localhost:5000')

uploader.upload_person(
    person_id='person_001',
    location='Gate 1',
    shirt_colors=[{'rank': 1, 'name': 'red', 'rgb': (255,0,0)}],
    pants_colors=[{'rank': 1, 'name': 'blue', 'rgb': (0,0,255)}],
    hair_colors=[{'rank': 1, 'name': 'black', 'rgb': (0,0,0)}],
    confidence=0.95,
    frame_index=100,
    video_source='camera_001'
)
```

### Search Persons
```python
results = uploader.search_persons(
    location='Gate 1',
    page=1,
    per_page=20
)
print(results['data'])
print(f"Total: {results['total']}, Pages: {results['pages']}")
```

### Check Health
```python
if uploader.check_api_health():
    print("API is healthy!")
else:
    print("API is down!")
```

---

## 🎥 Camera Manager

### Import
```python
from camera_manager import camera_manager
```

### Add Camera
```python
camera_manager.add_camera(
    'camera_001',
    'rtsp://admin:pass@192.168.1.1:554/stream'
)
```

### Start/Stop
```python
camera_manager.start_camera('camera_001')
# ... use frames ...
camera_manager.stop_camera('camera_001')
```

### Get Frame
```python
# JPEG bytes
frame_jpeg = camera_manager.get_frame_jpeg('camera_001')

# Base64 string
frame_b64 = camera_manager.get_frame_base64('camera_001')

# Save to file
with open('frame.jpg', 'wb') as f:
    f.write(frame_jpeg)
```

### Get Status
```python
status = camera_manager.get_camera_status('camera_001')
print(status)
# {is_running, is_connected, frame_count, error_count}
```

---

## 📝 Database

### Connect to Database
```bash
psql -U postgres -d ai_detection
```

### Useful Queries
```sql
-- Count persons
SELECT COUNT(*) FROM persons;

-- Recent detections
SELECT * FROM persons ORDER BY timestamp DESC LIMIT 10;

-- Cameras by location
SELECT * FROM cameras WHERE location = 'Gate 1';

-- Active alerts
SELECT * FROM alerts WHERE status = 'active';

-- Persons with color analysis
SELECT person_id, location, shirt_colors FROM persons;
```

---

## 🖥️ Model Structure

### Person Model
```python
{
  "person_id": "person_001",
  "location": "Gate 1",
  "timestamp": "2024-01-15T10:30:00",
  "confidence": 0.95,
  "shirt_colors": [{"rank": 1, "name": "red", "rgb": [...], "bgr": [...], "hsv": [...]}],
  "pants_colors": [...],
  "hair_colors": [...],
  "image_path": "path/to/image.jpg",
  "frame_index": 100,
  "video_source": "camera_001"
}
```

### Camera Model
```python
{
  "camera_id": "camera_001",
  "name": "Main Gate",
  "location": "Gate 1",
  "stream_url": "rtsp://...",
  "protocol": "rtsp",
  "fps": 30,
  "resolution": "1920x1080",
  "brand": "Hikvision",
  "username": "admin",
  "is_active": true,
  "last_connection_status": "connected",
  "last_frame_timestamp": "2024-01-15T10:30:00"
}
```

---

## 🐛 Common Issues

### Port 5000 in use
```bash
# Find what's using it
netstat -ano | findstr :5000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
python app.py --port 5001
```

### Database connection error
```bash
# Check PostgreSQL running
pg_isready -h localhost -p 5432

# Check credentials in .env
# Default: user=postgres, password=123456
```

### Camera not connecting
```bash
# Test RTSP URL
ffmpeg -rtsp_transport tcp -i "rtsp://..." -f null -

# Check camera online and credentials
# Check firewall rules
```

### Dashboard shows empty
```bash
# Normal if no data uploaded
# Add test data via API
# Or run detection first
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Main documentation |
| GETTING_STARTED.md | 5-min setup |
| CAMERA_SETUP.md | Camera guide |
| INTEGRATION_GUIDE.py | Code examples |
| DEPLOYMENT_CHECKLIST.md | Production |
| ARCHITECTURE.txt | Design |
| SYSTEM_STATUS.md | Overview |

---

## 🔗 URLs

| URL | Purpose |
|-----|---------|
| http://localhost:5000 | API docs |
| http://localhost:5000/dashboard | Web UI |
| http://localhost:5000/api/health | Health check |
| http://localhost:5000/api/statistics | Stats |
| http://localhost:5000/api/cameras | Camera API |

---

## 📦 Requirements

- Python 3.9+
- PostgreSQL 12+
- Requirements in requirements.txt

---

## ✅ Verify Setup

```bash
# 1. Check PostgreSQL
psql -U postgres -c "SELECT 1"

# 2. Check Python
python --version

# 3. Check dependencies
pip list | grep -E "Flask|SQLAlchemy|opencv"

# 4. Test database
python -c "from models import db; print('✓ Database OK')"

# 5. Test API
curl http://localhost:5000/api/health

# 6. Test dashboard
curl http://localhost:5000/dashboard | head -20
```

---

## 🎯 Quick Testing

```bash
# Terminal 1: Start server
python app.py

# Terminal 2: Test API
curl http://localhost:5000/api/cameras
curl http://localhost:5000/api/statistics
curl http://localhost:5000/api/health

# Browser: Open dashboard
http://localhost:5000/dashboard
```

---

**Last Updated**: 2024  
**Version**: 1.0.0

Print this page for quick reference! 📋
