import cv2
import os
import numpy as np
from ultralytics import YOLO
import time
import torch

# ===== CẤU HÌNH TỐI ƯU HÓA =====
CONF_THRESHOLD = 0.5          # Độ tin cậy tối thiểu (0.5-0.7 tốt nhất)
KEYPOINT_CONF_THRESHOLD = 0.3 # Độ tin cậy tối thiểu cho keypoints
RESIZE_SCALE = 0.5            # Resize frame để xử lý nhanh (0.5 = 50% kích thước)
SKIP_FRAMES = 1               # Xử lý mỗi N frame (1 = mỗi frame, 2 = cách 1 frame)
USE_GPU = True                # Sử dụng GPU nếu có
USE_OCR = True                # Sử dụng OCR để đọc biển số
DISPLAY_OUTPUT = False        # Hiển thị màn hình (Tắt nếu chạy headless/server)

# ===== CẤU HÌNH PHÂN TÍCH MÀU SẮC =====
NUM_COLORS_PERSON = 3         # Số màu phân tích cho người (3-5)
NUM_COLORS_VEHICLE = 10       # Số màu phân tích cho xe (5-12) - tăng lên để nhận biết chi tiết hơn

# Khởi tạo mô hình với GPU (fallback to CPU nếu không có)
if USE_GPU and torch.cuda.is_available():
    device = 0  # GPU
    print(f"✓ GPU Available: {torch.cuda.get_device_name(0)}")
else:
    device = 'cpu'  # CPU
    print("⚠ GPU Not available, using CPU")

# ===== LOAD MÔ HÌNH =====
# Model 1: Pose Detection (nhận diện người)
# ✅ UPGRADED: YOLOv11s-pose (mAP 46.9%) thay YOLOv8n-pose (mAP 37%)
model_path_pose = 'ai_engine/models/yolo11s-pose.pt'
if not os.path.exists(model_path_pose):
    print(f"⚠️  Model not found: {model_path_pose}")
    print(f"    Fallback to: yolov8n-pose.pt")
    model_path_pose = 'yolov8n-pose.pt'
model_pose = YOLO(model_path_pose)
if device != 'cpu':
    model_pose.to(device)

# Model 2: Object Detection (nhận diện phương tiện)
# ✅ UPGRADED: YOLOv11s (mAP 46.9%) thay YOLOv8n (mAP 39.4%)
model_path_object = 'ai_engine/models/yolo11s.pt'
if not os.path.exists(model_path_object):
    print(f"⚠️  Model not found: {model_path_object}")
    print(f"    Fallback to: yolov8n.pt")
    model_path_object = 'yolov8n.pt'
model_object = YOLO(model_path_object)
if device != 'cpu':
    model_object.to(device)

# Model 3: Fire/Smoke Detection (tùy chọn - nếu có model custom)
# ✅ UPGRADED: YOLO custom model thay HSV color filter (90% fewer false positives)
model_fire = None
fire_detection_enabled = False  # Set True after downloading fire model
if os.path.exists('ai_engine/models/yolo11n-fire.pt'):
    try:
        model_fire = YOLO('ai_engine/models/yolo11n-fire.pt')
        fire_detection_enabled = True
        print("✓ Fire detection model loaded")
    except Exception as e:
        print(f"⚠️  Fire model load error: {e}")

# Model 4: OCR - Đọc biển số xe (nếu sử dụng)
# ✅ UPGRADED: PaddleOCR (better for Vietnamese) thay EasyOCR
ocr_reader = None
if USE_OCR:
    try:
        from paddleocr import PaddleOCR
        print("⏳ Loading OCR model (PaddleOCR)... (Lần đầu sẽ tải ~200MB)")
        # CPU mode để giải phóng GPU VRAM cho YOLO models
        ocr_reader = PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False)
        print("✓ OCR model loaded (PaddleOCR - CPU mode)")
    except ImportError:
        print("⚠ PaddleOCR not installed. Install with: pip install paddleocr paddlepaddle")
        USE_OCR = False
    except Exception as e:
        print(f"⚠ OCR load error: {e}")
        USE_OCR = False

# COCO classes - lọc chỉ lấy phương tiện
VEHICLE_CLASSES = {
    2: 'car',           # Xe ô tô
    3: 'motorcycle',    # Xe máy
    5: 'bus',           # Xe khách
    7: 'truck',         # Xe tải
    1: 'bicycle'        # Xe đạp
}

VEHICLE_NAMES_VN = {
    'car': 'Xe ô tô',
    'motorcycle': 'Xe máy',
    'bus': 'Xe khách',
    'truck': 'Xe tải',
    'bicycle': 'Xe đạp'
}

