<<<<<<< HEAD
# 🎥 AI Detection System - Complete Platform

Hệ thống hoàn chỉnh: **PostgreSQL Database + Flask REST API + Camera Management + Web Dashboard**

> **Status**: ✅ **PRODUCTION READY** | **Version**: 1.0.0 | **Cameras**: RTSP/HTTPS/HTTP

Hệ thống quản lý camera thông minh với YOLO detection, lưu trữ dữ liệu phát hiện người/phương tiện, quản lý cảnh báo, và web dashboard thực tế.

## 🌟 Tính năng Chính

### 🎥 Camera Management (NEW)
- ✅ RTSP/HTTPS/HTTP streaming support
- ✅ Multi-camera management
- ✅ Live frame capture (JPEG)
- ✅ MJPEG streaming
- ✅ Auto-reconnection
- ✅ Real-time status monitoring
- ✅ Camera add/edit/delete via dashboard

### 📊 Data Management
- ✅ Person detection (với dữ liệu màu áo/quần/tóc)
- ✅ Vehicle detection (với biển số)
- ✅ Alert system (cỏa, suspicious, missing)
- ✅ Full search & filter capabilities
- ✅ Pagination & sorting
- ✅ Timestamp tracking

### 🌐 Web Dashboard
- ✅ 5 tabs: Dashboard, Cameras, Persons, Vehicles, Alerts
- ✅ Live camera preview
- ✅ Statistics overview
- ✅ Real-time updates (5 second refresh)
- ✅ Responsive design (mobile-friendly)
- ✅ Add/edit/delete operations

### 📡 Backend & API
- ✅ 30+ REST endpoints
- ✅ Full CRUD operations
- ✅ WebSocket real-time push
- ✅ Error handling & logging
- ✅ Database optimization with indexes

### 🔗 Integration
- ✅ Python client library (db_integration.py)
- ✅ Easy YOLO integration
- ✅ Automatic data upload
- ✅ Search API for queries

## 📋 Thành phần Hệ Thống

### Backend Layer
- **PostgreSQL Database** (4 tables): persons, vehicles, alerts, cameras
- **Flask API Server** (30+ endpoints): REST, WebSocket, streaming
- **Camera Manager** (New): RTSP/HTTPS streaming + frame capture
- **SQLAlchemy ORM**: Database abstraction layer
- **SocketIO**: Real-time WebSocket updates

### Frontend Layer  
- **Web Dashboard** (dashboard.html): Single-page app
- **Responsive UI**: Works on desktop/tablet/mobile
- **Real-time updates**: Auto-refresh + WebSocket ready

## 🛠️ Cài đặt

### 1. Cài đặt PostgreSQL

#### Windows
- Tải: https://www.postgresql.org/download/windows/
- Chạy installer
- Nhớ password cho user `postgres`
- Default port: 5432

#### hoặc Docker
```bash
docker run --name ai-postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 -d postgres
```

### 2. Cài đặt Python Packages

```bash
pip install -r requirements.txt
```

### 3. Cấu hình Database (sửa .env)

```env
DATABASE_URL=postgresql://postgres:123456@localhost:5432/ai_detection
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Khởi tạo Database

```bash
python init_db.py
```

Output:
```
✓ Database 'ai_detection' created successfully
✓ All tables created successfully
✓ Sample data inserted successfully
```

### 5. Chạy Flask API Server

```bash
python app.py
```

Output:
```
 * Running on http://0.0.0.0:5000
 * Serving Flask app...
