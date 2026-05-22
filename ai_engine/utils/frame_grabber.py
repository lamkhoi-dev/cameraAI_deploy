"""
Frame Grabber Module - Đọc frame từ go2rtc RTSP stream
"""

import cv2
import threading
import time
from typing import Optional, Any


class FrameGrabber:
    """
    Lấy frame từ go2rtc RTSP internal stream
    Sử dụng threading để grab frame liên tục
    """
    
    def __init__(self, camera_id: str, go2rtc_url: str = "localhost", port: int = 8554, buffer_size: int = 2,
                 camera_config: Optional[dict] = None, processing_fps: Optional[float] = None):
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
        self.camera_config = camera_config or {}
        self.processing_fps = self._resolve_processing_fps(processing_fps, self.camera_config)
        self.frame_interval = (1.0 / self.processing_fps) if self.processing_fps > 0 else 0.0
        
        self.frame = None
        self.running = False
        self._lock = threading.Lock()
        self._thread = None
        self.frame_count = 0
        self.fps = 0
        self._next_process_time = 0.0
    
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
        if self.processing_fps > 0:
            cap.set(cv2.CAP_PROP_FPS, self.processing_fps)
        
        fps_start = time.time()
        fps_count = 0
        
        while self.running:
            try:
                now = time.time()
                if self.frame_interval > 0 and now < self._next_process_time:
                    if cap.grab():
                        continue
                    time.sleep(0.001)
                    continue

                if self.frame_interval > 0:
                    if not cap.grab():
                        time.sleep(0.01)
                        continue
                    ret, frame = cap.retrieve()
                else:
                    ret, frame = cap.read()
                
                if ret and frame is not None:
                    self._next_process_time = time.time() + self.frame_interval if self.frame_interval > 0 else 0.0
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

    def _resolve_processing_fps(self, processing_fps: Optional[float], camera_config: dict[str, Any]) -> float:
        """Resolve configured FPS from explicit argument or camera config."""
        candidate = processing_fps
        if candidate is None:
            candidate = camera_config.get("processing_fps")
        if candidate is None:
            candidate = camera_config.get("ai_processing_fps")
        if candidate is None:
            candidate = camera_config.get("fps_target")

        try:
            return max(0.0, float(candidate or 0.0))
        except (TypeError, ValueError):
            return 0.0
    
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
