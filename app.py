from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db, Person, Vehicle, Alert, Camera
from camera_manager import camera_manager
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc
import os
from dotenv import load_dotenv

# Face recognition (Phase 2)
try:
    from ai_engine.utils.face_matcher import get_face_matching_engine
    FACE_MATCHING_AVAILABLE = True
except ImportError:
    FACE_MATCHING_AVAILABLE = False

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# ===== CẤU HÌNH DATABASE =====
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/ai_detection')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# ===== KHỞI TẠO =====
db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== WEBSOCKET EVENTS (Real-time Updates) =====

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('response', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('subscribe_persons')
def subscribe_persons():
    """Subscribe to real-time person updates"""
    join_room('persons')
    emit('response', {'status': 'subscribed', 'channel': 'persons'})

@socketio.on('subscribe_vehicles')
def subscribe_vehicles():
    """Subscribe to real-time vehicle updates"""
    join_room('vehicles')
    emit('response', {'status': 'subscribed', 'channel': 'vehicles'})

@socketio.on('subscribe_alerts')
def subscribe_alerts():
    """Subscribe to real-time alerts"""
    join_room('alerts')
    emit('response', {'status': 'subscribed', 'channel': 'alerts'})

@socketio.on('subscribe_faces')
def subscribe_faces():
    """Subscribe to real-time face detection (Phase 2)"""
    join_room('faces')
    emit('response', {'status': 'subscribed', 'channel': 'faces'})

# ===== HELPER FUNCTIONS =====

def broadcast_new_person(person_data):
    """Phát sóng dữ liệu người mới cho các client đang lắng nghe"""
    socketio.emit('new_person', person_data, room='persons')

def broadcast_new_vehicle(vehicle_data):
    """Phát sóng dữ liệu phương tiện mới"""
    socketio.emit('new_vehicle', vehicle_data, room='vehicles')

def broadcast_new_alert(alert_data):
    """Phát sóng cảnh báo mới"""
    socketio.emit('new_alert', alert_data, room='alerts')

def broadcast_new_camera(camera_data):
    """Phát sóng camera mới"""
    socketio.emit('new_camera', camera_data, room='cameras')

def broadcast_new_face(face_data):
    """Phát sóng dữ liệu khuôn mặt mới (Phase 2)"""
    socketio.emit('new_face', face_data, room='faces')

# ===== API ENDPOINTS - CAMERAS =====

@app.route('/api/cameras', methods=['POST'])
def create_camera():
    """Tạo hoặc cập nhật camera"""
    try:
        data = request.get_json()
        
        if not data.get('camera_id') or not data.get('stream_url'):
            return jsonify({'error': 'camera_id and stream_url are required'}), 400
        
        camera = Camera.query.filter_by(camera_id=data['camera_id']).first()
        
        if camera:
            # Cập nhật
            camera.name = data.get('name', camera.name)
            camera.location = data.get('location', camera.location)
            camera.stream_url = data.get('stream_url', camera.stream_url)
            camera.protocol = data.get('protocol', camera.protocol)
            camera.resolution = data.get('resolution', camera.resolution)
            camera.fps = data.get('fps', camera.fps)
            camera.brand = data.get('brand', camera.brand)
            camera.model = data.get('model', camera.model)
            camera.username = data.get('username', camera.username)
            camera.password = data.get('password', camera.password)
            camera.enable_detection = data.get('enable_detection', camera.enable_detection)
            camera.notes = data.get('notes', camera.notes)
        else:
            # Tạo mới
            camera = Camera(
                camera_id=data['camera_id'],
                name=data.get('name', f'Camera {data["camera_id"]}'),
                location=data.get('location', 'Unknown'),
                stream_url=data['stream_url'],
                protocol=data.get('protocol', 'rtsp'),
                resolution=data.get('resolution'),
                fps=data.get('fps', 30),
                brand=data.get('brand'),
                model=data.get('model'),
                username=data.get('username'),
                password=data.get('password'),
                enable_detection=data.get('enable_detection', True),
                notes=data.get('notes')
            )
            
            # Thêm vào camera manager
            camera_manager.add_camera(
                data['camera_id'],
                data['stream_url'],
                data.get('username'),
                data.get('password'),
                data.get('fps', 30)
            )
            
            db.session.add(camera)
        
        db.session.commit()
        broadcast_new_camera(camera.to_dict())
        
        return jsonify(camera.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras', methods=['GET'])
def list_cameras():
    """Liệt kê camera"""
    try:
        location = request.args.get('location')
        is_active = request.args.get('is_active')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Camera.query
        
        if location:
            query = query.filter(Camera.location.ilike(f'%{location}%'))
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter_by(is_active=is_active_bool)
        
        query = query.order_by(desc(Camera.created_at))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [c.to_dict() for c in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Lấy thông tin camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        return jsonify(camera.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>', methods=['PUT'])
def update_camera(camera_id):
    """Cập nhật camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            camera.name = data['name']
        if 'location' in data:
            camera.location = data['location']
        if 'stream_url' in data:
            camera.stream_url = data['stream_url']
        if 'protocol' in data:
            camera.protocol = data['protocol']
        if 'resolution' in data:
            camera.resolution = data['resolution']
        if 'fps' in data:
            camera.fps = data['fps']
        if 'brand' in data:
            camera.brand = data['brand']
        if 'model' in data:
            camera.model = data['model']
        if 'is_active' in data:
            camera.is_active = data['is_active']
        if 'enable_detection' in data:
            camera.enable_detection = data['enable_detection']
        if 'notes' in data:
            camera.notes = data['notes']
        
        camera.updated_at = datetime.utcnow()
        db.session.commit()
        
        broadcast_new_camera(camera.to_dict())
        return jsonify(camera.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Xóa camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        # Dừng stream
        camera_manager.stop_camera(camera_id)
        camera_manager.remove_camera(camera_id)
        
        db.session.delete(camera)
        db.session.commit()
        
        return jsonify({'message': 'Camera deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/start', methods=['POST'])
def start_camera(camera_id):
    """Bắt đầu stream camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        if camera_manager.start_camera(camera_id):
            camera.is_active = True
            camera.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Camera started', 'camera': camera.to_dict()}), 200
        else:
            return jsonify({'error': 'Failed to start camera'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/stop', methods=['POST'])
def stop_camera(camera_id):
    """Dừng stream camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        camera_manager.stop_camera(camera_id)
        camera.is_active = False
        camera.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Camera stopped', 'camera': camera.to_dict()}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/frame', methods=['GET'])
def get_camera_frame(camera_id):
    """Lấy frame hiện tại từ camera (JPEG)"""
    try:
        frame_data = camera_manager.get_frame_jpeg(camera_id)
        if frame_data is None:
            return jsonify({'error': 'No frame available'}), 404
        
        return Response(frame_data, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/stream', methods=['GET'])
def get_camera_stream(camera_id):
    """WebRTC/MJPEG stream camera (motion JPEG)"""
    try:
        def generate():
            while True:
                frame_data = camera_manager.get_frame_jpeg(camera_id)
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' +
                           frame_data + b'\r\n')
                else:
                    return
                
                # Control frame rate
                import time
                time.sleep(0.033)  # ~30 fps
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/status', methods=['GET'])
def get_camera_status(camera_id):
    """Lấy status camera"""
    try:
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        status = camera_manager.get_camera_status(camera_id)
        
        return jsonify({
            'camera': camera.to_dict(),
            'stream_status': status
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/status/all', methods=['GET'])
def get_all_cameras_status():
    """Lấy status tất cả camera"""
    try:
        cameras = Camera.query.all()
        status = camera_manager.get_all_status()
        
        return jsonify({
            'cameras': [c.to_dict() for c in cameras],
            'status': status
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/persons', methods=['POST'])
def create_person():
    """Tạo hoặc cập nhật thông tin người"""
    try:
        data = request.get_json()
        
        # Kiểm tra dữ liệu bắt buộc
        if not data.get('person_id') or not data.get('location'):
            return jsonify({'error': 'person_id and location are required'}), 400
        
        # Kiểm tra xem người này đã tồn tại chưa
        person = Person.query.filter_by(person_id=data['person_id']).first()
        
        if person:
            # Cập nhật
            person.location = data.get('location', person.location)
            person.timestamp = datetime.utcnow()
            person.image_path = data.get('image_path', person.image_path)
            person.shirt_colors = data.get('shirt_colors', person.shirt_colors)
            person.pants_colors = data.get('pants_colors', person.pants_colors)
            person.hair_colors = data.get('hair_colors', person.hair_colors)
            person.confidence = data.get('confidence', person.confidence)
            person.frame_index = data.get('frame_index', person.frame_index)
            person.video_source = data.get('video_source', person.video_source)
            person.notes = data.get('notes', person.notes)
        else:
            # Tạo mới
            person = Person(
                person_id=data['person_id'],
                location=data['location'],
                timestamp=datetime.utcnow(),
                image_path=data.get('image_path'),
                shirt_colors=data.get('shirt_colors'),
                pants_colors=data.get('pants_colors'),
                hair_colors=data.get('hair_colors'),
                confidence=data.get('confidence', 0.0),
                frame_index=data.get('frame_index'),
                video_source=data.get('video_source'),
                notes=data.get('notes')
            )
            db.session.add(person)
        
        db.session.commit()
        
        # Phát sóng update real-time
        broadcast_new_person(person.to_dict())
        
        return jsonify(person.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons/<person_id>', methods=['GET'])
def get_person(person_id):
    """Lấy thông tin một người"""
    try:
        person = Person.query.filter_by(person_id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        return jsonify(person.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons', methods=['GET'])
def list_persons():
    """Liệt kê người với lọc và tìm kiếm"""
    try:
        # Tham số truy vấn
        location = request.args.get('location')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        shirt_color = request.args.get('shirt_color')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Xây dựng query
        query = Person.query
        
        if location:
            query = query.filter(Person.location.ilike(f'%{location}%'))
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(Person.timestamp >= start_dt)
            except:
                pass
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(Person.timestamp <= end_dt)
            except:
                pass
        
        # Sắp xếp theo thời gian mới nhất trước
        query = query.order_by(desc(Person.timestamp))
        
        # Phân trang
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [p.to_dict() for p in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons/<person_id>', methods=['PUT'])
def update_person(person_id):
    """Cập nhật thông tin người"""
    try:
        person = Person.query.filter_by(person_id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        data = request.get_json()
        
        if 'location' in data:
            person.location = data['location']
        if 'image_path' in data:
            person.image_path = data['image_path']
        if 'shirt_colors' in data:
            person.shirt_colors = data['shirt_colors']
        if 'pants_colors' in data:
            person.pants_colors = data['pants_colors']
        if 'hair_colors' in data:
            person.hair_colors = data['hair_colors']
        if 'confidence' in data:
            person.confidence = data['confidence']
        if 'notes' in data:
            person.notes = data['notes']
        
        person.updated_at = datetime.utcnow()
        db.session.commit()
        
        broadcast_new_person(person.to_dict())
        return jsonify(person.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons/<person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Xóa thông tin người"""
    try:
        person = Person.query.filter_by(person_id=person_id).first()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        db.session.delete(person)
        db.session.commit()
        
        return jsonify({'message': 'Person deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== API ENDPOINTS - VEHICLES =====

@app.route('/api/vehicles', methods=['POST'])
def create_vehicle():
    """Tạo hoặc cập nhật thông tin phương tiện"""
    try:
        data = request.get_json()
        
        if not data.get('vehicle_id') or not data.get('vehicle_type'):
            return jsonify({'error': 'vehicle_id and vehicle_type are required'}), 400
        
        vehicle = Vehicle.query.filter_by(vehicle_id=data['vehicle_id']).first()
        
        if vehicle:
            # Cập nhật
            vehicle.vehicle_type = data.get('vehicle_type', vehicle.vehicle_type)
            vehicle.license_plate = data.get('license_plate', vehicle.license_plate)
            vehicle.location = data.get('location', vehicle.location)
            vehicle.timestamp = datetime.utcnow()
            vehicle.image_path = data.get('image_path', vehicle.image_path)
            vehicle.vehicle_colors = data.get('vehicle_colors', vehicle.vehicle_colors)
            vehicle.confidence = data.get('confidence', vehicle.confidence)
            vehicle.frame_index = data.get('frame_index', vehicle.frame_index)
            vehicle.video_source = data.get('video_source', vehicle.video_source)
            vehicle.notes = data.get('notes', vehicle.notes)
        else:
            # Tạo mới
            vehicle = Vehicle(
                vehicle_id=data['vehicle_id'],
                vehicle_type=data['vehicle_type'],
                license_plate=data.get('license_plate'),
                location=data.get('location'),
                timestamp=datetime.utcnow(),
                image_path=data.get('image_path'),
                vehicle_colors=data.get('vehicle_colors'),
                confidence=data.get('confidence', 0.0),
                frame_index=data.get('frame_index'),
                video_source=data.get('video_source'),
                notes=data.get('notes')
            )
            db.session.add(vehicle)
        
        db.session.commit()
        broadcast_new_vehicle(vehicle.to_dict())
        return jsonify(vehicle.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicles/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Lấy thông tin một phương tiện"""
    try:
        vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        return jsonify(vehicle.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicles', methods=['GET'])
def list_vehicles():
    """Liệt kê phương tiện với lọc"""
    try:
        vehicle_type = request.args.get('vehicle_type')
        license_plate = request.args.get('license_plate')
        location = request.args.get('location')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Vehicle.query
        
        if vehicle_type:
            query = query.filter_by(vehicle_type=vehicle_type)
        
        if license_plate:
            query = query.filter(Vehicle.license_plate.ilike(f'%{license_plate}%'))
        
        if location:
            query = query.filter(Vehicle.location.ilike(f'%{location}%'))
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(Vehicle.timestamp >= start_dt)
            except:
                pass
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(Vehicle.timestamp <= end_dt)
            except:
                pass
        
        query = query.order_by(desc(Vehicle.timestamp))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [v.to_dict() for v in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicles/<vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    """Cập nhật thông tin phương tiện"""
    try:
        vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        data = request.get_json()
        
        if 'vehicle_type' in data:
            vehicle.vehicle_type = data['vehicle_type']
        if 'license_plate' in data:
            vehicle.license_plate = data['license_plate']
        if 'location' in data:
            vehicle.location = data['location']
        if 'vehicle_colors' in data:
            vehicle.vehicle_colors = data['vehicle_colors']
        if 'notes' in data:
            vehicle.notes = data['notes']
        
        vehicle.updated_at = datetime.utcnow()
        db.session.commit()
        
        broadcast_new_vehicle(vehicle.to_dict())
        return jsonify(vehicle.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicles/<vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    """Xóa thông tin phương tiện"""
    try:
        vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'message': 'Vehicle deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== API ENDPOINTS - ALERTS =====

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Tạo cảnh báo mới"""
    try:
        data = request.get_json()
        
        if not data.get('alert_type'):
            return jsonify({'error': 'alert_type is required'}), 400
        
        alert = Alert(
            alert_type=data['alert_type'],
            person_id=data.get('person_id'),
            vehicle_id=data.get('vehicle_id'),
            description=data.get('description'),
            location=data.get('location'),
            frame_index=data.get('frame_index'),
            image_path=data.get('image_path'),
            severity=data.get('severity', 'normal'),
            status=data.get('status', 'active')
        )
        
        db.session.add(alert)
        db.session.commit()
        
        broadcast_new_alert(alert.to_dict())
        return jsonify(alert.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def list_alerts():
    """Liệt kê cảnh báo"""
    try:
        alert_type = request.args.get('alert_type')
        status = request.args.get('status')
        severity = request.args.get('severity')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Alert.query
        
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
        
        if status:
            query = query.filter_by(status=status)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(Alert.timestamp >= start_dt)
            except:
                pass
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(Alert.timestamp <= end_dt)
            except:
                pass
        
        query = query.order_by(desc(Alert.timestamp))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [a.to_dict() for a in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Cập nhật cảnh báo"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        data = request.get_json()
        
        if 'status' in data:
            alert.status = data['status']
        if 'severity' in data:
            alert.severity = data['severity']
        if 'description' in data:
            alert.description = data['description']
        
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        
        broadcast_new_alert(alert.to_dict())
        return jsonify(alert.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Xóa cảnh báo"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({'message': 'Alert deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== API ENDPOINTS - THỐNG KÊ =====

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Lấy thống kê chung"""
    try:
        stats = {
            'total_persons': Person.query.count(),
            'total_vehicles': Vehicle.query.count(),
            'active_alerts': Alert.query.filter_by(status='active').count(),
            'total_alerts': Alert.query.count(),
            'recent_persons': Person.query.order_by(desc(Person.timestamp)).limit(5),
            'recent_vehicles': Vehicle.query.order_by(desc(Vehicle.timestamp)).limit(5),
            'recent_alerts': Alert.query.order_by(desc(Alert.timestamp)).limit(5)
        }
        
        return jsonify({
            'total_persons': stats['total_persons'],
            'total_vehicles': stats['total_vehicles'],
            'active_alerts': stats['active_alerts'],
            'total_alerts': stats['total_alerts'],
            'recent_persons': [p.to_dict() for p in stats['recent_persons']],
            'recent_vehicles': [v.to_dict() for v in stats['recent_vehicles']],
            'recent_alerts': [a.to_dict() for a in stats['recent_alerts']]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API ENDPOINTS - FACE RECOGNITION (Phase 2) =====

@app.route('/api/ai/faces', methods=['POST'])
def receive_face_data():
    """
    Receive face detection data from AI engine
    Includes face embeddings and matching results
    """
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        data = request.get_json()
        
        camera_id = data.get('camera_id')
        frame_idx = data.get('frame_index')
        person_id = data.get('person_id')
        faces = data.get('faces', [])
        matched_person = data.get('matched_person')
        
        if not all([camera_id, person_id, faces]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get face matcher
        face_matcher = get_face_matching_engine()
        
        # Process each face
        for face_data in faces:
            embedding = face_data.get('embedding')
            
            if embedding:
                # Try to match with known faces
                match = face_matcher.find_matching_face(embedding)
                
                # Update person record with face embedding
                person = Person.query.filter_by(person_id=person_id).first()
                if person:
                    person.face_embedding = embedding
                    person.face_confidence = face_data.get('confidence', 0.0)
                    person.face_bbox = face_data.get('bbox')
                    person.face_embedding_model = "buffalo_l"
                    
                    # Update if matched
                    if match:
                        person.notes = f"FaceID Match: {match['person_id']} ({match['similarity']:.1%})"
                    
                    db.session.commit()
        
        # Broadcast to connected clients
        broadcast_new_face({
            'camera_id': camera_id,
            'frame_index': frame_idx,
            'person_id': person_id,
            'face_count': len(faces),
            'matched_person': matched_person,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'status': 'received',
            'faces_processed': len(faces),
            'matched': matched_person is not None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/known', methods=['GET'])
def get_known_faces():
    """Get all known faces (registered people for FaceID matching)"""
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        face_matcher = get_face_matching_engine()
        known_faces = face_matcher.get_known_faces()
        
        return jsonify({
            'total': len(known_faces),
            'faces': {
                person_id: {
                    'metadata': face_data['metadata'],
                    'added_at': face_data['added_at'],
                    'match_count': face_data['match_count']
                }
                for person_id, face_data in known_faces.items()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/known', methods=['POST'])
def register_known_face():
    """Register a known face for FaceID matching"""
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        data = request.get_json()
        
        person_id = data.get('person_id')
        embedding = data.get('embedding')
        metadata = data.get('metadata', {})
        
        if not all([person_id, embedding]):
            return jsonify({'error': 'person_id and embedding are required'}), 400
        
        if len(embedding) != 512:
            return jsonify({'error': 'Embedding must be 512-dimensional'}), 400
        
        face_matcher = get_face_matching_engine()
        success = face_matcher.add_known_face(person_id, embedding, metadata)
        
        if success:
            return jsonify({
                'status': 'registered',
                'person_id': person_id
            }), 201
        else:
            return jsonify({'error': 'Failed to register face'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/match', methods=['POST'])
def match_face():
    """Find matching known face for a query embedding"""
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        data = request.get_json()
        
        embedding = data.get('embedding')
        
        if not embedding or len(embedding) != 512:
            return jsonify({'error': 'Valid 512-dimensional embedding required'}), 400
        
        face_matcher = get_face_matching_engine()
        match = face_matcher.find_matching_face(embedding)
        
        if match:
            return jsonify({
                'status': 'matched',
                'person_id': match['person_id'],
                'similarity': match['similarity'],
                'metadata': match['metadata']
            }), 200
        else:
            return jsonify({
                'status': 'no_match',
                'message': 'No matching known face found'
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/stats', methods=['GET'])
def get_face_stats():
    """Get face matching statistics"""
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        face_matcher = get_face_matching_engine()
        stats = face_matcher.get_stats()
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/known/<person_id>', methods=['DELETE'])
def remove_known_face(person_id):
    """Remove a known face from database"""
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        face_matcher = get_face_matching_engine()
        success = face_matcher.remove_known_face(person_id)
        
        if success:
            return jsonify({
                'status': 'removed',
                'person_id': person_id
            }), 200
        else:
            return jsonify({'error': f'Known face not found: {person_id}'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/register-image', methods=['POST'])
def register_face_from_image():
    """
    Register a known face from image file
    Extracts face embedding and stores it
    """
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        person_id = request.form.get('person_id')
        metadata_str = request.form.get('metadata', '{}')
        
        if not person_id:
            return jsonify({'error': 'person_id is required'}), 400
        
        # Get image file
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Read image
        import numpy as np
        from PIL import Image
        import io
        
        try:
            img_pil = Image.open(io.BytesIO(image_file.read()))
            img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return jsonify({'error': f'Failed to read image: {str(e)}'}), 400
        
        # Extract face embedding using face processor
        try:
            from ai_engine.processors.face_processor import FaceProcessor
            
            face_processor = FaceProcessor()
            if not face_processor.load_model():
                return jsonify({'error': 'Face recognition model not available'}), 501
            
            # Extract embedding
            embedding = face_processor.extract_embedding(img_cv2)
            
            if not embedding:
                return jsonify({'error': 'No face detected in image'}), 400
            
            # Parse metadata
            import json
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
            except:
                metadata = {}
            
            # Register the face
            face_matcher = get_face_matching_engine()
            success = face_matcher.add_known_face(person_id, embedding, metadata)
            
            if success:
                return jsonify({
                    'status': 'registered',
                    'person_id': person_id,
                    'embedding_dim': len(embedding),
                    'metadata': metadata
                }), 201
            else:
                return jsonify({'error': 'Failed to register face'}), 500
                
        except ImportError:
            return jsonify({'error': 'Face recognition dependencies not installed'}), 501
        except Exception as e:
            return jsonify({'error': f'Embedding extraction failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/search-image', methods=['POST'])
def search_face_from_image():
    """
    Search for matching person from image file
    Extracts face embedding and finds closest match
    """
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        # Check if file is in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Read image
        import numpy as np
        from PIL import Image
        import io
        
        try:
            img_pil = Image.open(io.BytesIO(image_file.read()))
            img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return jsonify({'error': f'Failed to read image: {str(e)}'}), 400
        
        # Extract face embedding using face processor
        try:
            from ai_engine.processors.face_processor import FaceProcessor
            
            face_processor = FaceProcessor()
            if not face_processor.load_model():
                return jsonify({'error': 'Face recognition model not available'}), 501
            
            # Extract embedding
            embedding = face_processor.extract_embedding(img_cv2)
            
            if not embedding:
                return jsonify({'error': 'No face detected in image'}), 400
            
            # Find matching face
            face_matcher = get_face_matching_engine()
            match = face_matcher.find_matching_face(embedding)
            
            if match:
                return jsonify({
                    'status': 'matched',
                    'person_id': match['person_id'],
                    'similarity': match['similarity'],
                    'confidence_percent': round(match['similarity'] * 100, 2),
                    'metadata': match['metadata'],
                    'added_at': match['added_at']
                }), 200
            else:
                return jsonify({
                    'status': 'no_match',
                    'message': 'No matching face found in database'
                }), 200
                
        except ImportError:
            return jsonify({'error': 'Face recognition dependencies not installed'}), 501
        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/persons-with-faces', methods=['GET'])
def get_persons_with_faces():
    """Get all persons that have registered face embeddings"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query persons with face embeddings
        query = Person.query.filter(Person.face_embedding != None)
        query = query.order_by(desc(Person.updated_at))
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [p.to_dict() for p in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/person/<person_id>/history', methods=['GET'])
def get_person_face_history(person_id):
    """Get face detection history for a specific person"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get person with face embedding
        person = Person.query.filter_by(person_id=person_id).first()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        if not person.face_embedding:
            return jsonify({'error': 'Person has no registered face'}), 404
        
        # Get all detections of this person
        query = Person.query.filter_by(person_id=person_id).order_by(desc(Person.timestamp))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'person_id': person_id,
            'person_info': person.to_dict(),
            'detection_history': [p.to_dict() for p in paginated.items],
            'total_detections': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faces/clear-all', methods=['POST'])
def clear_all_known_faces():
    """
    Clear all known faces from database (WARNING: Use with caution)
    Requires confirmation parameter
    """
    if not FACE_MATCHING_AVAILABLE:
        return jsonify({'error': 'Face matching not available'}), 501
    
    try:
        # Require explicit confirmation
        confirm = request.get_json().get('confirm_clear_all')
        
        if not confirm:
            return jsonify({
                'error': 'This action will delete all known faces. Pass {"confirm_clear_all": true} to proceed'
            }), 400
        
        face_matcher = get_face_matching_engine()
        success = face_matcher.clear_all_faces()
        
        if success:
            return jsonify({
                'status': 'cleared',
                'message': 'All known faces have been cleared'
            }), 200
        else:
            return jsonify({'error': 'Failed to clear faces'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ROUTES HEALTH CHECK =====

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra sức khỏe server"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/dashboard')
def dashboard():
    """Serve dashboard HTML"""
    return render_template('dashboard.html')

@app.route('/', methods=['GET'])
def index():
    """Trang chủ"""
    return jsonify({
        'message': 'AI Detection System API Server',
        'version': '1.0.0',
        'dashboard': 'Open http://localhost:5000/dashboard',
        'endpoints': {
            'cameras': {
                'POST /api/cameras': 'Create/Update camera',
                'GET /api/cameras': 'List cameras',
                'GET /api/cameras/<camera_id>': 'Get camera details',
                'GET /api/cameras/<camera_id>/frame': 'Get current frame (JPEG)',
                'GET /api/cameras/<camera_id>/stream': 'Get live stream (MJPEG)',
                'GET /api/cameras/<camera_id>/status': 'Get camera status',
                'POST /api/cameras/<camera_id>/start': 'Start camera stream',
                'POST /api/cameras/<camera_id>/stop': 'Stop camera stream',
                'PUT /api/cameras/<camera_id>': 'Update camera',
                'DELETE /api/cameras/<camera_id>': 'Delete camera'
            },
            'persons': {
                'POST /api/persons': 'Create/Update person',
                'GET /api/persons': 'List persons',
                'GET /api/persons/<person_id>': 'Get person details',
                'PUT /api/persons/<person_id>': 'Update person',
                'DELETE /api/persons/<person_id>': 'Delete person'
            },
            'vehicles': {
                'POST /api/vehicles': 'Create/Update vehicle',
                'GET /api/vehicles': 'List vehicles',
                'GET /api/vehicles/<vehicle_id>': 'Get vehicle details',
                'PUT /api/vehicles/<vehicle_id>': 'Update vehicle',
                'DELETE /api/vehicles/<vehicle_id>': 'Delete vehicle'
            },
            'alerts': {
                'POST /api/alerts': 'Create alert',
                'GET /api/alerts': 'List alerts',
                'PUT /api/alerts/<alert_id>': 'Update alert',
                'DELETE /api/alerts/<alert_id>': 'Delete alert'
            },
            'other': {
                'GET /api/statistics': 'Get statistics',
                'GET /health': 'Health check'
            }
        }
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