```

## ⚡ Quick Start (5 minutes)

### 1️⃣ Install Dependencies
# 1. Cài đặt các gói lõi trước
pip install torch==2.2.2 torchvision==0.17.2
```bash
pip install -r requirements.txt
```

### 2️⃣ Initialize Database
```bash
python init_db.py
```

### 3️⃣ Start Server
```bash
python app.py
# Server running at http://localhost:5000
```

### 4️⃣ Open Dashboard
```
Browser: http://localhost:5000/dashboard
```

### 5️⃣ Add Camera
- Click "+ Add Camera"
- Enter camera details (RTSP/HTTPS URL)
- Camera appears in grid with live preview

**Done!** Your system is now running. 🎉

---

## 📚 Documentation Hub

| Document | Purpose |
|----------|---------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | ⭐ Start here - 5 min setup |
| **[CAMERA_SETUP.md](CAMERA_SETUP.md)** | 📹 Camera management guide |
| **[INTEGRATION_GUIDE.py](INTEGRATION_GUIDE.py)** | 🔗 Integration examples |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | 🚀 Production deployment |
| **[SYSTEM_STATUS.md](SYSTEM_STATUS.md)** | 📊 System overview |
| **[ARCHITECTURE.txt](ARCHITECTURE.txt)** | 🏗️ System architecture |

---

## 🚀 Sử dụng

### Option 1: Qua Python Client

```python
from db_integration import DetectionDataUploader

uploader = DetectionDataUploader('http://localhost:5000')

# Upload người
uploader.upload_person(
    person_id='person_001',
    location='Camera 1',
    shirt_colors=[{'rank': 1, 'name': 'Trắng', 'rgb': (255, 255, 255)}],
    pants_colors=[{'rank': 1, 'name': 'Xanh đen', 'rgb': (0, 51, 102)}],
    hair_colors=[{'rank': 1, 'name': 'Đen', 'rgb': (0, 0, 0)}],
    confidence=0.95
)

# Tìm kiếm
results = uploader.search_persons(location='Camera 1')
```

### Option 2: Qua REST API (cURL)

```bash
# Tạo người
curl -X POST http://localhost:5000/api/persons \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "person_001",
    "location": "Camera 1",
    "shirt_colors": [{"rank": 1, "name": "Trắng", "rgb": [255, 255, 255]}],
    "confidence": 0.95
  }'

# Liệt kê
curl http://localhost:5000/api/persons?location=Camera%201

# Tạo xe
curl -X POST http://localhost:5000/api/vehicles \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "vehicle_001",
    "vehicle_type": "car",
    "license_plate": "29A-12345",
    "confidence": 0.92
  }'
```

### Option 3: Tích hợp vào main.py

Xem `INTEGRATION_GUIDE.py` cho hướng dẫn chi tiết

## 📊 API Endpoints

### Persons (Người)

```
POST   /api/persons                    # Tạo/cập nhật
GET    /api/persons                    # Liệt kê (với filter)
GET    /api/persons/<id>               # Chi tiết
PUT    /api/persons/<id>               # Cập nhật
DELETE /api/persons/<id>               # Xóa
```

**Query parameters cho GET /api/persons**:
- `location` - Tìm theo vị trí
- `start_time` - Từ thời gian (ISO format)
- `end_time` - Đến thời gian
- `page` - Trang (default 1)
- `per_page` - Số lượng (default 20)

### Vehicles (Phương tiện)

```
POST   /api/vehicles                   # Tạo/cập nhật
GET    /api/vehicles                   # Liệt kê (với filter)
GET    /api/vehicles/<id>              # Chi tiết
PUT    /api/vehicles/<id>              # Cập nhật
DELETE /api/vehicles/<id>              # Xóa
```

**Query parameters cho GET /api/vehicles**:
- `vehicle_type` - Loại (car, motorcycle, bus, truck, bicycle)
- `license_plate` - Biển số
- `location` - Vị trí
- `start_time` - Từ thời gian
- `end_time` - Đến thời gian

### Alerts (Cảnh báo)

```
POST   /api/alerts                     # Tạo
GET    /api/alerts                     # Liệt kê (với filter)
PUT    /api/alerts/<id>                # Cập nhật
DELETE /api/alerts/<id>                # Xóa
```

**Query parameters**:
- `alert_type` - Loại cảnh báo
- `status` - Trạng thái (active, resolved, false_alarm)
- `severity` - Mức độ (low, normal, high, critical)

### Statistics

```
GET    /api/statistics                 # Thống kê chung
GET    /health                         # Kiểm tra sức khỏe
```

## 🔄 Real-time Updates (WebSocket)

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected')
    sio.emit('subscribe_persons')      # Theo dõi người mới
    sio.emit('subscribe_vehicles')     # Theo dõi xe mới
    sio.emit('subscribe_alerts')       # Theo dõi cảnh báo mới

@sio.on('new_person')
def on_person(data):
    print(f'New person: {data["person_id"]}')

@sio.on('new_vehicle')
def on_vehicle(data):
    print(f'New vehicle: {data["vehicle_id"]}')

@sio.on('new_alert')
def on_alert(data):
    print(f'Alert: {data["alert_type"]}')

sio.connect('http://localhost:5000')
sio.wait()
```

