"""
Camera Management Module - RTSP/HTTPS Stream Handler
"""

import cv2
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List
from collections import deque
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraStream:
    """Quản lý stream từ một camera"""
    
    def __init__(self, camera_id: str, stream_url: str, username: str = None, 
                 password: str = None, fps: int = 30):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.username = username
        self.password = password
        self.fps = fps
        self.is_running = False
        self.is_connected = False
        self.last_frame = None
        self.last_frame_timestamp = None
        self.frame_count = 0
        self.frame_buffer = deque(maxlen=5)  # Giữ 5 frame gần nhất
        self.thread = None
        self.error_count = 0
        self.max_errors = 5
        
    def start(self):
        """Bắt đầu stream"""
        if self.is_running:
            logger.warning(f"Camera {self.camera_id} already running")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_handler, daemon=True)
        self.thread.start()
        logger.info(f"Camera {self.camera_id} stream started")
        return True
    
    def stop(self):
        """Dừng stream"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.is_connected = False
        logger.info(f"Camera {self.camera_id} stream stopped")
    
    def _build_stream_url(self) -> str:
        """Xây dựng URL stream với credentials"""
        if self.username and self.password:
            # rtsp://user:pass@host:port/path
            url_parts = self.stream_url.split('://')
            if len(url_parts) == 2:
                protocol, rest = url_parts
                return f"{protocol}://{self.username}:{self.password}@{rest}"
        return self.stream_url
    
    def _stream_handler(self):
        """Thread handler để lấy frames từ stream"""
        stream_url = self._build_stream_url()
        cap = None
        consecutive_errors = 0
        
        while self.is_running:
            try:
                if cap is None:
                    logger.info(f"Connecting to {self.camera_id}: {self.stream_url}")
                    cap = cv2.VideoCapture(stream_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Giảm buffer
                    
                    if not cap.isOpened():
                        logger.error(f"Failed to open stream: {self.camera_id}")
                        consecutive_errors += 1
                        time.sleep(2)
                        continue
                    
                    self.is_connected = True
                    self.error_count = 0
                    consecutive_errors = 0
                
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from {self.camera_id}")
                    consecutive_errors += 1
                    if consecutive_errors > self.max_errors:
                        raise Exception(f"Too many errors reading from {self.camera_id}")
                    time.sleep(0.5)
                    continue
                
                consecutive_errors = 0
                
                # Resize để giảm memory usage
                frame = cv2.resize(frame, (1280, 720))
                
                self.last_frame = frame
                self.last_frame_timestamp = datetime.utcnow()
                self.frame_count += 1
                self.frame_buffer.append(frame.copy())
                
                # FPS control
                time.sleep(1 / self.fps)
                
            except Exception as e:
                logger.error(f"Error in camera stream {self.camera_id}: {e}")
                self.is_connected = False
                self.error_count += 1
                
                if cap:
                    try:
                        cap.release()
                    except:
                        pass
                    cap = None
                
                time.sleep(2)
        
        if cap:
            cap.release()
        self.is_connected = False
    
    def get_frame_jpeg(self) -> Optional[bytes]:
        """Lấy frame hiện tại dưới dạng JPEG bytes"""
        if self.last_frame is None:
            return None
        
        try:
            ret, buffer = cv2.imencode('.jpg', self.last_frame, 
                                      [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
        
        return None
    
    def get_frame_base64(self) -> Optional[str]:
        """Lấy frame dưới dạng base64 string"""
        jpeg_bytes = self.get_frame_jpeg()
        if jpeg_bytes:
            return base64.b64encode(jpeg_bytes).decode('utf-8')
        return None
    
    def get_status(self) -> Dict:
        """Lấy status hiện tại"""
        return {
            'camera_id': self.camera_id,
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'frame_count': self.frame_count,
            'last_frame_timestamp': self.last_frame_timestamp.isoformat() if self.last_frame_timestamp else None,
            'error_count': self.error_count,
            'has_frame': self.last_frame is not None
        }


class CameraManager:
    """Quản lý nhiều camera"""
    
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.lock = threading.Lock()
    
    def add_camera(self, camera_id: str, stream_url: str, 
                   username: str = None, password: str = None, 
                   fps: int = 30) -> bool:
        """Thêm camera mới"""
        with self.lock:
            if camera_id in self.cameras:
                logger.warning(f"Camera {camera_id} already exists")
                return False
            
            camera = CameraStream(camera_id, stream_url, username, password, fps)
            self.cameras[camera_id] = camera
            logger.info(f"Added camera {camera_id}")
            return True
    
    def remove_camera(self, camera_id: str) -> bool:
        """Xóa camera"""
        with self.lock:
            if camera_id not in self.cameras:
                return False
            
            camera = self.cameras[camera_id]
            camera.stop()
            del self.cameras[camera_id]
            logger.info(f"Removed camera {camera_id}")
            return True
    
    def start_camera(self, camera_id: str) -> bool:
        """Bắt đầu stream của một camera"""
        with self.lock:
            if camera_id not in self.cameras:
                return False
            return self.cameras[camera_id].start()
    
    def stop_camera(self, camera_id: str) -> bool:
        """Dừng stream của một camera"""
        with self.lock:
            if camera_id not in self.cameras:
                return False
            self.cameras[camera_id].stop()
            return True
    
    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        """Lấy camera object"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> List[str]:
        """Lấy danh sách tất cả camera IDs"""
        return list(self.cameras.keys())
    
    def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """Lấy status của một camera"""
        camera = self.cameras.get(camera_id)
        if camera:
            return camera.get_status()
        return None
    
    def get_all_status(self) -> Dict:
        """Lấy status tất cả camera"""
        return {
            camera_id: camera.get_status()
            for camera_id, camera in self.cameras.items()
        }
    
    def get_frame_jpeg(self, camera_id: str) -> Optional[bytes]:
        """Lấy frame JPEG từ camera"""
        camera = self.cameras.get(camera_id)
        if camera:
            return camera.get_frame_jpeg()
        return None
    
    def start_all(self):
        """Bắt đầu tất cả camera"""
        with self.lock:
            for camera in self.cameras.values():
                camera.start()
            logger.info("Started all cameras")
    
    def stop_all(self):
        """Dừng tất cả camera"""
        with self.lock:
            for camera in self.cameras.values():
                camera.stop()
            logger.info("Stopped all cameras")


# Global instance
camera_manager = CameraManager()


if __name__ == '__main__':
    # Test example
    manager = CameraManager()
    
    # Thêm camera test
    manager.add_camera(
        'camera_001',
        'rtsp://admin:12345@192.168.1.100:554/stream1',
        fps=30
    )
    
    # Bắt đầu stream
    if manager.start_camera('camera_001'):
        print("Camera started")
        
        # Lấy frame sau 5 giây
        time.sleep(5)
        frame = manager.get_frame_jpeg('camera_001')
        if frame:
            print(f"Frame size: {len(frame)} bytes")
    
    # Dừng
    manager.stop_camera('camera_001')
