"""
Integration module để gửi dữ liệu từ hệ thống YOLO detection
tới Flask API và cơ sở dữ liệu PostgreSQL
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import time

class DetectionDataUploader:
    """Lớp để upload dữ liệu detection vào API"""
    
    def __init__(self, api_base_url='http://localhost:5000'):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.retry_count = 3
        self.retry_delay = 1
    
    def _request_with_retry(self, method, endpoint, data=None, params=None):
        """Thực hiện request với retry logic"""
        url = f"{self.api_base_url}{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(url, json=data)
                elif method.upper() == 'GET':
                    response = self.session.get(url, params=params)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=data)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url)
                else:
                    return None
                
                if response.status_code < 400:
                    return response.json()
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
            
            except requests.exceptions.RequestException as e:
                print(f"  ⚠ Request error (attempt {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        return None
    
    def upload_person(self, person_id: str, location: str, 
                     shirt_colors: List[Dict] = None,
                     pants_colors: List[Dict] = None,
                     hair_colors: List[Dict] = None,
                     image_path: str = None,
                     confidence: float = 0.0,
                     frame_index: int = None,
                     video_source: str = None,
                     notes: str = None) -> bool:
        """
        Upload thông tin người phát hiện được
        
        Args:
            person_id: ID duy nhất của người
            location: Vị trí phát hiện (e.g., "Camera 1", "Zone A")
            shirt_colors: Danh sách màu áo [{rank, name, rgb, bgr, hsv}, ...]
            pants_colors: Danh sách màu quần
            hair_colors: Danh sách màu tóc
            image_path: Đường dẫn ảnh đã crop
            confidence: Độ tin cậy phát hiện (0-1)
            frame_index: Index frame video
            video_source: Nguồn video
            notes: Ghi chú thêm
        """
        data = {
            'person_id': person_id,
            'location': location,
            'shirt_colors': shirt_colors or [],
            'pants_colors': pants_colors or [],
            'hair_colors': hair_colors or [],
            'image_path': image_path,
            'confidence': confidence,
            'frame_index': frame_index,
            'video_source': video_source,
            'notes': notes
        }
        
        result = self._request_with_retry('POST', '/api/persons', data=data)
        
        if result:
            print(f"  ✓ Person {person_id} uploaded successfully")
            return True
        else:
            print(f"  ✗ Failed to upload person {person_id}")
            return False
    
    def upload_vehicle(self, vehicle_id: str, vehicle_type: str,
                      license_plate: str = None,
                      vehicle_colors: List[Dict] = None,
                      location: str = None,
                      image_path: str = None,
                      confidence: float = 0.0,
                      frame_index: int = None,
                      video_source: str = None,
                      notes: str = None) -> bool:
        """
        Upload thông tin phương tiện phát hiện được
        
        Args:
            vehicle_id: ID duy nhất của xe
            vehicle_type: Loại xe (car, motorcycle, bus, truck, bicycle)
            license_plate: Biển số xe
            vehicle_colors: Danh sách màu xe [{rank, name, rgb, bgr, hsv}, ...]
            location: Vị trí phát hiện
            image_path: Đường dẫn ảnh đã crop
            confidence: Độ tin cậy phát hiện
            frame_index: Index frame video
            video_source: Nguồn video
            notes: Ghi chú thêm
        """
        data = {
            'vehicle_id': vehicle_id,
            'vehicle_type': vehicle_type,
            'license_plate': license_plate,
            'vehicle_colors': vehicle_colors or [],
            'location': location,
            'image_path': image_path,
            'confidence': confidence,
            'frame_index': frame_index,
            'video_source': video_source,
            'notes': notes
        }
        
        result = self._request_with_retry('POST', '/api/vehicles', data=data)
        
        if result:
            print(f"  ✓ Vehicle {vehicle_id} uploaded successfully")
            return True
        else:
            print(f"  ✗ Failed to upload vehicle {vehicle_id}")
            return False
    
    def upload_alert(self, alert_type: str, description: str = None,
                    person_id: str = None, vehicle_id: str = None,
                    location: str = None, frame_index: int = None,
                    image_path: str = None, severity: str = 'normal',
                    status: str = 'active') -> bool:
        """
        Upload cảnh báo
        
        Args:
            alert_type: Loại cảnh báo (fire, suspicious, missing_person, etc.)
            description: Mô tả cảnh báo
            person_id: ID người liên quan (nếu có)
            vehicle_id: ID xe liên quan (nếu có)
            location: Vị trí cảnh báo
            frame_index: Index frame
            image_path: Đường dẫn ảnh
            severity: Mức độ (low, normal, high, critical)
            status: Trạng thái (active, resolved, false_alarm)
        """
        data = {
            'alert_type': alert_type,
            'description': description,
            'person_id': person_id,
            'vehicle_id': vehicle_id,
            'location': location,
            'frame_index': frame_index,
            'image_path': image_path,
            'severity': severity,
            'status': status
        }
        
        result = self._request_with_retry('POST', '/api/alerts', data=data)
        
        if result:
            print(f"  ✓ Alert {alert_type} created successfully")
            return True
        else:
            print(f"  ✗ Failed to create alert {alert_type}")
            return False
    
    def get_person(self, person_id: str) -> Dict:
        """Lấy thông tin một người"""
        result = self._request_with_retry('GET', f'/api/persons/{person_id}')
        return result
    
    def search_persons(self, location: str = None, start_time: str = None,
                      end_time: str = None, page: int = 1,
                      per_page: int = 20) -> Dict:
        """Tìm kiếm người"""
        params = {
            'location': location,
            'start_time': start_time,
            'end_time': end_time,
            'page': page,
            'per_page': per_page
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = self._request_with_retry('GET', '/api/persons', params=params)
        return result
    
    def search_vehicles(self, vehicle_type: str = None, license_plate: str = None,
                       location: str = None, start_time: str = None,
                       end_time: str = None, page: int = 1,
                       per_page: int = 20) -> Dict:
        """Tìm kiếm phương tiện"""
        params = {
            'vehicle_type': vehicle_type,
            'license_plate': license_plate,
            'location': location,
            'start_time': start_time,
            'end_time': end_time,
            'page': page,
            'per_page': per_page
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = self._request_with_retry('GET', '/api/vehicles', params=params)
        return result
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê"""
        result = self._request_with_retry('GET', '/api/statistics')
        return result
    
    def check_api_health(self) -> bool:
        """Kiểm tra xem API có hoạt động không"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


# ===== HELPER FUNCTION ĐỂ CONVERT MÀU SẮC TỪ MAIN.PY =====

def convert_color_format(color_info_list: List[Dict]) -> List[Dict]:
    """
    Convert định dạng màu từ hàm analyze_colors() trong main.py
    Định dạng input: {'rank': i, 'name': name, 'rgb': (r,g,b), 'bgr': (b,g,r), 'hsv': (h,s,v)}
    Định dạng output: {rank, name, rgb, bgr, hsv} - giống hệt cho compatibility
    """
    if not color_info_list:
        return []
    
    return [
        {
            'rank': c.get('rank'),
            'name': c.get('name'),
            'rgb': c.get('rgb'),
            'bgr': c.get('bgr'),
            'hsv': c.get('hsv')
        }
        for c in color_info_list
    ]


# ===== EXAMPLE USAGE =====

if __name__ == '__main__':
    """
    Ví dụ sử dụng:
    
    # 1. Khởi tạo uploader
    uploader = DetectionDataUploader('http://localhost:5000')
    
    # 2. Kiểm tra kết nối API
    if uploader.check_api_health():
        print("✓ API server is running")
    else:
        print("✗ API server is not running")
    
    # 3. Upload người
    uploader.upload_person(
        person_id='person_001',
        location='Camera 1',
        shirt_colors=[{'rank': 1, 'name': 'Đỏ', 'rgb': (255, 0, 0)}],
        pants_colors=[{'rank': 1, 'name': 'Xanh đen', 'rgb': (0, 51, 102)}],
        hair_colors=[{'rank': 1, 'name': 'Đen', 'rgb': (0, 0, 0)}],
        confidence=0.95,
        frame_index=100
    )
    
    # 4. Upload xe
    uploader.upload_vehicle(
        vehicle_id='vehicle_001',
        vehicle_type='car',
        license_plate='29A-12345',
        vehicle_colors=[{'rank': 1, 'name': 'Bạc', 'rgb': (192, 192, 192)}],
        location='Camera 1',
        confidence=0.92,
        frame_index=100
    )
    
    # 5. Upload cảnh báo
    uploader.upload_alert(
        alert_type='fire',
        description='Detected fire in zone A',
        location='Camera 1',
        severity='critical',
        frame_index=150
    )
    
    # 6. Tìm kiếm
    results = uploader.search_persons(location='Camera 1')
    print(results)
    """
    print("Detection Data Uploader Module - Ready to use")
