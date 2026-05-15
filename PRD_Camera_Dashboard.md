# 📋 PRD — Hệ Thống Camera Streaming & Dashboard
## Phạm Vi: Camera Connection · Streaming · Dashboard · Management

> **Version**: 1.0 | **Ngày**: 02/05/2026  
> **Phạm vi tài liệu này**: Chỉ bao gồm phần kết nối camera, streaming, dashboard UI và quản lý hệ thống.  
> **KHÔNG bao gồm**: Core AI (nhận diện người, xe, cháy — do dev AI phụ trách).

---

## 1. PHÂN CHIA TRÁCH NHIỆM

| Phần | Người phụ trách | Ghi chú |
|---|---|---|
| **Camera Connection & Streaming** | **Bạn** | RTSP/HTTPS ingest, MJPEG/WebRTC output |
| **Dashboard UI** | **Bạn** | Lưới camera, quản lý, xem lịch sử |
| **Camera Management API** | **Bạn** | CRUD camera, start/stop stream |
| **Database Schema (cameras table)** | **Bạn** | Quản lý cấu hình camera |
| **AI Engine (YOLO, fire, attributes)** | Dev AI | Đọc frame từ stream, trả kết quả qua API |
| **AI Result Storage API** | **Bạn** | Nhận kết quả từ dev AI, lưu DB + push WebSocket |
| **Search/History UI** | **Bạn** | Hiển thị kết quả do dev AI tạo ra |

---

## 2. TỔNG QUAN KIẾN TRÚC

```
┌─────────────────────────────────────────────────────────┐
│                    PHẦN CỦA BẠN                         │
│                                                         │
│  Cameras (RTSP) ──► go2rtc ──► WebRTC/HLS ──► Browser  │
│        │                                         ▲      │
│        ▼                                         │      │
│   Camera Manager                           Dashboard     │
│   (Python/FastAPI)                         (Next.js)    │
│        │                                         ▲      │
│        ▼                                         │      │
│   PostgreSQL (cameras, events, persons, vehicles)│      │
│        │                                         │      │
│        └─────────────────────────────────────────┘      │
│                          ▲                              │
└──────────────────────────│──────────────────────────────┘
                           │  REST API (nhận kết quả AI)
                ┌──────────┴──────────┐
                │   PHẦN DEV AI       │
                │  AI Engine          │
                │  (YOLO, OCR, Fire)  │
                └─────────────────────┘
```

### Stack Kỹ Thuật

| Layer | Technology | Lý do chọn |
|---|---|---|
| **Streaming Server** | go2rtc | RTSP → WebRTC, độ trễ < 1s, miễn phí |
| **Backend API** | FastAPI (Python) | Async, performance tốt hơn Flask |
| **Database** | PostgreSQL | Hiện tại đã có schema |
| **Frontend** | Next.js 14 + TailwindCSS | Modern, responsive |
| **WebSocket** | FastAPI WebSocket | Real-time updates |
| **Camera Ingest** | OpenCV / FFmpeg | Đọc RTSP frame cho AI |

---

## 3. YÊU CẦU CHỨC NĂNG CHI TIẾT

---

### 3.1 MODULE: CAMERA MANAGEMENT

#### 3.1.1 Thêm / Sửa / Xóa Camera

**Màn hình**: Settings > Camera Management

| Field | Type | Bắt buộc | Mô tả |
|---|---|---|---|
| `camera_id` | string | ✅ | ID duy nhất, tự sinh hoặc nhập tay |
| `name` | string | ✅ | Tên hiển thị (VD: "Cổng chính", "Tầng 2") |
| `location` | string | ✅ | Vị trí lắp đặt |
| `stream_url` | string | ✅ | URL RTSP/HTTPS (VD: `rtsp://admin:pass@192.168.1.10:554/stream1`) |
| `username` | string | ❌ | Tên đăng nhập camera (nếu URL không embed) |
| `password` | string | ❌ | Mật khẩu camera |
| `protocol` | enum | ✅ | `rtsp` / `https` / `http` |
| `resolution` | string | ❌ | VD: `1920x1080` |
| `fps` | int | ✅ | Default: 30 |
| `enable_ai` | bool | ✅ | Bật/tắt AI engine cho camera này |
| `notes` | text | ❌ | Ghi chú tự do |

**Validation rules:**
- `stream_url` phải bắt đầu bằng `rtsp://`, `https://`, hoặc `http://`
- `fps` trong khoảng 1-60
- Không cho phép 2 camera cùng `camera_id` hoặc cùng `stream_url`

