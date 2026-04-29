# 🚀 Getting Started - AI Detection System with Camera Management

## ✅ Pre-requisites

- [x] **Python 3.9+** installed
- [x] **PostgreSQL 12+** installed and running
- [x] **Git** (optional)
- [x] **Visual Studio Code** or any IDE

---

## 🎯 Step-by-Step Setup (5 minutes)

### Step 1: Verify PostgreSQL is Running

**Windows**:
```bash
# Check in Services (services.msc)
# Look for: PostgreSQL 15 Server
# Status should be: Running
```

**Or via command line**:
```bash
psql -U postgres -h localhost -c "SELECT version();"
# Should show PostgreSQL version
```

### Step 2: Navigate to Project

```bash
cd d:\AI_AI\a04
```

### Step 3: Create/Activate Virtual Environment (Optional but Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt

# This will install:
# - Flask 3.0+
# - SQLAlchemy 2.0+
# - OpenCV 4.8+
# - psycopg2 (PostgreSQL driver)
# - python-socketio (WebSocket)
# - torch/ultralytics (YOLO)
# - And more...

# Wait 5-10 minutes (first time installation)
```

### Step 5: Initialize Database

```bash
python init_db.py

# You should see:
# ✓ Dropped existing database
# ✓ Created new database: ai_detection
# ✓ Created tables: persons, vehicles, alerts, cameras
# ✓ Inserted sample data
# ✓ Database initialization complete
```

### Step 6: Start Flask Server

```bash
python app.py

# You should see:
# * Running on http://0.0.0.0:5000
# * Debug mode: ON
# (Press CTRL+C to stop)
```

### Step 7: Open Dashboard in Browser

Open your web browser and go to:
```
http://localhost:5000/dashboard
```

You should see:
- 5 tabs: Dashboard, Cameras, Persons, Vehicles, Alerts
- Statistics boxes (0 cameras, 0 persons, 0 vehicles, 0 alerts initially)
- Tables showing sample data
- Add Camera button

---

## 📹 First Time: Add a Test Camera

### Option A: Via Dashboard UI (Easiest)

1. **Open Dashboard**: http://localhost:5000/dashboard
2. **Click Tab**: "Cameras"
3. **Click Button**: "+ Add Camera"
4. **Fill Form** with test data:

   | Field | Value |
   |-------|-------|
   | Camera Name | `Test Camera` |
   | Camera ID | `test_001` |
   | Location | `Test Location` |
   | Stream URL | `rtsp://example.com/stream` |
   | Protocol | `RTSP` |
   | FPS | `30` |
   | Resolution | `1920x1080` |
   | Brand | `Test` |

5. **Click**: "Add Camera"
6. You should see camera card appear in the grid

### Option B: Via API (curl)

```bash
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "test_001",
    "name": "Test Camera",
    "location": "Test Location",
    "stream_url": "rtsp://example.com/stream",
    "protocol": "rtsp",
    "fps": 30,
    "resolution": "1920x1080",
    "brand": "Test"
  }'
```

### Option C: Via Python

```python
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    "dbname=ai_detection user=postgres password=123456 host=localhost"
)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO cameras 
    (camera_id, name, location, stream_url, protocol, fps, resolution)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", ('test_001', 'Test Camera', 'Test', 'rtsp://example.com/stream', 'rtsp', 30, '1920x1080'))

conn.commit()
cursor.close()
conn.close()

print("Camera added!")
```

---

## 🧪 Verify Everything Works

### Test 1: Check API Health
```bash
curl http://localhost:5000/api/health
# Should return: {"status": "healthy", "timestamp": "2024-..."}
```

### Test 2: List Cameras
```bash
curl http://localhost:5000/api/cameras
# Should return: {"data": [...], "total": 1, "pages": 1}
```

### Test 3: Get Camera Details
```bash
curl http://localhost:5000/api/cameras/test_001
# Should return camera details
```

### Test 4: Check Dashboard Displays Data
- Go to: http://localhost:5000/dashboard
- Tab: "Cameras"
- Should see your camera card

---

## 📊 Understanding the Dashboard

### Tab: Dashboard
- **Statistics**: Total persons, vehicles, alerts (updates every 5 seconds)
- **Recent Detections**: Latest person/vehicle detections
- **Purpose**: System overview

