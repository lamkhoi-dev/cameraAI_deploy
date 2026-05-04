"""
Frame Grabber Module - Đọc frame từ go2rtc RTSP stream
"""

import cv2
import threading
import time
from typing import Optional
from collections import deque


class FrameGrabber:
    """
    Lấy frame từ go2rtc RTSP internal stream
    Sử dụng threading để grab frame liên tục
    """
    
    def __init__(self, camera_id: str, go2rtc_url: str = "localhost", port: int = 8554, buffer_size: int = 2):
        """
        Args:
            camera_id: Camera ID (e.g., 'cam_01')
            go2rtc_url: go2rtc server URL
            port: RTSP port (default 8554)
            buffer_size: Frame buffer size (default 2 = latest frame only)
        """
        self.camera_id = camera_id
        self.rtsp_url = f"rtsp://{go2rtc_url}:{port}/{camera_id}"
        self.buffer_size = buffer_size
        
        self.frame = None
        self.running = False
        self._lock = threading.Lock()
        self._thread = None
        self.frame_count = 0
        self.fps = 0
    
    def start(self) -> bool:
        """Start frame grabber thread"""
        if self.running:
            return False
        
        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        
        # Wait for first frame
        time.sleep(1)
        return self.frame is not None
    
    def _capture_loop(self):
        """Main capture loop - runs in background thread"""
        cap = cv2.VideoCapture(self.rtsp_url)
        
        # Optimize for low latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        fps_start = time.time()
        fps_count = 0
        
        while self.running:
            try:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    with self._lock:
                        self.frame = frame
                        self.frame_count += 1
                    
                    fps_count += 1
                    elapsed = time.time() - fps_start
                    if elapsed >= 1.0:
                        self.fps = fps_count / elapsed
                        fps_count = 0
                        fps_start = time.time()
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"⚠️  Error in frame capture loop: {e}")
                time.sleep(0.1)
        
        cap.release()
    
    def get_frame(self) -> Optional[tuple]:
        """
        Get latest frame
        
        Returns:
            Tuple: (frame, frame_count) hoặc (None, 0) nếu không có frame
        """
        with self._lock:
            if self.frame is not None:
                return self.frame.copy(), self.frame_count
            return None, 0
    
    def stop(self):
        """Stop frame grabber"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def is_alive(self) -> bool:
        """Check if grabber is running"""
        return self.running and self.frame is not None
