"""
Hướng dẫn tích hợp Flask API và Database vào hệ thống YOLO detection

Bây giờ main.py có thể gửi dữ liệu phát hiện được tới cơ sở dữ liệu
và web server tự động thông qua db_integration.py

CÔNG VIỆC CÓ THỂ LÀM:
1. Lưu trữ thông tin người/xe phát hiện vào database
2. Tìm kiếm người/xe dựa trên màu sắc, vị trí, thời gian
3. Tạo cảnh báo thời gian thực
4. Xem thống kê trực quan qua web interface
"""

# ===== CÁCH 1: Sửa đổi hàm save_person() trong main.py =====

"""
Từ: main.py (dòng ~500)

    def save_person(keypoints, frame_idx, center_pos):
        # Code hiện tại...
        # Lưu ảnh, phân tích màu, v.v...

Sang: Sử dụng db_integration

    from db_integration import DetectionDataUploader
    
    # Khởi tạo uploader (1 lần duy nhất)
    uploader = DetectionDataUploader('http://localhost:5000')
    
    def save_person(keypoints, frame_idx, center_pos):
        # Code hiện tại...
        # Lưu ảnh, phân tích màu, v.v...
        
        # THÊM: Upload lên database
        if uploader.check_api_health():
            uploader.upload_person(
                person_id=f'person_{center_pos[2]}',
                location=f'Camera 1',
                shirt_colors=shirt_colors_info,
                pants_colors=pants_colors_info,
                hair_colors=hair_colors_info,
                image_path=image_file_path,
                confidence=confidence_score,
                frame_index=frame_idx,
                video_source='video1.mov'
            )
"""

# ===== CÁCH 2: Sửa đổi hàm save_vehicle() trong main.py =====

"""
    from db_integration import DetectionDataUploader
    
    uploader = DetectionDataUploader('http://localhost:5000')
    
    def save_vehicle(vehicle, frame_idx):
        # Code hiện tại...
        # Lưu ảnh xe, phân tích màu, nhận diện biển số, v.v...
        
        # THÊM: Upload lên database
        if uploader.check_api_health():
            uploader.upload_vehicle(
                vehicle_id=f'vehicle_{frame_idx}_{vehicle["confidence"]:.2f}',
                vehicle_type=vehicle['type'],
                license_plate=detected_plate_text,
                vehicle_colors=vehicle_colors_info,
                location='Camera 1',
                image_path=image_file_path,
                confidence=vehicle['confidence'],
                frame_index=frame_idx,
                video_source='video1.mov'
            )
"""

# ===== CÁCH 3: Thêm phát hiện cảnh báo =====

"""
    from db_integration import DetectionDataUploader
    
    uploader = DetectionDataUploader('http://localhost:5000')
    
    # Trong hàm chính, nếu phát hiện cháy/khói
    if fire_detected:
        uploader.upload_alert(
            alert_type='fire',
            description='Fire/Smoke detected in frame',
            location='Camera 1',
            frame_index=frame_idx,
            image_path=fire_image_path,
            severity='critical',
            status='active'
        )
"""

# ===== CÀI ĐẶT TOÀN BỘ HỆ THỐNG =====

"""
1. CÀI ĐẶT POSTGRESQL
   - Windows: https://www.postgresql.org/download/windows/
   - Hoặc dùng Docker: docker run --name postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 postgres
   - Tạo user/database nếu cần

2. CÀI ĐẶT PYTHON PACKAGES
   pip install -r requirements.txt

3. KHỞI TẠO DATABASE
   python init_db.py
   
   Output:
   ✓ Database 'ai_detection' created successfully
   ✓ All tables created successfully
   ✓ Sample data inserted successfully

4. CHẠY FLASK API SERVER
   python app.py
   
   Output:
   * Running on http://0.0.0.0:5000

5. (TÙY CHỌN) CHẠY YOLO DETECTION VỚI INTEGRATION
   - Sửa main.py thêm code từ trên
   - python main.py
   - Dữ liệu tự động lưu vào database

6. TRUY CẬP WEB DASHBOARD
   - API Documentation: http://localhost:5000/
   - API Endpoints: http://localhost:5000/api/persons, /api/vehicles, /api/alerts
   - WebSocket: ws://localhost:5000 (cho real-time updates)
"""

# ===== API ENDPOINTS CHÍNH =====