### Tab: Cameras
- **Camera Grid**: Live camera cards
- **Features**:
  - Status indicator (green=connected, red=offline)
  - Live frame preview
  - Camera metadata (location, FPS, resolution, brand)
  - Controls: Start, Stop, Delete buttons
- **Purpose**: Monitor and manage cameras

### Tab: Persons
- **Detection Table**: All person detections
- **Columns**: ID, Location, Shirt Color, Pants Color, Hair Color, Confidence, Time
- **Purpose**: Review person detection history

### Tab: Vehicles
- **Detection Table**: All vehicle detections
- **Columns**: ID, Type, License Plate, Color, Location, Confidence, Time
- **Purpose**: Review vehicle detection history

### Tab: Alerts
- **Alert List**: All system alerts
- **Types**: Fire, Suspicious, Missing Person
- **Purpose**: Alert history and management

---

## 🔗 API Endpoints Quick Reference

### Cameras
```
GET    /api/cameras                      # List all cameras
POST   /api/cameras                      # Add new camera
GET    /api/cameras/<id>                 # Get camera details
PUT    /api/cameras/<id>                 # Update camera
DELETE /api/cameras/<id>                 # Delete camera
POST   /api/cameras/<id>/start           # Start camera stream
POST   /api/cameras/<id>/stop            # Stop camera stream
GET    /api/cameras/<id>/frame           # Get current frame (JPEG)
GET    /api/cameras/<id>/stream          # Get live stream (MJPEG)
GET    /api/cameras/<id>/status          # Get camera status
```

### Persons
```
GET    /api/persons                      # List all persons
POST   /api/persons                      # Add person detection
GET    /api/persons/<id>                 # Get person details
PUT    /api/persons/<id>                 # Update person
DELETE /api/persons/<id>                 # Delete person
```

### Vehicles
```
GET    /api/vehicles                     # List all vehicles
POST   /api/vehicles                     # Add vehicle detection
GET    /api/vehicles/<id>                # Get vehicle details
PUT    /api/vehicles/<id>                # Update vehicle
DELETE /api/vehicles/<id>                # Delete vehicle
```

### Alerts
```
GET    /api/alerts                       # List all alerts
POST   /api/alerts                       # Create alert
GET    /api/alerts/<id>                  # Get alert details
PUT    /api/alerts/<id>                  # Update alert
DELETE /api/alerts/<id>                  # Delete alert
```

### System
```
GET    /api/statistics                   # Get system statistics
GET    /api/health                       # Health check
GET    /                                 # API documentation
GET    /dashboard                        # Web dashboard
```

---

## 🐛 Troubleshooting

### "Address already in use" Error
```bash
# Port 5000 is already in use
# Option 1: Stop the other service
# Option 2: Run on different port
python app.py --port 5001
```

### "ModuleNotFoundError: No module named 'flask'"
```bash
# Dependencies not installed
pip install -r requirements.txt
```

### "psycopg2.OperationalError: could not translate host name"
```bash
# PostgreSQL is not running
# Windows: Start PostgreSQL service from services.msc
# Or run: net start PostgreSQL15
```

### "FATAL: authentication failed for user 'postgres'"
```bash
# Wrong password in .env
# Default: password=123456
# Update .env if your password is different
```

### "relation 'persons' does not exist"
```bash
# Database tables not created
python init_db.py
# Then restart: python app.py
```

### Dashboard shows "No data" or empty tables
```bash
# This is normal if no detections have been uploaded
# Add some test data via API
# Or run detection system first

# Test data example:
curl -X POST http://localhost:5000/api/persons \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "test_person_001",
    "location": "Test Location",
    "confidence": 0.95,
    "shirt_colors": [{"name": "red", "rank": 1}],
    "pants_colors": [{"name": "blue", "rank": 1}],
    "hair_colors": [{"name": "black", "rank": 1}]
  }'
```

---

## 📈 Next Steps After Setup

### Short-term (Today)
- [ ] Get familiar with dashboard
- [ ] Add a few cameras via API
- [ ] Test API endpoints with curl
- [ ] Explore database with pgAdmin

