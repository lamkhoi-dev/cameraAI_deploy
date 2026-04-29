# 🚀 Quick Start Guide

## 5 Phút để Có Hệ Thống Hoàn Chỉnh

### Bước 1: Cài PostgreSQL (nếu chưa có)

**Windows**: https://www.postgresql.org/download/windows/
- Download và cài
- Password cho user `postgres`: `123456`
- Port: `5432`

**hoặc Docker** (nhanh hơn):
```bash
docker run --name ai-postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 -d postgres
```

### Bước 2: Cài Python Dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Khởi tạo Database

```bash
python init_db.py
```

Expected output:
```
✓ Database 'ai_detection' created successfully
✓ All tables created successfully
✓ Sample data inserted successfully
```

### Bước 4: Chạy Flask Server

```bash
python app.py
```

Expected output:
```
* Running on http://0.0.0.0:5000
* Serving Flask app 'app'
```

### Bước 5: Test (Terminal mới)

```bash
python client_example.py
```

✓ **DONE!** System is running!

---

## API Endpoints

**Mở browser và test:**

- API Docs: http://localhost:5000/
- Statistics: http://localhost:5000/api/statistics
- Persons: http://localhost:5000/api/persons
- Vehicles: http://localhost:5000/api/vehicles
- Alerts: http://localhost:5000/api/alerts

---

## Tích hợp vào main.py

Xem `INTEGRATION_GUIDE.py` hoặc bản tóm tắt:

```python
from db_integration import DetectionDataUploader

uploader = DetectionDataUploader('http://localhost:5000')

# Khi phát hiện người
uploader.upload_person(
    person_id='person_001',
    location='Camera 1',
    shirt_colors=[...],
    confidence=0.95,
    frame_index=100
)

# Khi phát hiện xe
uploader.upload_vehicle(
    vehicle_id='vehicle_001',
    vehicle_type='car',
    license_plate='29A-12345',
    confidence=0.92,
    frame_index=100
)

# Khi có cảnh báo
uploader.upload_alert(
    alert_type='fire',
    severity='critical',
    location='Camera 1'
)
```

---

## Cơ Sở Dữ Liệu

3 bảng chính:
1. **persons** - Thông tin người (ID, location, quần áo màu, tóc, vv)
2. **vehicles** - Thông tin xe (type, biển số, màu, vị trí)
3. **alerts** - Cảnh báo (type, status, severity)

**Toàn bộ dữ liệu có index** để search/filter nhanh ⚡

---

## Tính Năng

✅ CRUD - Create, Read, Update, Delete  
✅ Search & Filter - Theo location, time, vehicle type, plate  
✅ Real-time Updates - WebSocket push notifications  
✅ Statistics - Dashboard stats  
✅ Batch Upload - Upload nhiều data cùng lúc  
✅ Error Handling - Retry logic, connection checks  

---

## Tìm Kiếm Ví Dụ

### Tìm người
```
/api/persons?location=Camera%201&page=1&per_page=20
/api/persons?start_time=2024-01-01T00:00:00&end_time=2024-01-02T23:59:59
```

### Tìm xe
```
/api/vehicles?vehicle_type=car
/api/vehicles?license_plate=29A
/api/vehicles?location=Camera%201
```

### Tìm cảnh báo
```
/api/alerts?alert_type=fire&status=active
/api/alerts?severity=critical
```

---

## Troubleshooting

| Vấn đề | Giải pháp |
|--------|----------|
| PostgreSQL connection error | Kiểm tra .env DATABASE_URL, đảm bảo PostgreSQL chạy |
| API "Address already in use" | Port 5000 bị chiếm, chạy lệnh: `lsof -i :5000` rồi kill process |
| "No module named flask" | Chạy: `pip install -r requirements.txt` |
| Database already exists | Xóa cũ: `python -c "from app import db; db.drop_all()"` |

---

## Tiếp Theo

1. ✅ Hệ thống hoạt động → Tích hợp vào main.py
2. 📊 Tạo web dashboard để visualize
3. 🔔 Setup notifications/alerts
4. 📈 Thêm machine learning models
5. 🌐 Deploy production (Heroku, AWS, etc.)

---

## Liên Hệ & Support

- Docs: README.md
- Integration: INTEGRATION_GUIDE.py
- Examples: client_example.py
- Code: models.py, app.py, db_integration.py

---

**Happy Coding! 🎉**
