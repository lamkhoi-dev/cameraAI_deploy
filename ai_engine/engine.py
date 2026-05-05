"""
Main AI Engine - Orchestrator for all processors
Coordinates person detection, vehicle detection, fire detection, and API integration
"""

import logging
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .config import (
    MODELS, USE_GPU, GPU_DEVICE, SKIP_FRAMES, BACKEND_API_URL, API_KEY,
    LOG_LEVEL, LOG_FILE, USE_FACE_DETECTION, USE_FACE_RECOGNITION
)
from .api_client import AIResultClient
from .processors import PersonProcessor, VehicleProcessor, FireProcessor
from .processors.face_processor import FaceProcessor
from .utils import FrameGrabber
from .utils.face_matcher import get_face_matching_engine


# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AIEngine:
    """
    Main AI Engine - Tọa độ hóa tất cả processors
    Xử lý multiple cameras đồng thời với frame skipping strategy
    """
    
    def __init__(self, backend_url: str = BACKEND_API_URL, api_key: str = API_KEY):
        """
        Args:
            backend_url: Backend API URL
            api_key: API authentication key
        """
        self.backend_url = backend_url
        self.api_key = api_key
        
        # Initialize processors
        self.person_processor = None
        self.vehicle_processor = None
        self.fire_processor = None
        self.face_processor = None  # Phase 2: FaceID
        
        # Face matching engine (Phase 2)
        self.face_matcher = None
        
        # Frame grabbers for each camera
        self.frame_grabbers: Dict[str, FrameGrabber] = {}
        
        # Statistics
        self.frame_count = 0
        self.fps = 0
        self.gpu_usage_percent = 0
        
        self.running = False
    
    def initialize(self) -> bool:
        """Initialize AI engine"""
        try:
            logger.info("🚀 Initializing AI Engine...")
            
            # Load person detection model
            person_model_path = MODELS['person_pose']['name']
            self.person_processor = PersonProcessor(person_model_path)
            if not self.person_processor.load_model():
                logger.warning("⚠️  Person processor initialization failed")
            
            # Load vehicle detection model
            vehicle_model_path = MODELS['vehicle']['name']
            self.vehicle_processor = VehicleProcessor(vehicle_model_path)
            if not self.vehicle_processor.load_model():
                logger.warning("⚠️  Vehicle processor initialization failed")
            
            # Load fire detection model (optional)
            fire_model_path = MODELS['fire_smoke']['name']
            self.fire_processor = FireProcessor(fire_model_path)
            if not self.fire_processor.load_model():
                logger.warning("⚠️  Fire processor initialization failed (optional)")
            
            # Load face detection model (Phase 2 - optional)
            if USE_FACE_DETECTION and USE_FACE_RECOGNITION:
                try:
                    self.face_processor = FaceProcessor()
                    if self.face_processor.load_model():
                        self.face_matcher = get_face_matching_engine()
                        logger.info("✓ Face recognition processor loaded")
                    else:
                        logger.warning("⚠️  Face processor initialization failed (optional)")
                except Exception as e:
                    logger.warning(f"⚠️  Face processor not available: {e}")
            
            # Initialize API client
            self.api_client = AIResultClient(self.backend_url, self.api_key)
            
            logger.info("✓ AI Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ AI Engine initialization failed: {e}")
            return False
    
    def register_camera(self, camera_id: str, go2rtc_url: str = "localhost") -> bool:
        """
        Register camera for frame streaming
        
        Args:
            camera_id: Camera identifier (e.g., 'cam_01')
            go2rtc_url: go2rtc server URL
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"📷 Registering camera: {camera_id}")
            
            frame_grabber = FrameGrabber(camera_id, go2rtc_url)
            if frame_grabber.start():
                self.frame_grabbers[camera_id] = frame_grabber
                logger.info(f"✓ Camera registered: {camera_id}")
                return True
            else:
                logger.error(f"✗ Failed to start frame grabber for {camera_id}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Camera registration failed: {e}")
            return False
    
    def process_frame(self, frame, camera_id: str, frame_idx: int) -> Dict:
        """
        Process single frame through all processors
        
        Args:
            frame: BGR frame
            camera_id: Camera ID
            frame_idx: Frame index
            
        Returns:
            Dict: Combined results from all processors
        """
        results = {
            'persons': [],
            'vehicles': [],
            'alerts': [],
            'frame_idx': frame_idx,
            'camera_id': camera_id,
            'timestamp': time.time()
        }
        
        try:
            # Person detection
            if self.person_processor:
                person_results = self.person_processor.process(frame)
                results['persons'] = person_results.get('persons', [])
            
            # Vehicle detection
            if self.vehicle_processor:
                vehicle_results = self.vehicle_processor.process(frame)
                results['vehicles'] = vehicle_results.get('vehicles', [])
            
            # Fire detection
            if self.fire_processor:
                fire_results = self.fire_processor.process(frame, frame_idx)
                if fire_results.get('confirmed'):
                    results['alerts'].extend(fire_results.get('alerts', []))
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Frame processing error: {e}")
            return results
    
    async def push_results(self, results: Dict):
        """Push results to backend API"""
        try:
            if not self.api_client:
                return
            
            camera_id = results.get('camera_id')
            frame_idx = results.get('frame_idx')
            
            # Push persons
            persons = results.get('persons', [])
            if persons:
                await self.api_client.push_persons(camera_id, frame_idx, persons)
            
            # Push vehicles
            vehicles = results.get('vehicles', [])
            if vehicles:
                await self.api_client.push_vehicles(camera_id, frame_idx, vehicles)
            
            # Push alerts
            alerts = results.get('alerts', [])
            for alert in alerts:
                await self.api_client.push_alert(
                    camera_id,
                    frame_idx,
                    alert.get('type', 'unknown'),
                    'high',
                    alert.get('confidence', 0.0),
                    alert.get('bbox'),
                    alert.get('snapshot_path')
                )
            
        except Exception as e:
            logger.error(f"✗ Failed to push results: {e}")
    
    def run_single_camera(self, camera_id: str):
        """
        Process frames from single camera
        
        Args:
            camera_id: Camera ID
        """
        if camera_id not in self.frame_grabbers:
            logger.error(f"✗ Camera not registered: {camera_id}")
            return
        
        frame_grabber = self.frame_grabbers[camera_id]
        frame_idx = 0
        frame_skip_counter = 0
        
        logger.info(f"▶️  Starting frame processing for {camera_id}")
        
        try:
            while self.running:
                frame, grabbed_frame_count = frame_grabber.get_frame()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                frame_skip_counter += 1
                
                # Process every Nth frame (frame skipping)
                if frame_skip_counter >= SKIP_FRAMES:
                    frame_skip_counter = 0
                    
                    # Process frame
                    results = self.process_frame(frame, camera_id, frame_idx)
                    
                    # Push results async
                    asyncio.run(self.push_results(results))
                    
                    frame_idx += 1
                    self.frame_count += 1
                    
                    # Log statistics
                    if frame_idx % 30 == 0:
                        logger.info(f"📊 {camera_id}: {frame_idx} frames processed, "
                                  f"FPS: {frame_grabber.fps:.1f}")
                
                time.sleep(0.001)  # Small delay to prevent CPU spinning
                
        except Exception as e:
            logger.error(f"✗ Error processing {camera_id}: {e}")
        finally:
            logger.info(f"⏹️  Frame processing stopped for {camera_id}")
    
    def run(self, camera_ids: List[str]):
        """
        Run AI engine for multiple cameras
        
        Args:
            camera_ids: List of camera IDs to process
        """
        if not camera_ids:
            logger.error("✗ No cameras specified")
            return
        
        if not self.initialize():
            logger.error("✗ Failed to initialize AI engine")
            return
        
        # Register all cameras
        for camera_id in camera_ids:
            self.register_camera(camera_id)
        
        self.running = True
        logger.info(f"🚀 AI Engine running with {len(self.frame_grabbers)} cameras")
        
        try:
            # For now, process first camera (can be extended to multi-threading)
            if self.frame_grabbers:
                self.run_single_camera(camera_ids[0])
        except KeyboardInterrupt:
            logger.info("⏹️  AI Engine stopped by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown AI engine"""
        logger.info("🛑 Shutting down AI Engine...")
        
        self.running = False
        
        # Stop all frame grabbers
        for camera_id, grabber in self.frame_grabbers.items():
            grabber.stop()
        
        # Disconnect API client
        if self.api_client:
            asyncio.run(self.api_client.disconnect())
        
        # Unload models
        if self.person_processor:
            self.person_processor.unload_model()
        if self.vehicle_processor:
            self.vehicle_processor.unload_model()
        if self.fire_processor:
            self.fire_processor.unload_model()
        
        logger.info("✓ AI Engine shutdown complete")


def create_engine(backend_url: str = BACKEND_API_URL, api_key: str = API_KEY) -> AIEngine:
    """Factory function to create AI engine"""
    return AIEngine(backend_url, api_key)