## 📁 Cấu trúc File

```
.
├── app.py                    # Flask API server chính
├── models.py                 # SQLAlchemy models (Person, Vehicle, Alert)
├── db_integration.py         # Client để upload dữ liệu
├── init_db.py                # Script khởi tạo database
├── client_example.py         # Ví dụ sử dụng
├── INTEGRATION_GUIDE.py      # Hướng dẫn tích hợp vào main.py
├── requirements.txt          # Python dependencies
├── .env                       # Cấu hình (database URL, etc.)
├── main.py                   # YOLO detection (main system)
├── yolov8n-pose.pt           # Model pose detection
├── yolov8n.pt                # Model object detection
└── cropped_data/             # Ảnh crops từ detection
    ├── person_1/
    ├── person_2/
    ├── vehicles/
    └── fire_alerts/
```

## 📈 Database Schema

### Table: persons
```sql
- id: PRIMARY KEY
- person_id: UNIQUE (INDEX)
- location: TEXT (INDEX)
- timestamp: DATETIME (INDEX)
- image_path: VARCHAR(500)
- shirt_colors: JSON
- pants_colors: JSON
- hair_colors: JSON
- confidence: FLOAT
- frame_index: INT
- video_source: VARCHAR(255)
- notes: TEXT
- created_at, updated_at: DATETIME
```

### Table: vehicles
```sql
- id: PRIMARY KEY
- vehicle_id: UNIQUE (INDEX)
- vehicle_type: VARCHAR(50) (INDEX)
- license_plate: VARCHAR(50) (INDEX)
- vehicle_colors: JSON
- location: TEXT (INDEX)
- timestamp: DATETIME (INDEX)
- image_path: VARCHAR(500)
- confidence: FLOAT
- frame_index: INT
- video_source: VARCHAR(255)
- notes: TEXT
- created_at, updated_at: DATETIME
```

### Table: alerts
```sql
- id: PRIMARY KEY
- alert_type: VARCHAR(50) (INDEX)
- person_id: VARCHAR(50) (FOREIGN KEY, INDEX)
- vehicle_id: VARCHAR(50) (FOREIGN KEY, INDEX)
- description: TEXT
- location: VARCHAR(255)
- timestamp: DATETIME (INDEX)
- frame_index: INT
- image_path: VARCHAR(500)
- severity: VARCHAR(20)
- status: VARCHAR(20) (INDEX)
- created_at, updated_at: DATETIME
```

## 🧪 Test

### Chạy Client Examples
```bash
python client_example.py
```

Output:
```
✓ Example 1: CRUD Operations
✓ Example 2: Search & Filter
✓ Example 3: WebSocket Real-time Updates
...
```

## 🔧 Troubleshooting

### Lỗi: "Connection refused"
```
✗ FAILED: Can't connect to PostgreSQL

Giải pháp:
1. Kiểm tra PostgreSQL service đang chạy
2. Sửa DATABASE_URL trong .env
3. Kiểm tra user/password trong .env
```