"""
PERSONS (Người)
================
POST   /api/persons                    - Tạo/Cập nhật người
GET    /api/persons                    - Liệt kê người (với filter)
GET    /api/persons/<person_id>        - Lấy thông tin một người
PUT    /api/persons/<person_id>        - Cập nhật thông tin người
DELETE /api/persons/<person_id>        - Xóa thông tin người

VEHICLES (Phương tiện)
=====================
POST   /api/vehicles                   - Tạo/Cập nhật xe
GET    /api/vehicles                   - Liệt kê xe (với filter)
GET    /api/vehicles/<vehicle_id>      - Lấy thông tin một xe
PUT    /api/vehicles/<vehicle_id>      - Cập nhật thông tin xe
DELETE /api/vehicles/<vehicle_id>      - Xóa thông tin xe

ALERTS (Cảnh báo)
=================
POST   /api/alerts                     - Tạo cảnh báo
GET    /api/alerts                     - Liệt kê cảnh báo (với filter)
PUT    /api/alerts/<alert_id>          - Cập nhật cảnh báo
DELETE /api/alerts/<alert_id>          - Xóa cảnh báo

STATISTICS
==========
GET    /api/statistics                 - Lấy thống kê chung

HEALTH
======
GET    /health                         - Kiểm tra sức khỏe server
"""

# ===== VÍ DỤ SỬ DỤNG CURL =====

"""
# 1. Tạo người
curl -X POST http://localhost:5000/api/persons \\
  -H "Content-Type: application/json" \\
  -d '{
    "person_id": "person_001",
    "location": "Camera 1",
    "shirt_colors": [{"rank": 1, "name": "Trắng", "rgb": [255, 255, 255]}],
    "pants_colors": [{"rank": 1, "name": "Xanh đen", "rgb": [0, 51, 102]}],
    "hair_colors": [{"rank": 1, "name": "Đen", "rgb": [0, 0, 0]}],
    "confidence": 0.95,
    "frame_index": 1
  }'

# 2. Liệt kê người
curl http://localhost:5000/api/persons?location=Camera%201&page=1&per_page=10

# 3. Tạo xe
curl -X POST http://localhost:5000/api/vehicles \\
  -H "Content-Type: application/json" \\
  -d '{
    "vehicle_id": "vehicle_001",
    "vehicle_type": "car",
    "license_plate": "29A-12345",
    "vehicle_colors": [{"rank": 1, "name": "Bạc", "rgb": [192, 192, 192]}],
    "location": "Camera 1",
    "confidence": 0.94
  }'

# 4. Tạo cảnh báo
curl -X POST http://localhost:5000/api/alerts \\
  -H "Content-Type: application/json" \\
  -d '{
    "alert_type": "fire",
    "description": "Fire detected",
    "location": "Camera 1",
    "severity": "critical"
  }'

# 5. Lấy thống kê
curl http://localhost:5000/api/statistics

# 6. WebSocket connection (real-time updates)
# Client có thể kết nối ws://localhost:5000
# Gửi event "subscribe_persons" để nhận updates về người phát hiện mới
"""

# ===== SEARCH & FILTER CAPABILITIES =====

"""
SEARCH NGƯỜI:
GET /api/persons?
  location=Camera%201                  - Tìm theo vị trí
  &start_time=2024-01-01T00:00:00      - Từ thời gian
  &end_time=2024-01-02T23:59:59        - Đến thời gian
  &page=1                              - Trang (mặc định 1)
  &per_page=20                         - Số lượng per trang (mặc định 20)

SEARCH XE:
GET /api/vehicles?
  vehicle_type=car                     - Loại xe (car, motorcycle, bus, truck, bicycle)
  &license_plate=29A-12345             - Biển số (tìm kiếm gần đúng)
  &location=Camera%201                 - Vị trí
  &start_time=2024-01-01T00:00:00      - Từ thời gian
  &end_time=2024-01-02T23:59:59        - Đến thời gian

SEARCH CẢNH BÁO:
GET /api/alerts?
  alert_type=fire                      - Loại cảnh báo
  &status=active                       - Trạng thái (active, resolved, false_alarm)
  &severity=critical                   - Mức độ (low, normal, high, critical)
  &start_time=2024-01-01T00:00:00      - Từ thời gian
  &end_time=2024-01-02T23:59:59        - Đến thời gian
"""

# ===== DATABASE SCHEMA =====

"""
TABLE persons
--------------
- id (PRIMARY KEY)
- person_id (UNIQUE INDEX)
- location (INDEX)
- timestamp (INDEX)
- image_path
- shirt_colors (JSON)
- pants_colors (JSON)
- hair_colors (JSON)
- confidence
- frame_index
- video_source
- notes
- created_at, updated_at

TABLE vehicles
---------------
- id (PRIMARY KEY)
- vehicle_id (UNIQUE INDEX)
- vehicle_type (INDEX)
- license_plate (UNIQUE INDEX)
- vehicle_colors (JSON)
- location (INDEX)
- timestamp (INDEX)
- image_path
- confidence
- frame_index
- video_source
- notes
- created_at, updated_at

TABLE alerts
-------------
- id (PRIMARY KEY)
- alert_type (INDEX)
- person_id (FOREIGN KEY, INDEX)
- vehicle_id (FOREIGN KEY, INDEX)
- description
- location
- timestamp (INDEX)
- frame_index
- image_path
- severity
- status (INDEX)
- created_at, updated_at
"""

print(__doc__)
