"""
Client Example - Sử dụng API và WebSocket để nhận real-time updates
"""

import requests
import json
import time
from datetime import datetime
from db_integration import DetectionDataUploader

def print_separator(title=""):
    """In dòng phân cách"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print("="*60)

def example_basic_crud():
    """Ví dụ: CRUD cơ bản"""
    print_separator("EXAMPLE 1: CRUD Operations")
    
    uploader = DetectionDataUploader('http://localhost:5000')
    
    # Kiểm tra kết nối
    if not uploader.check_api_health():
        print("✗ API server is not running!")
        print("  Please run: python app.py")
        return
    
    print("✓ API server is running\n")
    
    # 1. Upload người
    print("[1] Creating person...")
    uploader.upload_person(
        person_id='person_demo_001',
        location='Camera Main Gate',
        shirt_colors=[
            {'rank': 1, 'name': 'Trắng', 'rgb': (255, 255, 255)},
            {'rank': 2, 'name': 'Xanh', 'rgb': (0, 100, 200)}
        ],
        pants_colors=[
            {'rank': 1, 'name': 'Xanh đen', 'rgb': (0, 51, 102)}
        ],
        hair_colors=[
            {'rank': 1, 'name': 'Đen', 'rgb': (0, 0, 0)}
        ],
        confidence=0.95,
        frame_index=100,
        notes='Demo person from client'
    )
    
    # 2. Upload xe
    print("\n[2] Creating vehicle...")
    uploader.upload_vehicle(
        vehicle_id='vehicle_demo_001',
        vehicle_type='car',
        license_plate='29A-99999',
        vehicle_colors=[
            {'rank': 1, 'name': 'Bạc', 'rgb': (192, 192, 192)},
            {'rank': 2, 'name': 'Đen', 'rgb': (0, 0, 0)}
        ],
        location='Camera Main Gate',
        confidence=0.92,
        frame_index=100,
        notes='Demo vehicle from client'
    )
    
    # 3. Tạo cảnh báo
    print("\n[3] Creating alert...")
    uploader.upload_alert(
        alert_type='suspicious',
        description='Suspicious person detected near gate',
        person_id='person_demo_001',
        location='Camera Main Gate',
        severity='normal',
        frame_index=100
    )
    
    # 4. Lấy thông tin người
    print("\n[4] Getting person details...")
    person = uploader.get_person('person_demo_001')
    if person:
        print(f"  Person ID: {person['person_id']}")
        print(f"  Location: {person['location']}")
        print(f"  Confidence: {person['confidence']}")
        print(f"  Shirt colors: {person['shirt_colors']}")
    
    # 5. Tìm kiếm
    print("\n[5] Searching persons by location...")
    results = uploader.search_persons(location='Camera')
    if results and 'data' in results:
        print(f"  Found {len(results['data'])} persons")
        for person in results['data'][:3]:  # Hiện 3 cái đầu
            print(f"    - {person['person_id']}: {person['location']}")
    
    # 6. Lấy thống kê
    print("\n[6] Getting statistics...")
    stats = uploader.get_statistics()
    if stats:
        print(f"  Total persons: {stats['total_persons']}")
        print(f"  Total vehicles: {stats['total_vehicles']}")
        print(f"  Active alerts: {stats['active_alerts']}")

def example_search_and_filter():
    """Ví dụ: Tìm kiếm và lọc"""
    print_separator("EXAMPLE 2: Search & Filter")
    
    uploader = DetectionDataUploader('http://localhost:5000')
    
    if not uploader.check_api_health():
        print("✗ API server is not running!")
        return
    
    # Tìm kiếm xe theo loại
    print("[1] Finding all cars...")
    results = uploader.search_vehicles(vehicle_type='car', per_page=5)
    if results and 'data' in results:
        print(f"  Found {results['total']} cars (showing first {len(results['data'])})")
        for vehicle in results['data']:
            plate = vehicle['license_plate'] or 'Unknown'
            print(f"    - {vehicle['vehicle_id']}: {vehicle['vehicle_type'].upper()} ({plate})")
    
    # Tìm kiếm theo vị trí
    print("\n[2] Finding all vehicles in 'Camera'...")
    results = uploader.search_vehicles(location='Camera', per_page=5)
    if results and 'data' in results:
        print(f"  Found {results['total']} vehicles")
        for vehicle in results['data']:
            print(f"    - {vehicle['vehicle_id']}: {vehicle['location']}")
    
    # Tìm kiếm theo biển số
    print("\n[3] Finding vehicles by license plate...")
    results = uploader.search_vehicles(license_plate='29A', per_page=5)
    if results and 'data' in results:
        print(f"  Found {results['total']} vehicles with '29A' in plate")

def example_websocket_listener():
    """Ví dụ: Lắng nghe real-time updates qua WebSocket"""
    print_separator("EXAMPLE 3: WebSocket Real-time Updates")
    
    print("WebSocket example - requires python-socketio client")
    print("\nCode example:")
    print("""
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')
    sio.emit('subscribe_persons')
    sio.emit('subscribe_vehicles')
    sio.emit('subscribe_alerts')