### Lỗi: "Table already exists"
```
✗ ERROR: relation "persons" already exists

Giải pháp:
# Option 1: Drop database cũ
python -c "from app import db; db.drop_all()"

# Option 2: Xóa database trong PostgreSQL
DROP DATABASE ai_detection;
```

### Lỗi: "API not responding"
```
✗ API server is not running!

Giải pháp:
1. Chạy Flask server: python app.py
2. Kiểm tra port 5000 không bị chiếm
3. Kiểm tra firewall
```

## 📝 Ví dụ Tích hợp vào main.py

Xem `INTEGRATION_GUIDE.py` cho code mẫu

Cơ bản:
```python
from db_integration import DetectionDataUploader

uploader = DetectionDataUploader('http://localhost:5000')

# Trong hàm save_person():
if uploader.check_api_health():
    uploader.upload_person(
        person_id=f'person_{id}',
        location='Camera 1',
        shirt_colors=shirt_colors,
        confidence=conf,
        frame_index=frame_idx
    )
```

## 🚦 Performance Tips

1. **Batch Operations**: Group multiple uploads thành 1 request nếu có thể
2. **Pagination**: Sử dụng `page` và `per_page` khi query lớn
3. **Indexing**: Database đã có indexes cho search (location, timestamp, type)
4. **Connection Pooling**: Flask-SQLAlchemy tự động quản lý connection pool
5. **WebSocket**: Dùng cho real-time updates thay vì polling

## 📚 Documentation

- REST API Docs: http://localhost:5000/ (khi server chạy)
- INTEGRATION_GUIDE.py: Hướng dẫn chi tiết
- db_integration.py: API client documentation
- client_example.py: Ví dụ sử dụng

## 🤝 Hỗ trợ

Để khắc phục sự cố:

1. Kiểm tra PostgreSQL đang chạy
2. Kiểm tra credentials trong .env
3. Chạy `python init_db.py` để reinitialize
4. Kiểm tra Flask server logs
5. Xem INTEGRATION_GUIDE.py cho ví dụ

## ✅ Checklist

- [ ] PostgreSQL cài và chạy
- [ ] Python packages cài: `pip install -r requirements.txt`
- [ ] Database khởi tạo: `python init_db.py`
- [ ] Flask server chạy: `python app.py`
- [ ] Test client: `python client_example.py`
- [ ] Tích hợp vào main.py (xem INTEGRATION_GUIDE.py)

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Language**: Vietnamese (Tiếng Việt)
=======
# SecureVision AI v4.0 — Hệ thống Giám sát Camera AI Toàn diện

SecureVision AI là một giải pháp giám sát an ninh thông minh tích hợp Trí tuệ nhân tạo (AI) thế hệ mới, được thiết kế để quản lý tập trung từ 16-20 camera với khả năng nhận diện, phân tích và cảnh báo thời gian thực. Hệ thống sử dụng kiến trúc hiện đại, đảm bảo độ trễ thấp (<1s) và khả năng mở rộng cao.

---

## 🌟 Tính năng cốt lõi

### 1. Giám sát & Luồng Video
*   **Hỗ trợ 16-20 Camera**: Quản lý đồng thời nhiều luồng RTSP/HTTPS.
*   **Siêu độ trễ thấp (Ultra-low Latency)**: Tích hợp **go2rtc** để chuyển đổi RTSP sang WebRTC, giúp xem trực tiếp với độ trễ dưới 1 giây trên trình duyệt.
*   **Dashboard Hiện đại**: Giao diện lưới (Grid) 4x4 hoặc 5x4, thiết kế Premium với Next.js và TailwindCSS.