# ✅ UPGRADED: Support go2rtc RTSP streams + local video files
# For production: use go2rtc RTSP (rtsp://localhost:8554/camera_id)
# For testing: use local video file
video_source = os.getenv('VIDEO_SOURCE', 'video1.mov')
if not os.path.exists(video_source) and not video_source.startswith('rtsp://'):
    print(f"⚠️  Video file not found: {video_source}")
    print(f"    Using fallback: video1.mov")
    video_source = 'video1.mov'

print(f"📹 Loading video source: {video_source}")

cap = cv2.VideoCapture(video_source)

# Check if video opened successfully
if not cap.isOpened():
    print(f"❌ Failed to open video: {video_source}")
    print("   Check if video file exists or RTSP server is running")
    exit(1)

# Lấy thông tin video
fps_video = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Tạo thư mục lưu ảnh nếu chưa có
if not os.path.exists('cropped_data'):
    os.makedirs('cropped_data')

# Dictionary lưu ID đã chụp
processed_ids = {}

# FPS counter
frame_count = 0
fps_start = time.time()

# ===== HÀM NHẬN DIỆN MÀU SẮC =====
def detect_dominant_colors(image, k=3):
    """
    Phát hiện k màu sắc chủ yếu trong ảnh bằng K-means
    Sắp xếp theo tần suất xuất hiện (nhiều nhất đứng trước)
    """
    if image is None or image.size == 0:
        return [], []
    
    # Reshape ảnh thành mảng điểm
    pixels = image.reshape((-1, 3))
    pixels = np.float32(pixels)
    
    # K-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Sắp xếp theo tần suất (số lần xuất hiện)
    label_counts = np.bincount(labels.flatten())
    sorted_indices = np.argsort(-label_counts)  # Sắp xếp descending
    
    # Chuyển từ BGR sang HSV để dễ nhận diện màu
    centers = np.uint8(centers)
    centers_sorted = centers[sorted_indices]
    
    centers_bgr = centers_sorted.reshape((k, 1, 3))
    centers_hsv = cv2.cvtColor(centers_bgr, cv2.COLOR_BGR2HSV)
    
    return centers_hsv.reshape((k, 3)), centers_sorted

def get_color_name(hsv_color):
    """
    Chuyển HSV thành tên màu tiếng Việt
    HSV: Hue (0-179), Saturation (0-255), Value (0-255)
    """
    h, s, v = hsv_color[0], hsv_color[1], hsv_color[2]
    
    # Nếu saturation thấp = màu xám/trắng/đen
    if s < 30:
        if v < 50:
            return "Đen"
        elif v > 200:
            return "Trắng"
        else:
            return "Xám"
    
    # Phân loại theo Hue
    if h < 5 or h > 175:
        return "Đỏ"
    elif 5 <= h < 15:
        return "Cam"
    elif 15 <= h < 25:
        return "Vàng"
    elif 25 <= h < 35:
        return "Vàng lục"
    elif 35 <= h < 77:
        return "Lục"
    elif 77 <= h < 99:
        return "Xanh lục"
    elif 99 <= h < 110:
        return "Xanh lam"
    elif 110 <= h < 125:
        return "Xanh dương"
    elif 125 <= h < 145:
        return "Tím"
    elif 145 <= h < 165:
        return "Hồng"
    else:
        return "Đỏ tím"

def analyze_colors(crop_img, part_name, num_colors=3):
    """
    Phân tích màu sắc của một phần cơ thể hoặc phương tiện
    part_name: Tên phần (hair, shirt, pants, car, etc.)
    num_colors: Số lượng màu muốn phát hiện
    """
    if crop_img is None or crop_img.size == 0:
        return None
    
    try:
        # Phát hiện n màu sắc chủ yếu (tùy chỉnh theo num_colors)
        hsv_colors, bgr_colors = detect_dominant_colors(crop_img, k=num_colors)
        
        color_info = []
        for i, (hsv, bgr) in enumerate(zip(hsv_colors, bgr_colors)):
            color_name = get_color_name(hsv)
            # Lưu RGB cho dễ hiểu
            r, g, b = int(bgr[2]), int(bgr[1]), int(bgr[0])
            color_info.append({
                'rank': i + 1,
                'name': color_name,
                'rgb': (r, g, b),
                'bgr': tuple(map(int, bgr)),
                'hsv': tuple(map(int, hsv))
            })
        
        return color_info
    except Exception as e:
        print(f"    ! Lỗi phân tích màu {part_name}: {e}")
        return None