### Medium-term (This Week)
- [ ] Integrate with main.py for real detections
- [ ] Test with real camera streams
- [ ] Configure notifications/alerts
- [ ] Setup recording

### Long-term (Before Production)
- [ ] Add user authentication
- [ ] Enable HTTPS/SSL
- [ ] Setup database backups
- [ ] Performance tuning
- [ ] Load testing

---

## 🎓 Learning Resources

### Understanding the System
1. **Architecture**: Read [ARCHITECTURE.txt](ARCHITECTURE.txt)
2. **Database**: Review [models.py](models.py)
3. **API**: Check [app.py](app.py)
4. **Integration**: Study [INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)

### Running Detection
1. Update [main.py](main.py) to use camera system
2. Reference [db_integration.py](db_integration.py) for upload
3. Test with real YOLO models

### Extending the System
1. Add new detection types in models.py
2. Create new API endpoints in app.py
3. Add UI components to dashboard.html
4. Update WebSocket events

---

## 📚 Files Explanation

| File | Purpose |
|------|---------|
| `main.py` | YOLO detection script (entry point) |
| `models.py` | SQLAlchemy database models |
| `app.py` | Flask REST API server |
| `camera_manager.py` | Camera streaming manager |
| `db_integration.py` | Python client library |
| `init_db.py` | Database initialization |
| `config.py` | Configuration settings |
| `templates/dashboard.html` | Web UI (single-page app) |
| `.env` | Environment variables |
| `requirements.txt` | Python dependencies |

---

## 💡 Tips & Tricks

### Speed up dashboard
- Reduce auto-refresh interval
- Reduce pagination size
- Use search/filter to load less data

### Improve camera performance
- Reduce resolution (1280x720 instead of 1920x1080)
- Reduce FPS (15-20 instead of 30)
- Use H.264 codec (more efficient)

### Debug API issues
```bash
# Enable request logging
curl -v http://localhost:5000/api/cameras

# Check response headers
curl -i http://localhost:5000/api/cameras

# Save response to file
curl http://localhost:5000/api/cameras > response.json
```

### Monitor database
```bash
# Connect to database
psql -U postgres -d ai_detection

# Check tables
\dt

# Count rows
SELECT COUNT(*) FROM persons;
SELECT COUNT(*) FROM vehicles;
SELECT COUNT(*) FROM cameras;
SELECT COUNT(*) FROM alerts;

# Exit
\q
```

---

## 🚨 Important Notes

1. **Default Credentials**:
   - Database User: `postgres`
   - Database Password: `123456`
   - No API authentication yet (add in production)

2. **Default Configuration**:
   - API Port: `5000`
   - Database: `ai_detection`
   - Host: `localhost:5432`
   - Check `.env` to change

3. **Development Mode**:
   - Debug mode is ON
   - Auto-reload on code changes
   - Verbose logging

4. **Production Readiness**:
   - [ ] Disable debug mode
   - [ ] Add authentication
   - [ ] Enable HTTPS
   - [ ] Setup monitoring
   - [ ] Configure backups

---

## ✅ System Requirements Met

- [x] PostgreSQL database with 4 tables
- [x] 30+ REST API endpoints
- [x] Real-time WebSocket updates
- [x] Camera RTSP/HTTPS support
- [x] Web dashboard UI
- [x] Python integration library
- [x] Full CRUD operations
- [x] Search & filter capabilities
- [x] Error handling & logging

---

## 🎉 You're All Set!

Your AI Detection System with Camera Management is now ready to use!

### What's next?

1. **Explore Dashboard**: http://localhost:5000/dashboard
2. **Read Documentation**: Check README.md or CAMERA_SETUP.md
3. **Integrate Detection**: Update main.py to use the system
4. **Customize**: Add your own detection logic and cameras

---

## 📞 Support Resources

- **Documentation**: See [README.md](README.md)
- **Camera Guide**: See [CAMERA_SETUP.md](CAMERA_SETUP.md)
- **Integration**: See [INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)
- **Architecture**: See [ARCHITECTURE.txt](ARCHITECTURE.txt)
- **System Status**: See [SYSTEM_STATUS.md](SYSTEM_STATUS.md)

---

**Enjoy your AI Detection System! 🚀**

*Last Updated: 2024 | Version 1.0.0*