@sio.on('new_person')
def on_new_person(data):
    print(f'New person detected: {data["person_id"]}')

@sio.on('new_vehicle')
def on_new_vehicle(data):
    print(f'New vehicle detected: {data["vehicle_id"]}')

@sio.on('new_alert')
def on_new_alert(data):
    print(f'New alert: {data["alert_type"]}')

@sio.event
def disconnect():
    print('Disconnected from server')

sio.connect('http://localhost:5000')
sio.wait()
    """)

def example_batch_upload():
    """Ví dụ: Batch upload nhiều dữ liệu"""
    print_separator("EXAMPLE 4: Batch Upload")
    
    uploader = DetectionDataUploader('http://localhost:5000')
    
    if not uploader.check_api_health():
        print("✗ API server is not running!")
        return
    
    print("Simulating YOLO detection results and batch upload...\n")
    
    # Giả lập dữ liệu detection
    detections = [
        {
            'type': 'person',
            'id': f'person_batch_{i:03d}',
            'location': f'Camera {(i % 3) + 1}',
            'confidence': 0.85 + (i * 0.01) % 0.15,
            'colors': {
                'shirt': [{'rank': 1, 'name': 'Màu sắc áo', 'rgb': (100 + i*10, 150, 200)}],
                'pants': [{'rank': 1, 'name': 'Xanh đen', 'rgb': (0, 51, 102)}],
                'hair': [{'rank': 1, 'name': 'Đen', 'rgb': (0, 0, 0)}]
            }
        }
        for i in range(3)
    ]
    
    # Upload từng detection
    for detection in detections:
        uploader.upload_person(
            person_id=detection['id'],
            location=detection['location'],
            shirt_colors=detection['colors']['shirt'],
            pants_colors=detection['colors']['pants'],
            hair_colors=detection['colors']['hair'],
            confidence=detection['confidence'],
            frame_index=100 + detections.index(detection) * 10
        )
        time.sleep(0.2)  # Delay tránh spam
    
    print("\n✓ Batch upload completed!")
    
    # Kiểm tra
    results = uploader.search_persons(per_page=10)
    if results and 'data' in results:
        print(f"Total persons in database: {results['total']}")

def example_error_handling():
    """Ví dụ: Xử lý lỗi"""
    print_separator("EXAMPLE 5: Error Handling")
    
    uploader = DetectionDataUploader('http://localhost:5001')  # Port sai
    
    print("[1] Testing with incorrect server...")
    if not uploader.check_api_health():
        print("  ✗ Server not reachable (as expected)")
    
    # Khôi phục port đúng
    uploader = DetectionDataUploader('http://localhost:5000')
    
    print("\n[2] Testing with correct server...")
    if uploader.check_api_health():
        print("  ✓ Server is reachable")
    
    print("\n[3] Testing with invalid data...")
    # Missing required field
    result = uploader._request_with_retry('POST', '/api/persons', data={'location': 'Test'})
    if result is None or 'error' in str(result):
        print("  ✓ Error handling works (invalid data rejected)")

def example_rest_api_calls():
    """Ví dụ: Direct REST API calls"""
    print_separator("EXAMPLE 6: Direct REST API Calls")
    
    base_url = 'http://localhost:5000'
    
    try:
        # 1. Check server
        response = requests.get(f'{base_url}/health', timeout=5)
        if response.status_code == 200:
            print("✓ Server is healthy\n")
        
        # 2. Get API documentation
        print("[1] API Root Endpoint:")
        response = requests.get(f'{base_url}/', timeout=5)
        data = response.json()
        print(f"  Message: {data.get('message')}")
        print(f"  Version: {data.get('version')}")
        
        # 3. List statistics
        print("\n[2] Getting statistics...")
        response = requests.get(f'{base_url}/api/statistics', timeout=5)
        stats = response.json()
        print(f"  Total persons: {stats['total_persons']}")
        print(f"  Total vehicles: {stats['total_vehicles']}")
        print(f"  Active alerts: {stats['active_alerts']}")
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server")
        print("  Please run: python app.py")
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    """Chạy tất cả ví dụ"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + "  AI Detection System - Client Examples".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    examples = [
        ("Basic CRUD Operations", example_basic_crud),
        ("Search & Filter", example_search_and_filter),
        ("WebSocket Real-time Updates", example_websocket_listener),
        ("Batch Upload", example_batch_upload),
        ("Error Handling", example_error_handling),
        ("REST API Calls", example_rest_api_calls),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, func in examples:
        try:
            func()
            time.sleep(1)
        except Exception as e:
            print(f"✗ Error in {name}: {e}\n")
    
    print_separator("Summary")
    print("""
✓ All examples completed!

Next steps:
1. Customize examples to your needs
2. Integrate with main.py YOLO detection
3. Create a web dashboard to visualize data
4. Set up real-time alerts and notifications

For more information, see:
- INTEGRATION_GUIDE.py
- app.py (API server)
- db_integration.py (Database client)
    """)

if __name__ == '__main__':
    main()