**Sau khi tạo camera:**
1. Hệ thống tự động thêm stream vào go2rtc config
2. Thử kết nối, cập nhật `connection_status`
3. Nếu `enable_ai = true`, notify AI engine qua API

---

#### 3.1.2 Test Kết Nối Camera

- Button **"Test Connection"** trên form add/edit
- Backend thử `cv2.VideoCapture(url)`, grab 1 frame
- Trả về: `{ success: bool, latency_ms: int, resolution: string, thumbnail: base64 }`
- Timeout: 10 giây
- Hiển thị thumbnail preview ngay trong form nếu thành công

---

#### 3.1.3 Danh Sách Camera

**Hiển thị columns:**
- Tên camera + location
- Status badge: 🟢 Online / 🔴 Offline / 🟡 Connecting
- Resolution + FPS thực tế
- Frame cuối cùng nhận được (timestamp)
- Toggle bật/tắt AI
- Actions: Preview · Edit · Delete · Start/Stop

**Tính năng:**
- Filter theo location, status
- Sort theo tên, status, time
- Refresh status tự động mỗi 30 giây

---

### 3.2 MODULE: LIVE DASHBOARD

#### 3.2.1 Camera Grid

**Layout options (user có thể chọn):**
- 1x1 (1 camera full screen)
- 2x2 (4 cameras)
- 3x3 (9 cameras)  
- 4x4 (16 cameras)
- 4x5 (20 cameras)

**Mỗi ô camera hiển thị:**
```
┌─────────────────────────────────┐
│  [Camera Name]      [🟢 Online] │
│                                 │
│   < Live Video Stream >         │
│                                 │
│  [AI Overlay: boxes + labels]   │
│─────────────────────────────────│
│  👤 2 người  🚗 1 xe  ⏱ 02:13  │
└─────────────────────────────────┘
```

**Stream Protocol:**
- **Ưu tiên 1**: WebRTC (qua go2rtc) — độ trễ < 1s
- **Fallback**: HLS (qua go2rtc) — độ trễ ~3-5s
- **Fallback cuối**: MJPEG (Flask) — độ trễ cao, dùng khi không có go2rtc

**Tính năng dashboard:**
- Click vào ô camera → Phóng to full screen
- Pause/Resume từng camera
- Snapshot: chụp ảnh frame hiện tại (download PNG)
- Fullscreen mode (F11 hoặc button)
- Auto-reconnect khi mất kết nối (retry mỗi 5s, max 3 lần, sau đó show error)

---

#### 3.2.2 Statistics Panel (Sidebar)

Hiển thị realtime, cập nhật qua WebSocket:

```
┌────────────────────────┐
│ 📊 Hôm nay             │
│ 👤 Người phát hiện: 47 │
│ 🚗 Xe phát hiện: 23    │
│ 🔥 Cảnh báo: 0         │
│                        │
│ 📹 Camera (16/20 online│
│ ■■■■■■■■■■■■■■□□□□□    │
│                        │
│ ⚡ Cảnh báo gần đây    │
│ • 14:32 - Cháy Zone C  │
│ • 13:15 - Xe lạ Gate A │
└────────────────────────┘
```

---

#### 3.2.3 Alert Panel

Khi AI engine push alert qua WebSocket:
- Toast notification xuất hiện góc phải màn hình
- Badge đỏ trên icon Alert
- Alert panel collapsible bên cạnh dashboard
- Click alert → highlight camera tương ứng + zoom

**Alert types (do dev AI định nghĩa, UI chỉ render):**
- `fire` → icon 🔥, màu đỏ
- `smoke` → icon 💨, màu cam
- `suspicious` → icon ⚠️, màu vàng
- `vehicle_unknown` → icon 🚗, màu tím

---

### 3.3 MODULE: STREAMING SERVER (go2rtc)

#### 3.3.1 Setup go2rtc

go2rtc là binary độc lập, chạy song song với backend:

```yaml
# go2rtc.yaml (auto-generated bởi backend)
api:
  listen: ":1984"

streams:
  cam_01: rtsp://admin:pass@192.168.1.10:554/stream1
  cam_02: rtsp://admin:pass@192.168.1.11:554/stream1
  # ... tự động thêm khi add camera
```

**Endpoints go2rtc:**
- WebRTC player: `http://localhost:1984/stream.html?src=cam_01`
- HLS: `http://localhost:1984/stream.m3u8?src=cam_01`
- API: `http://localhost:1984/api/streams` — lấy danh sách streams

#### 3.3.2 Dynamic Stream Management

