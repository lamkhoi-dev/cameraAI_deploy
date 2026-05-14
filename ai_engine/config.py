"""
AI Engine Configuration - Tesla P4 Optimized
"""

import os
from pathlib import Path

# ============= BASE CONFIGURATION =============
BASE_DIR = Path(__file__).parent.parent
MODEL_DIR = BASE_DIR / "ai_engine" / "models"
CROPPED_DATA_DIR = BASE_DIR / "cropped_data"

# Create directories if not exist
CROPPED_DATA_DIR.mkdir(exist_ok=True)
(CROPPED_DATA_DIR / "persons").mkdir(exist_ok=True)
(CROPPED_DATA_DIR / "vehicles").mkdir(exist_ok=True)
(CROPPED_DATA_DIR / "fire_alerts").mkdir(exist_ok=True)

# ============= DETECTION CONFIGURATION =============
CONF_THRESHOLD = 0.5                    # Minimum confidence for detections
KEYPOINT_CONF_THRESHOLD = 0.3          # Minimum confidence for keypoints
TRACK_CONF_THRESHOLD = 0.4             # Minimum confidence for tracking

# ============= MODEL CONFIGURATION =============
# YOLO Models (use YOLOv11s for Tesla P4 8GB VRAM)
MODELS = {
    "person_pose": {
        "name": "yolo11s-pose.pt",      # Replace with .engine after TensorRT export
        "input_size": 640,
        "batch_size": 1,
    },
    "vehicle": {
        "name": "yolo11s.pt",            # Replace with .engine after TensorRT export
        "input_size": 640,
        "batch_size": 1,
    },
    "fire_smoke": {
        "name": "yolo11n-fire.pt",       # Custom trained fire detection model
        "input_size": 640,
        "batch_size": 1,
    },
    "plate_detect": {
        "name": "yolo11n-plate.pt",      # Custom trained license plate detection
        "input_size": 640,
        "batch_size": 1,
    }
}

# ============= VRAM & PERFORMANCE =============
USE_GPU = True
GPU_DEVICE = 0
USE_TENSORRT = False  # Set to True after exporting .engine files
USE_FP16 = True       # Use FP16 precision for TensorRT (faster but less accurate)
USE_INT8 = False      # Use INT8 quantization (fastest but least accurate)

# Tesla P4 VRAM Budget (8GB total)
# YOLO11s-pose: ~0.8GB (TensorRT FP16)
# YOLO11s: ~0.8GB (TensorRT FP16)
# YOLO11n-fire: ~0.3GB (TensorRT FP16)
# YOLO11n-plate: ~0.3GB (TensorRT FP16)
# CUDA overhead + buffers: ~1.0GB
# Total: ~3.2GB (plenty of headroom on 8GB card)

# ============= FRAME PROCESSING =============
SKIP_FRAMES = 3                         # Process every Nth frame (2-3fps at 30fps input)
FRAME_RESIZE_SCALE = 0.5               # Resize frame for processing (0.5 = 50%)
FRAME_BUFFER_SIZE = 10                 # Maximum frames to buffer

# ============= TRACKING CONFIGURATION =============
TRACK_PERSISTENT_FRAMES = 30           # Keep track for N frames even without detection
TRACK_MAX_AGE = 60                     # Maximum age of track without detection

# ============= COLOR ANALYSIS =============
NUM_COLORS_PERSON = 3                  # Number of dominant colors for person clothing
NUM_COLORS_VEHICLE = 5                 # Number of dominant colors for vehicle
COLOR_ANALYSIS_MARGIN = 0.15           # Remove N% from edges to avoid background

# ============= FIRE DETECTION =============
FIRE_TEMPORAL_THRESHOLD = 3            # Number of consecutive frames to confirm fire
FIRE_MINIMUM_AREA = 100                # Minimum pixel area to consider as fire

# ============= LICENSE PLATE OCR =====
USE_PLATE_DETECTION = True             # Enable license plate detection
USE_OCR = True                         # Enable optical character recognition
OCR_CONFIDENCE_THRESHOLD = 0.7         # Minimum confidence for valid OCR result

# ============= FACE RECOGNITION (Phase 2) =============
USE_FACE_DETECTION = True              # Enable face detection
USE_FACE_RECOGNITION = True            # Enable face embedding extraction
FACE_DETECTION_CONFIDENCE = 0.5        # Minimum confidence for face detection
FACE_EMBEDDING_DIM = 512               # InsightFace ArcFace embedding dimension
FACE_SIMILARITY_THRESHOLD = 0.6        # Threshold for face matching (0.0-1.0)
FACE_EMBEDDING_MODEL = "buffalo_l"     # InsightFace model: buffalo_s, buffalo_m, buffalo_l
FACE_MIN_FACE_SIZE = 10                # Minimum face size in pixels
FACE_VECTOR_DB_TYPE = "memory"         # memory, redis, or pgvector (future)
KNOWN_FACES_DB_DIR = BASE_DIR / "known_faces"  # Directory to store known face embeddings
KNOWN_FACES_DB_DIR.mkdir(exist_ok=True)

# ============= API CONFIGURATION =============
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")
API_TIMEOUT = 10                       # API request timeout in seconds

# ============= GO2RTC CONFIGURATION =============
GO2RTC_URL = os.getenv("GO2RTC_URL", "localhost")
GO2RTC_RTSP_PORT = 8554
GO2RTC_HTTP_PORT = 1984

# ============= COCO VEHICLE CLASSES =============
VEHICLE_CLASSES = {
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# ============= LOGGING CONFIGURATION =============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "ai_engine.log"
LOG_FILE.parent.mkdir(exist_ok=True)