### 2. Phân tích AI Thời gian thực
*   **Nhận diện Người**: Phát hiện người, trích xuất thuộc tính (màu áo, màu quần), định danh khuôn mặt (**FaceID**).
*   **Quản lý Phương tiện**: Phân loại xe (xe đạp, xe máy, ô tô, xe tải), nhận diện màu sắc và tự động đọc biển số (**LPR - OCR**).
*   **Cảnh báo Cháy & Khói**: Phát hiện lửa và khói theo thời gian thực với thuật toán YOLOv11 tối ưu.
*   **Cảnh báo Thông minh**: Đẩy thông báo tức thời qua WebSocket lên Dashboard.

### 3. Tìm kiếm & Quản trị
*   **Smart Search**: Tìm kiếm lịch sử theo thuộc tính đối tượng (ví dụ: "Người mặc áo xanh", "Xe tải màu trắng", "Biển số 29A-123.45").
*   **Vector Search**: Tìm kiếm khuôn mặt sử dụng **pgvector** trên PostgreSQL, cho phép so khớp hàng triệu khuôn mặt trong tích tắc.
*   **Quản lý Camera**: Giao diện thêm/sửa/xóa và cấu hình camera linh hoạt.

---

## 🛠️ Công nghệ sử dụng

*   **Frontend**: Next.js 14+ (App Router), TailwindCSS, Shadcn/UI, Lucide React, WebRTC.
*   **Backend**: Python 3.10+, FastAPI, SQLAlchemy, WebSockets, Redis.
*   **AI Engine**: 
    *   **YOLOv11**: Phát hiện vật thể, người, xe và lửa/khói.
    *   **EasyOCR/PaddleOCR**: Nhận diện biển số xe.
    *   **FaceID**: Trích xuất đặc trưng khuôn mặt (ArcFace/InsightFace).
*   **Media Server**: **go2rtc** (RTSP to WebRTC/MSE).
*   **Database**: PostgreSQL + **pgvector** (Dữ liệu cấu trúc và vector).
*   **Infrastructure**: Docker & Docker Compose.

---

## 💻 Yêu cầu hệ thống

*   **CPU**: Intel Core i7 / AMD Ryzen 7 trở lên.
*   **GPU**: NVIDIA RTX 3060 / 4060 trở lên (Khuyến nghị 8GB+ VRAM để chạy 20 luồng AI).
*   **RAM**: Tối thiểu 16GB.
*   **OS**: Windows 10/11 hoặc Linux (Ubuntu 20.04+).

---

## 🚀 Hướng dẫn khởi chạy (với Docker)

### 1. Chuẩn bị
Đảm bảo bạn đã cài đặt **Docker** và **Docker Compose**.

### 2. Cấu hình Camera
Chỉnh sửa file `media_server/go2rtc.yaml` để thêm các URL RTSP camera của bạn:
```yaml
streams:
  cam_01: rtsp://user:pass@192.168.1.10:554/stream
```

### 3. Khởi chạy toàn bộ hệ thống
Tại thư mục gốc, chạy lệnh:
```bash
docker-compose up --build
```
Lệnh này sẽ khởi chạy:
*   Database (PostgreSQL + pgvector)
*   Media Server (go2rtc)
*   Backend API (FastAPI)
*   Frontend Dashboard (Next.js)

### 4. Khởi chạy AI Engine (Standalone)
Để đạt hiệu năng tốt nhất, AI Engine có thể chạy riêng lẻ:
```bash
cd ai_engine
pip install -r requirements.txt
python stream_processor.py
```

### 5. Truy cập
Mở trình duyệt và truy cập: `http://localhost:3000`

---

## 📂 Cấu trúc thư mục
```text
├── ai_engine/          # Engine xử lý AI (YOLO, OCR, Attributes)
├── backend/            # FastAPI API Server & Logic nghiệp vụ
├── frontend/           # Next.js Dashboard & Giao diện người dùng
├── media_server/       # Cấu hình go2rtc (Streaming server)
├── data/               # Lưu trữ dữ liệu snapshot và database
└── docker-compose.yml  # Cấu hình triển khai hệ thống
```
>>>>>>> 10ef258d8bc385feeb23a8cf5b29798e999ec536