Khi user thêm/xóa camera qua Dashboard:
1. Backend ghi file `go2rtc.yaml`
2. Gọi `POST http://localhost:1984/api/streams` để hot-reload (không cần restart)
3. Cập nhật DB

**Khi AI engine cần frame:**
- AI engine subscribe vào go2rtc stream: `rtsp://localhost:8554/cam_01`
- go2rtc forward stream RTSP nội bộ — không tốn bandwidth đọc camera 2 lần

---

### 3.4 MODULE: BACKEND API

#### 3.4.1 Camera Endpoints

```
POST   /api/cameras              # Tạo camera mới
GET    /api/cameras              # Danh sách (filter: location, status, page)
GET    /api/cameras/{id}         # Chi tiết 1 camera
PUT    /api/cameras/{id}         # Cập nhật camera
DELETE /api/cameras/{id}         # Xóa camera
POST   /api/cameras/{id}/test    # Test kết nối, trả thumbnail
POST   /api/cameras/{id}/start   # Bắt đầu stream
POST   /api/cameras/{id}/stop    # Dừng stream
GET    /api/cameras/{id}/status  # Lấy trạng thái realtime
GET    /api/cameras/status/all   # Tất cả camera status
```

#### 3.4.2 Stream Endpoints (proxy to go2rtc)

```
GET    /api/stream/{cam_id}/webrtc    # WebRTC SDP offer/answer proxy
GET    /api/stream/{cam_id}/hls       # HLS playlist proxy
GET    /api/stream/{cam_id}/snapshot  # Chụp ảnh tức thì (JPEG)
GET    /api/stream/{cam_id}/mjpeg     # MJPEG stream fallback
```

#### 3.4.3 AI Result Endpoints (nhận từ dev AI)

> **Các endpoint này bạn tạo, dev AI sẽ gọi vào để push kết quả**

```
POST   /api/ai/persons           # Nhận kết quả nhận diện người
POST   /api/ai/vehicles          # Nhận kết quả nhận diện xe
POST   /api/ai/alerts            # Nhận cảnh báo cháy/khói/suspicious
POST   /api/ai/heartbeat         # AI engine ping, báo còn sống
GET    /api/ai/config/{cam_id}   # AI engine lấy config cho camera
```

**Contract với dev AI — POST /api/ai/persons:**
```json
{
  "camera_id": "cam_01",
  "frame_index": 1234,
  "timestamp": "2026-05-02T10:30:00Z",
  "persons": [
    {
      "track_id": 5,
      "confidence": 0.92,
      "bbox": [100, 200, 300, 450],
      "attributes": {
        "shirt_color": [{"rank": 1, "name": "Trắng", "rgb": [255,255,255]}],
        "pants_color": [{"rank": 1, "name": "Đen", "rgb": [0,0,0]}],
        "hair_color":  [{"rank": 1, "name": "Đen", "rgb": [10,10,10]}]
      },
      "crop_image_base64": "..."
    }
  ]
}
```

**Contract — POST /api/ai/alerts:**
```json
{
  "camera_id": "cam_01",
  "frame_index": 5678,
  "timestamp": "2026-05-02T10:35:00Z",
  "alert_type": "fire",
  "severity": "high",
  "description": "Fire detected in lower-left zone",
  "confidence": 0.87,
  "bbox": [50, 300, 400, 600],
  "snapshot_base64": "..."
}
```

#### 3.4.4 Statistics & History Endpoints

```
GET    /api/statistics                     # Tổng quan hôm nay
GET    /api/persons                        # Lịch sử người (filter + paginate)
GET    /api/persons/{id}                   # Chi tiết 1 người
GET    /api/vehicles                       # Lịch sử xe
GET    /api/alerts                         # Lịch sử cảnh báo
PUT    /api/alerts/{id}/resolve            # Đánh dấu đã xử lý
GET    /api/events/timeline?camera_id=...  # Timeline sự kiện theo camera
```

#### 3.4.5 WebSocket Events

**Server → Client (Dashboard):**
```
new_person_detected   { camera_id, person_data }
new_vehicle_detected  { camera_id, vehicle_data }
new_alert             { camera_id, alert_data }
camera_status_changed { camera_id, status }
ai_engine_status      { status: online|offline }
stats_update          { total_persons, total_vehicles, active_alerts }
```

---

### 3.5 MODULE: SEARCH & HISTORY UI

#### 3.5.1 Màn hình History / Search

**Filter options:**
- Chọn Camera (multi-select)
- Khoảng thời gian (date range picker)
- Loại đối tượng: Người / Xe / Cảnh báo
- Màu áo (cho người)
- Loại xe (xe máy, ô tô, xe tải...)
- Trạng thái alert (active / resolved)