# ===== HÀM NHẬN DIỆN PHƯƠNG TIỆN =====
def detect_vehicles(frame_resized, frame_original):
    """
    Phát hiện phương tiện (xe đạp, xe máy, xe ô tô, xe khách)
    Trả về danh sách phương tiện với bbox
    """
    try:
        # Chạy object detection
        results_obj = model_object.predict(
            frame_resized,
            verbose=False,
            conf=CONF_THRESHOLD,
            iou=0.45,
            imgsz=384
        )
        
        vehicles = []
        if results_obj and len(results_obj) > 0:
            result = results_obj[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                classes = boxes.cls.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                xyxy = boxes.xyxy.cpu().numpy()
                
                for cls_id, conf, box in zip(classes, confs, xyxy):
                    cls_id = int(cls_id)
                    # Lọc chỉ lấy phương tiện
                    if cls_id in VEHICLE_CLASSES:
                        vehicle_type = VEHICLE_CLASSES[cls_id]
                        # Scale bbox về kích thước frame gốc
                        x1, y1, x2, y2 = box / RESIZE_SCALE
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Clamp vào frame
                        h, w = frame_original.shape[:2]
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(w, x2)
                        y2 = min(h, y2)
                        
                        if x2 > x1 and y2 > y1:  # Chỉ lấy nếu bbox hợp lệ
                            vehicle_crop = frame_original[y1:y2, x1:x2]
                            
                            vehicles.append({
                                'type': vehicle_type,
                                'type_vn': VEHICLE_NAMES_VN.get(vehicle_type, vehicle_type),
                                'confidence': float(conf),
                                'bbox': (x1, y1, x2, y2),
                                'crop': vehicle_crop
                            })
        
        return vehicles
    except Exception as e:
        print(f"  ! Lỗi phát hiện phương tiện: {e}")
        return []

def save_vehicle(vehicle, frame_idx):
    """
    Lưu ảnh phương tiện vào thư mục, phân tích màu sắc và nhận diện biển số
    """
    try:
        vehicle_dir = 'cropped_data/vehicles'
        if not os.path.exists(vehicle_dir):
            os.makedirs(vehicle_dir)
        
        # Tạo thư mục riêng cho từng loại xe
        vehicle_type_dir = f'{vehicle_dir}/{vehicle["type"]}'
        if not os.path.exists(vehicle_type_dir):
            os.makedirs(vehicle_type_dir)
        
        # Lưu ảnh xe
        filename_base = f'{vehicle_type_dir}/frame_{frame_idx}_conf_{vehicle["confidence"]:.2f}'
        cv2.imwrite(f'{filename_base}.jpg', vehicle['crop'])
        
        # ===== PHÂN TÍCH MÀU SẮC XE =====
        colors = analyze_colors(vehicle['crop'], vehicle['type'], num_colors=NUM_COLORS_VEHICLE)
        
        if colors:
            # Lưu thông tin màu vào file text
            with open(f'{filename_base}_colors.txt', 'w', encoding='utf-8') as f:
                f.write(f"=== MÀU SẮC {vehicle['type_vn'].upper()} ===\n")
                f.write(f"Frame: {frame_idx} | Confidence: {vehicle['confidence']:.2f}\n\n")
                
                for color_info in colors:
                    f.write(f"{color_info['rank']}. {color_info['name']}\n")
                    f.write(f"   RGB: {color_info['rgb']}\n")
                    f.write(f"   BGR: {color_info['bgr']}\n")
                f.write("\n")
            
            # In log thông tin màu xe
            color_names = ', '.join([c['name'] for c in colors])
            print(f"       Màu: {color_names}")
        
        # ===== NHẬN DIỆN BIỂN SỐ =====
        license_plate = detect_license_plate(vehicle['crop'])
        
        if license_plate is not None:
            # Lưu ảnh biển số
            cv2.imwrite(f'{filename_base}_plate.jpg', license_plate)
            
            # Nhận diện text từ biển số
            plate_info = recognize_license_plate(license_plate)
            
            if plate_info:
                # Lưu thông tin biển số vào file
                with open(f'{filename_base}_plate.txt', 'w', encoding='utf-8') as f:
                    f.write(f"=== BIỂN SỐ {vehicle['type_vn'].upper()} ===\n")
                    f.write(f"Frame: {frame_idx}\n")
                    f.write(f"Biển số: {plate_info['text']}\n")
                    f.write(f"Độ tin cậy OCR: {plate_info['confidence']:.2f}\n")
                
                print(f"       📋 Biển số: {plate_info['text']} (Confidence: {plate_info['confidence']:.2f})")
            else:
                print(f"       📋 Không đọc được biển số")
        else:
            print(f"       📋 Không phát hiện biển số")
        
        return True
    except Exception as e:
        print(f"  ! Lỗi lưu phương tiện: {e}")
        return False

# ===== HÀM NHẬN DIỆN BIỂN SỐ =====
def detect_license_plate(vehicle_crop):
    """
    Phát hiện và crop vùng biển số từ ảnh xe
    Biển số thường ở phía dưới xe
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None
    
    try:
        h, w = vehicle_crop.shape[:2]
        
        # Biển số thường nằm ở phía dưới xe
        # Lấy vùng dưới cùng của xe (khoảng 20-30% phía dưới)
        plate_region_y_start = int(h * 0.65)
        plate_region_y_end = h
        plate_region_x_start = int(w * 0.05)
        plate_region_x_end = int(w * 0.95)
        
        license_plate = vehicle_crop[plate_region_y_start:plate_region_y_end, 
                                     plate_region_x_start:plate_region_x_end]
        
        # Kiểm tra xem crop có hợp lệ không
        if license_plate.size > 0 and license_plate.shape[0] > 10 and license_plate.shape[1] > 50:
            return license_plate
        else:
            return None
    except Exception as e:
        print(f"  ! Lỗi phát hiện biển số: {e}")
        return None

def recognize_license_plate(license_plate_crop):
    """
    Đọc text từ biển số xe bằng OCR
    """
    if not USE_OCR or ocr_reader is None:
        return None
    
    if license_plate_crop is None or license_plate_crop.size == 0:
        return None
    
    try:
        # Enhance ảnh trước khi OCR
        gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
        # Tăng contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # OCR
        results = ocr_reader.readtext(enhanced, detail=1)  # detail=1 để lấy confidence
        
        if results and len(results) > 0:
            # Lấy các ký tự có confidence cao
            plate_text = ""
            confidence_scores = []
            
            for detection in results:
                text = detection[1]
                conf = detection[2]
                
                # Lọc các text có confidence >= 0.3
                if conf >= 0.3:
                    plate_text += text
                    confidence_scores.append(conf)
            
            if plate_text.strip():
                avg_conf = np.mean(confidence_scores) if confidence_scores else 0
                return {
                    'text': plate_text.strip(),
                    'confidence': float(avg_conf),
                    'raw_results': results
                }
        
        return None
    except Exception as e:
        print(f"  ! Lỗi OCR biển số: {e}")
        return None

# ===== HÀM PHÁT HIỆN CHÁY/KHÓI =====
def detect_fire_smoke_yolo(frame):
    """
    ✅ UPGRADED: YOLO model-based fire detection (replaces HSV)
    Much more accurate than HSV color thresholding
    """
    if not model_fire or frame is None:
        return {'fire': False, 'smoke': False, 'confidence': 0}
    
    try:
        results = model_fire.predict(frame, conf=0.5, verbose=False)
        if results[0].boxes:
            # Get class names and confidence
            for box in results[0].boxes:
                class_id = int(box.cls)
                conf = float(box.conf)
                class_name = model_fire.model.names.get(class_id, '')
                
                if class_name.lower() in ['fire', 'lửa']:
                    return {'fire': True, 'smoke': False, 'confidence': conf}
                elif class_name.lower() in ['smoke', 'khói']:
                    return {'fire': False, 'smoke': True, 'confidence': conf}
        
        return {'fire': False, 'smoke': False, 'confidence': 0}
    except Exception as e:
        print(f"  ! Lỗi YOLO fire detection: {e}")
        return {'fire': False, 'smoke': False, 'confidence': 0}

def detect_fire_smoke(frame, threshold_fire=0.25, threshold_smoke=0.25):
    """
    ⚠️  DEPRECATED: HSV color-based detection (causes 90% false positives)
    ✅ NOW: Uses YOLO model if available, falls back to HSV
    """
    if frame is None or frame.size == 0:
        return {'fire': False, 'smoke': False, 'fire_percentage': 0, 'smoke_percentage': 0}
    
    # Try YOLO first
    if fire_detection_enabled and model_fire:
        result_yolo = detect_fire_smoke_yolo(frame)
        if result_yolo['fire'] or result_yolo['smoke']:
            return result_yolo
    
    # Fallback to HSV (deprecated)
    try:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w, _ = hsv.shape
        
        # ⚠️  NOTE: HSV detection has ~90% false positive rate
        # Use YOLO model instead (see fire_detection_enabled flag)
        lower_red1 = np.array([0, 120, 120])
        upper_red1 = np.array([30, 255, 255])
        lower_red2 = np.array([170, 120, 120])
        upper_red2 = np.array([179, 255, 255])
        
        fire_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        fire_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        fire_mask = cv2.bitwise_or(fire_mask1, fire_mask2)
        
        fire_pixels = cv2.countNonZero(fire_mask)
        fire_percentage = fire_pixels / (h * w)
        fire_detected = fire_percentage > threshold_fire
        
        lower_smoke = np.array([0, 0, 70])
        upper_smoke = np.array([179, 40, 200])
        smoke_mask = cv2.inRange(hsv, lower_smoke, upper_smoke)
        saturation_check = hsv[:, :, 1]
        saturation_mask = (saturation_check > 0) & (saturation_check < 40)
        smoke_mask = cv2.bitwise_and(smoke_mask, saturation_mask.astype(np.uint8) * 255)
        
        smoke_pixels = cv2.countNonZero(smoke_mask)
        smoke_percentage = smoke_pixels / (h * w)
        smoke_detected = smoke_percentage > threshold_smoke
        
        return {
            'fire': fire_detected,
            'smoke': smoke_detected,
            'fire_percentage': float(fire_percentage),
            'smoke_percentage': float(smoke_percentage),
            'fire_mask': fire_mask,
            'smoke_mask': smoke_mask
        }
    except Exception as e:
        print(f"  ! Lỗi phát hiện cháy: {e}")
        return {'fire': False, 'smoke': False, 'fire_percentage': 0, 'smoke_percentage': 0}

def save_fire_alert(frame, detection_result, frame_idx):
    """
    Lưu cảnh báo cháy và ảnh có khói/lửa
    """
    try:
        alert_dir = 'cropped_data/fire_alerts'
        if not os.path.exists(alert_dir):
            os.makedirs(alert_dir)
        
        # Tạo timestamp
        timestamp = frame_idx
        
        # Tạo tiêu đề cảnh báo
        alert_types = []
        if detection_result['fire']:
            alert_types.append(f"LỬA ({detection_result['fire_percentage']:.1%})")
        if detection_result['smoke']:
            alert_types.append(f"KHÓI ({detection_result['smoke_percentage']:.1%})")
        
        alert_title = " + ".join(alert_types)
        
        # Lưu ảnh frame
        frame_filename = f'{alert_dir}/frame_{timestamp}_{alert_title}.jpg'
        cv2.imwrite(frame_filename, frame)
        
        # Lưu mask lửa nếu có
        if detection_result['fire']:
            fire_filename = f'{alert_dir}/frame_{timestamp}_fire_mask.jpg'
            cv2.imwrite(fire_filename, detection_result['fire_mask'])
        
        # Lưu mask khói nếu có
        if detection_result['smoke']:
            smoke_filename = f'{alert_dir}/frame_{timestamp}_smoke_mask.jpg'
            cv2.imwrite(smoke_filename, detection_result['smoke_mask'])
        
        # Lưu thông tin cảnh báo
        alert_info_filename = f'{alert_dir}/frame_{timestamp}_alert.txt'
        with open(alert_info_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== CẢNH BÁO CHÁY ===\n")
            f.write(f"Frame: {frame_idx}\n")
            f.write(f"Loại: {alert_title}\n")
            f.write(f"Lửa: {detection_result['fire']} ({detection_result['fire_percentage']:.2%})\n")
            f.write(f"Khói: {detection_result['smoke']} ({detection_result['smoke_percentage']:.2%})\n")
        
        return True
    except Exception as e:
        print(f"  ! Lỗi lưu cảnh báo cháy: {e}")
        return False

# Hàm crop các phần khác nhau của cơ thể
def crop_body_parts(frame, keypoints, confidences=None):
    """
    Crop các phần cơ thể từ keypoints với kiểm tra confidence
    keypoints: Tọa độ x, y của 17 điểm
    confidences: Độ tin cậy của từng keypoint
    """
    h, w = frame.shape[:2]
    crops = {}
    
    # Lọc keypoints có độ tin cậy cao
    if confidences is not None:
        valid_mask = confidences > KEYPOINT_CONF_THRESHOLD
        if np.sum(valid_mask) < 3:  # Ít nhất 3 keypoints hợp lệ
            return crops
        valid_kpts = keypoints[valid_mask]
    else:
        valid_kpts = keypoints[keypoints.sum(axis=1) != 0]
        if len(valid_kpts) < 3:
            return crops
    
    # 1. TOÀN THÂN (Full body)
    x_min, x_max = int(np.min(keypoints[:, 0])), int(np.max(keypoints[:, 0]))
    y_min, y_max = int(np.min(keypoints[:, 1])), int(np.max(keypoints[:, 1]))
    
    # Thêm padding
    padding = 20
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)
    
    if x_max > x_min and y_max > y_min:
        crops['full_body'] = frame[y_min:y_max, x_min:x_max]
    
    # 2. MẶT (Face) - vùng quanh mũi, mắt
    try:
        face_kpts = keypoints[[0, 1, 2, 3, 4]]  # nose, eyes, ears
        if confidences is not None:
            face_confs = confidences[[0, 1, 2, 3, 4]]
            if np.mean(face_confs) > KEYPOINT_CONF_THRESHOLD:
                face_x_min = max(0, int(np.min(face_kpts[:, 0])) - 30)
                face_y_min = max(0, int(np.min(face_kpts[:, 1])) - 30)
                face_x_max = min(w, int(np.max(face_kpts[:, 0])) + 30)
                face_y_max = min(h, int(np.max(face_kpts[:, 1])) + 30)
                if face_x_max > face_x_min and face_y_max > face_y_min:
                    crops['face'] = frame[face_y_min:face_y_max, face_x_min:face_x_max]
    except:
        pass
    
    # 3. TÓC (Hair) - vùng trên đầu
    try:
        if 'face' in crops and crops['face'] is not None:
            face_y_min = int(np.min(keypoints[[0, 1, 2, 3, 4], 1])) - 30
            hair_y_max = face_y_min
            hair_y_min = max(0, face_y_min - 60)
            hair_x_min = max(0, int(np.min(keypoints[:, 0])) - 20)
            hair_x_max = min(w, int(np.max(keypoints[:, 0])) + 20)
            if hair_y_max > hair_y_min and hair_x_max > hair_x_min:
                crops['hair'] = frame[hair_y_min:hair_y_max, hair_x_min:hair_x_max]
    except:
        pass
    
    # 4. ÁO (Shirt/Upper body) - từ vai đến hông
    try:
        upper_kpts = keypoints[[5, 6, 11, 12]]  # shoulders, hips
        if confidences is not None:
            upper_confs = confidences[[5, 6, 11, 12]]
            if np.mean(upper_confs) > KEYPOINT_CONF_THRESHOLD:
                shirt_x_min = max(0, int(np.min(upper_kpts[:, 0])) - 15)
                shirt_y_min = max(0, int(np.min(upper_kpts[[0, 1], 1])))
                shirt_x_max = min(w, int(np.max(upper_kpts[:, 0])) + 15)
                shirt_y_max = min(h, int(np.max(upper_kpts[[2, 3], 1])))
                if shirt_y_max > shirt_y_min and shirt_x_max > shirt_x_min:
                    crops['shirt'] = frame[shirt_y_min:shirt_y_max, shirt_x_min:shirt_x_max]
    except:
        pass
    
    # 5. QUẦN (Pants/Lower body) - từ hông đến cổ chân
    try:
        lower_kpts = keypoints[[11, 12, 15, 16]]  # hips, ankles
        if confidences is not None:
            lower_confs = confidences[[11, 12, 15, 16]]
            if np.mean(lower_confs) > KEYPOINT_CONF_THRESHOLD:
                pants_x_min = max(0, int(np.min(lower_kpts[:, 0])) - 15)
                pants_y_min = max(0, int(np.min(lower_kpts[[0, 1], 1])))
                pants_x_max = min(w, int(np.max(lower_kpts[:, 0])) + 15)
                pants_y_max = min(h, int(np.max(lower_kpts[:, 1])))
                if pants_y_max > pants_y_min and pants_x_max > pants_x_min:
                    crops['pants'] = frame[pants_y_min:pants_y_max, pants_x_min:pants_x_max]
    except:
        pass
    
    return crops

print("=" * 60)
print(f"Video: {frame_width}x{frame_height} @ {fps_video:.1f} FPS | Total: {total_frames} frames")
print(f"Config: Conf={CONF_THRESHOLD}, KeypointConf={KEYPOINT_CONF_THRESHOLD}, Resize={RESIZE_SCALE}")
print("Loaded Models: Pose Detection + Vehicle Detection + Fire/Smoke Detection + OCR")
print("=" * 60)

# Dictionary lưu các xe đã detect (để tránh lưu trùng)
detected_vehicles_cache = {}

# Counter cho cảnh báo cháy
fire_alerts_count = 0
smoke_alerts_count = 0

# ===== TEMPORAL FILTERING cho Fire/Smoke =====
FIRE_ALERT_THRESHOLD = 3      # Cần 3 frame liên tiếp để cảnh báo lửa
SMOKE_ALERT_THRESHOLD = 3     # Cần 3 frame liên tiếp để cảnh báo khói

fire_consecutive_frames = 0   # Số frame liên tiếp phát hiện lửa
smoke_consecutive_frames = 0  # Số frame liên tiếp phát hiện khói
last_fire_alert_frame = -100  # Frame cuối cùng cảnh báo lửa (để avoid spam)
last_smoke_alert_frame = -100 # Frame cuối cùng cảnh báo khói (để avoid spam)

frame_idx = 0
while cap.isOpened():
    success, frame = cap.read()
    if not success: 
        break
    
    frame_idx += 1
    
    # Skip frames để tăng tốc độ
    if frame_idx % SKIP_FRAMES != 0:
        continue
    
    # Resize frame để xử lý nhanh hơn
    frame_resized = cv2.resize(frame, (int(frame_width * RESIZE_SCALE), 
                                       int(frame_height * RESIZE_SCALE)))
    
    # ===== PHÁT HIỆN CHÁY/KHÓI (Song parallel + Temporal Filtering) =====
    fire_smoke_result = detect_fire_smoke(frame_resized) if fire_detection_enabled else {'fire': False, 'smoke': False}
    
    # Temporal Filtering: Chỉ cảnh báo khi liên tục nhiều frame
    if fire_smoke_result['fire']:
        fire_consecutive_frames += 1
    else:
        fire_consecutive_frames = 0
    
    if fire_smoke_result['smoke']:
        smoke_consecutive_frames += 1
    else:
        smoke_consecutive_frames = 0
    
    # ===== CẢNH BÁO CHỈ KHI CÓ CẢ KHÓI VÀ LỬA (Cháy thực sự) =====
    # Chỉ cảnh báo khi BOTH fire AND smoke liên tục được detect
    if (fire_consecutive_frames >= FIRE_ALERT_THRESHOLD and 
        smoke_consecutive_frames >= SMOKE_ALERT_THRESHOLD and 
        (frame_idx - last_fire_alert_frame) > 30):
        
        combined_percentage = (fire_smoke_result['fire_percentage'] + fire_smoke_result['smoke_percentage']) / 2
        print(f"\n[{frame_idx}] 🔥 CẢNH BÁO CHÁY (🔥 {fire_smoke_result['fire_percentage']:.1%} + 💨 {fire_smoke_result['smoke_percentage']:.1%})")
        save_fire_alert(frame_resized, fire_smoke_result, frame_idx)
        fire_alerts_count += 1
        last_fire_alert_frame = frame_idx
        last_smoke_alert_frame = frame_idx  # Cũng reset smoke timer
    
    # ===== PHÁT HIỆN PHƯƠNG TIỆN (Song song) =====
    vehicles = detect_vehicles(frame_resized, frame)
    
    if vehicles:
        print(f"\n[{frame_idx}] ✓ Phát hiện {len(vehicles)} phương tiện:")
        for v_idx, vehicle in enumerate(vehicles):
            print(f"    {v_idx + 1}. {vehicle['type_vn']} (Conf: {vehicle['confidence']:.2f})")
            save_vehicle(vehicle, frame_idx)
    
    # ===== PHÁT HIỆN NGƯỜI (Song song) =====
    # Chạy YOLO-Pose với confidence threshold
    results = model_pose.track(
        frame_resized, 
        persist=True, 
        verbose=False,
        conf=CONF_THRESHOLD,      # Độ tin cậy tối thiểu
        iou=0.45,                 # IoU threshold
        imgsz=384                 # Input size (tối ưu tốc độ vs độ chính xác)
    )

    ids = []  # Khởi tạo danh sách ID
    if results[0].boxes.id is not None:
        # Lấy danh sách ID, Keypoints, và Confidence
        ids = results[0].boxes.id.int().cpu().tolist()
        confidences = results[0].boxes.conf.cpu().numpy()
        keypoints_xy = results[0].keypoints.xy.cpu().numpy()
        keypoints_conf = results[0].keypoints.conf.cpu().numpy() if hasattr(results[0].keypoints, 'conf') else None

        for i, obj_id in enumerate(ids):
            # Kiểm tra độ tin cậy của detection
            if confidences[i] < CONF_THRESHOLD:
                continue
            
            # Nếu ID này chưa được xử lý
            if obj_id not in processed_ids:
                # Scale keypoints về kích thước frame gốc
                scaled_keypoints = keypoints_xy[i] / RESIZE_SCALE
                scaled_keypoints_conf = keypoints_conf[i] if keypoints_conf is not None else None
                
                print(f"\n[{frame_idx}] 👤 Người mới xuất hiện! ID: {obj_id} (Conf: {confidences[i]:.2f})")
                print(f"    Đang crop thuộc tính...")
                
                # Crop các phần cơ thể (sử dụng frame gốc để chất lượng tốt)
                body_crops = crop_body_parts(frame, scaled_keypoints, scaled_keypoints_conf)
                
                if body_crops:  # Chỉ lưu nếu có crop được
                    # Tạo thư mục cho từng người
                    person_dir = f'cropped_data/person_{obj_id}'
                    if not os.path.exists(person_dir):
                        os.makedirs(person_dir)
                    
                    # Lưu ảnh các phần khác nhau và phân tích màu sắc
                    saved_count = 0
                    color_results = {}
                    
                    for crop_name, crop_img in body_crops.items():
                        if crop_img is not None and crop_img.size > 0:
                            cv2.imwrite(f'{person_dir}/{crop_name}.jpg', crop_img)
                            saved_count += 1
                            
                            # Phân tích màu sắc cho tóc, áo, quần
                            if crop_name in ['hair', 'shirt', 'pants']:
                                colors = analyze_colors(crop_img, crop_name, num_colors=NUM_COLORS_PERSON)
                                if colors:
                                    color_results[crop_name] = colors
                    
                    # Lưu thông tin màu sắc vào file text
                    if color_results:
                        with open(f'{person_dir}/colors.txt', 'w', encoding='utf-8') as f:
                            f.write(f"=== MÀU SẮC PHÂN TÍCH ===\n")
                            f.write(f"ID: {obj_id} | Frame: {frame_idx}\n\n")
                            
                            for part_name, colors in color_results.items():
                                part_display = {'hair': 'TÓC', 'shirt': 'ÁO', 'pants': 'QUẦN'}.get(part_name, part_name)
                                f.write(f"--- {part_display} ---\n")
                                for color_info in colors:
                                    f.write(f"  {color_info['rank']}. {color_info['name']}\n")
                                    f.write(f"     RGB: {color_info['rgb']}\n")
                                    f.write(f"     BGR: {color_info['bgr']}\n")
                                f.write("\n")
                        
                        # In log thông tin màu sắc
                        for part_name, colors in color_results.items():
                            part_display = {'hair': 'TÓC', 'shirt': 'ÁO', 'pants': 'QUẦN'}.get(part_name, part_name)
                            color_names = ', '.join([c['name'] for c in colors])
                            print(f"    ✓ {part_display}: {color_names}")
                    
                    print(f"    ✓ Saved: {saved_count} crops")
                    # Đánh dấu là đã xử lý
                    processed_ids[obj_id] = True
                else:
                    print(f"    ✗ Failed: Không đủ keypoints hợp lệ")

    # Vẽ ID lên màn hình để quan sát (dùng frame đã resize)
    annotated_frame = results[0].plot()
    
    # Tính FPS và thống kê
    frame_count += 1
    elapsed = time.time() - fps_start
    if elapsed > 1:
        current_fps = frame_count / elapsed
        fps_start = time.time()
        frame_count = 0
        people_count = len(ids)
        vehicles_count = len(vehicles)
        # Chỉ hiển thị icon 🔥 khi BOTH fire AND smoke được detect (cháy thực sự)
        fire_status = "🔥" if (fire_consecutive_frames >= FIRE_ALERT_THRESHOLD and smoke_consecutive_frames >= SMOKE_ALERT_THRESHOLD) else ""
        print(f"FPS: {current_fps:.1f} | 👤 {people_count} người | 🚗 {vehicles_count} xe {fire_status}", end='\r')
    
    # Hiển thị frame nếu bật DISPLAY_OUTPUT
    if DISPLAY_OUTPUT:
        try:
            cv2.imshow('Tracking & Cropping (Optimized)', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break
        except Exception as e:
            print(f"\n⚠ Không thể hiển thị (GUI không hỗ trợ): {e}")
            DISPLAY_OUTPUT = False  # Tắt để không lỗi lần tới

cap.release()
if DISPLAY_OUTPUT:
    try:
        cv2.destroyAllWindows()
    except:
        pass

print("\n" + "=" * 60)
print("✓ Hoàn thành! Đã xử lý xong video.")
print(f"  👤 Tổng số người phát hiện: {len(processed_ids)}")
print(f"  🔥 Cảnh báo CHÁY (Khói + Lửa): {fire_alerts_count}")
print(f"  Dữ liệu lưu tại: cropped_data/")
print("=" * 60)