**Kết quả hiển thị dạng:**
- Card grid (ảnh thumbnail + thông tin)
- Timeline view
- Pagination (20 items/page)

**Mỗi card người hiển thị:**
- Ảnh crop full body
- Camera + Timestamp
- Màu áo / quần / tóc
- Confidence score

---

### 3.6 MODULE: AUTHENTICATION

**Phase 1 — Đơn giản (2 roles):**

| Role | Quyền |
|---|---|
| `admin` | Toàn quyền: thêm/sửa/xóa camera, xem dashboard, xem history, quản lý users |
| `operator` | Chỉ xem: dashboard live, xem history, không thay đổi config |

**Implementation:**
- JWT token, expire 24h
- Login page: `/login`
- Protected routes: tất cả routes trừ `/login` và `/health`
- Token lưu trong `httpOnly cookie`

**Endpoints:**
```
POST  /api/auth/login    { username, password } → { token }
POST  /api/auth/logout
GET   /api/auth/me       → { user_info }
```

**Default accounts (thay đổi trong .env):**
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123   # Bắt buộc đổi khi deploy
OPERATOR_USERNAME=operator
OPERATOR_PASSWORD=op123
```

---

## 4. DATABASE SCHEMA

### Bảng cameras (do bạn quản lý)

```sql
CREATE TABLE cameras (
    id              SERIAL PRIMARY KEY,
    camera_id       VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    location        VARCHAR(255) NOT NULL,
    stream_url      VARCHAR(500) NOT NULL,
    protocol        VARCHAR(20) DEFAULT 'rtsp',
    resolution      VARCHAR(50),
    fps             INTEGER DEFAULT 30,
    username        VARCHAR(100),
    password_enc    VARCHAR(255),         -- encrypted, không lưu plaintext
    is_active       BOOLEAN DEFAULT TRUE,
    enable_ai       BOOLEAN DEFAULT TRUE,
    connection_status VARCHAR(20) DEFAULT 'unknown',  -- connected/disconnected/error
    last_frame_at   TIMESTAMP,
    go2rtc_stream_name VARCHAR(100),      -- tên stream trong go2rtc
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### Bảng persons, vehicles, alerts (do bạn tạo, dev AI push data)

```sql
-- Giữ nguyên schema hiện tại trong models.py
-- Thêm index trên camera_id để search nhanh hơn
CREATE INDEX idx_persons_camera ON persons(video_source);
CREATE INDEX idx_vehicles_camera ON vehicles(video_source);
CREATE INDEX idx_alerts_camera ON alerts(camera_id);  -- thêm field này
```

### Bảng users (mới)

```sql
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20) DEFAULT 'operator',  -- admin / operator
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

---

## 5. CẤU TRÚC THƯ MỤC DỰ ÁN (Đề xuất)

```
Camera-Tracking-AI/
├── backend/                    # FastAPI backend (của bạn)
│   ├── main.py                 # App entry point
│   ├── config.py               # Settings từ .env
│   ├── database.py             # DB connection
│   ├── models/
│   │   ├── camera.py
│   │   ├── person.py
│   │   ├── vehicle.py
│   │   └── alert.py
│   ├── routers/
│   │   ├── cameras.py          # /api/cameras/*
│   │   ├── streams.py          # /api/stream/*
│   │   ├── ai_ingest.py        # /api/ai/* (nhận từ dev AI)
│   │   ├── history.py          # /api/persons, /api/vehicles...
│   │   ├── auth.py             # /api/auth/*
│   │   └── stats.py            # /api/statistics
│   ├── services/
│   │   ├── camera_service.py   # Business logic
│   │   ├── go2rtc_service.py   # Quản lý go2rtc config
│   │   └── stream_service.py   # Stream management
│   └── requirements.txt
│
├── frontend/                   # Next.js (của bạn)
│   ├── app/
│   │   ├── (auth)/login/
│   │   ├── dashboard/          # Live camera grid
│   │   ├── cameras/            # Camera management
│   │   ├── history/            # Search & history
│   │   └── alerts/             # Alert management
│   ├── components/
│   │   ├── CameraGrid/
│   │   ├── CameraCard/
│   │   ├── StreamPlayer/       # WebRTC/HLS/MJPEG player
│   │   ├── AlertPanel/
│   │   └── StatsPanel/
│   └── package.json
│
├── media_server/               # go2rtc (binary)
│   ├── go2rtc               # Binary (download)
│   └── go2rtc.yaml             # Auto-generated
│
├── ai_engine/                  # PHẦN DEV AI (không động vào)
│   └── README.md               # Interface contract
│
├── docker-compose.yml
└── .env.example
```

---

## 6. DOCKER COMPOSE

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_detection
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  go2rtc:
    image: alexxit/go2rtc
    network_mode: host
    volumes:
      - ./media_server/go2rtc.yaml:/config/go2rtc.yaml
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres/ai_detection
      GO2RTC_URL: http://localhost:1984
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - go2rtc

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_GO2RTC_URL: http://localhost:1984
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

---

## 7. FILE .env.example

```env
# Database
DB_USER=postgres
DB_PASSWORD=changeme_in_production
DATABASE_URL=postgresql://postgres:changeme@localhost:5432/ai_detection

# Backend
SECRET_KEY=change-this-secret-key-in-production
JWT_EXPIRE_HOURS=24
API_HOST=0.0.0.0
API_PORT=8000

# go2rtc
GO2RTC_URL=http://localhost:1984
GO2RTC_CONFIG_PATH=./media_server/go2rtc.yaml

# Default users (đổi ngay sau setup)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@2026!
OPERATOR_USERNAME=operator
OPERATOR_PASSWORD=Operator@2026!

# AI Engine (URL để backend giao tiếp với AI)
AI_ENGINE_URL=http://localhost:9000
AI_ENGINE_API_KEY=ai-engine-secret-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GO2RTC_URL=http://localhost:1984
```

---

## 8. TIÊU CHÍ NGHIỆM THU (Acceptance Criteria)

### ✅ Kết nối Camera

- [ ] Thêm camera RTSP thành công, thumbnail hiển thị trong form
- [ ] Test connection trả về kết quả trong vòng 10 giây
- [ ] Xóa camera → stream dừng, go2rtc config cập nhật
- [ ] Khi camera mất kết nối → status tự động đổi thành Offline

### ✅ Streaming Dashboard

- [ ] Dashboard hiển thị đồng thời ít nhất 16 camera
- [ ] Độ trễ WebRTC stream < 1 giây (đo bằng đồng hồ thực)
- [ ] Click phóng to camera → stream mượt, không giật
- [ ] Khi mất 1 camera → ô đó hiển thị "Offline", các ô khác không ảnh hưởng
- [ ] Snapshot camera hoạt động, tải về file PNG

### ✅ Camera Management

- [ ] CRUD camera hoạt động đầy đủ
- [ ] Validation form: URL sai format → báo lỗi rõ ràng
- [ ] Danh sách camera có filter và sort
- [ ] Start/Stop stream từng camera

### ✅ Authentication

- [ ] Login với admin → vào được tất cả trang
- [ ] Login với operator → không thấy menu Camera Management
- [ ] Token hết hạn 24h → redirect về login
- [ ] URL trực tiếp khi chưa login → redirect về login

### ✅ Integration với AI Engine

- [ ] Backend nhận POST /api/ai/persons → lưu DB + push WebSocket tới dashboard
- [ ] Backend nhận POST /api/ai/alerts → hiển thị alert notification trên dashboard
- [ ] Dashboard hiển thị bounding box overlay trên camera tương ứng (nếu AI gửi bbox)

### ✅ Search & History

- [ ] Filter theo camera + time range → trả kết quả đúng
- [ ] Pagination hoạt động
- [ ] Hiển thị ảnh thumbnail người/xe

---

## 9. PHẠM VI KHÔNG LÀM (Out of Scope)

> Những mục sau do **dev AI phụ trách**, bạn chỉ cần nhận kết quả qua API:

- Thuật toán nhận diện người (YOLO, pose estimation)
- Phân tích màu áo/quần/tóc bằng K-means
- Phân loại xe (COCO model)
- OCR đọc biển số
- Fire/smoke detection model
- FaceID (Phase 2)
- Vector search với FAISS/pgvector (Phase 2)

---

## 10. TIMELINE ĐỀ XUẤT

| Tuần | Nội dung |
|---|---|
| **Tuần 1** | Setup repo, Docker Compose, go2rtc, DB schema, backend skeleton |
| **Tuần 2** | Camera CRUD API + go2rtc integration + Test connection feature |
| **Tuần 3** | Dashboard UI: camera grid, stream player (WebRTC/HLS/MJPEG) |
| **Tuần 4** | Auth (login/JWT), AI ingest endpoints, WebSocket events |
| **Tuần 5** | History/Search UI, Alert panel, Polish & bug fix |
| **Tuần 6** | Integration test với AI engine, Acceptance criteria, Handover |
