"""
Script để tạo và khởi tạo cơ sở dữ liệu PostgreSQL
Chạy: python init_db.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from models import db, Person, Vehicle, Alert

load_dotenv()

def create_database():
    """Tạo cơ sở dữ liệu PostgreSQL"""
    
    # Cấu hình kết nối
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/ai_detection')
    
    # Parse connection string
    # Format: postgresql://user:password@host:port/database
    parts = db_url.replace('postgresql://', '').split('@')
    user_pass = parts[0].split(':')
    user = user_pass[0]
    password = user_pass[1]
    
    host_db = parts[1].split('/')
    host = host_db[0].split(':')[0]
    port = host_db[0].split(':')[1] if ':' in host_db[0] else '5432'
    database = host_db[1]
    
    # Kết nối tới PostgreSQL mặc định
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Kiểm tra xem database đã tồn tại chưa
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s;", (database,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Dropping existing database '{database}'...")
            cursor.execute(f"DROP DATABASE IF EXISTS {database};")
            print(f"✓ Database '{database}' dropped")
        
        print(f"Creating database '{database}'...")
        cursor.execute(f"CREATE DATABASE {database};")
        print(f"✓ Database '{database}' created successfully")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"✗ Database creation error: {e}")
        return False
    
    return True

def create_tables():
    """Tạo các bảng từ models"""
    try:
        from app import app
        
        with app.app_context():
            db.create_all()
            print("✓ All tables created successfully")
            
            # Hiển thị danh sách bảng
            engine = db.engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            print(f"✓ Tables: {', '.join(tables)}")
        
        return True
    
    except Exception as e:
        print(f"✗ Table creation error: {e}")
        return False

def insert_sample_data():
    """Chèn dữ liệu mẫu (tùy chọn)"""
    try:
        from app import app
        from datetime import datetime
        
        with app.app_context():
            # Kiểm tra xem đã có dữ liệu chưa
            if Person.query.first() is not None:
                print("Sample data already exists, skipping...")
                return True
            
            # Tạo người mẫu
            person1 = Person(
                person_id='person_001',
                location='Camera 1 - Gate A',
                timestamp=datetime.utcnow(),
                image_path='cropped_data/person_1/frame_001.jpg',
                shirt_colors=[{'rank': 1, 'name': 'Trắng', 'rgb': (255, 255, 255)}],
                pants_colors=[{'rank': 1, 'name': 'Xanh đen', 'rgb': (0, 51, 102)}],
                hair_colors=[{'rank': 1, 'name': 'Đen', 'rgb': (0, 0, 0)}],
                confidence=0.95,
                frame_index=1,
                video_source='video1.mov',
                notes='Test person 1'
            )
            
            person2 = Person(
                person_id='person_002',
                location='Camera 2 - Zone B',
                timestamp=datetime.utcnow(),
                image_path='cropped_data/person_2/frame_002.jpg',
                shirt_colors=[{'rank': 1, 'name': 'Đỏ', 'rgb': (255, 0, 0)}],
                pants_colors=[{'rank': 1, 'name': 'Xám', 'rgb': (128, 128, 128)}],
                hair_colors=[{'rank': 1, 'name': 'Nâu', 'rgb': (165, 42, 42)}],
                confidence=0.92,
                frame_index=100,
                video_source='video1.mov',
                notes='Test person 2'
            )
            
            # Tạo phương tiện mẫu
            vehicle1 = Vehicle(
                vehicle_id='vehicle_001',
                vehicle_type='car',
                license_plate='29A-12345',
                vehicle_colors=[{'rank': 1, 'name': 'Bạc', 'rgb': (192, 192, 192)}],
                location='Camera 1 - Gate A',
                timestamp=datetime.utcnow(),
                image_path='cropped_data/vehicles/car/frame_050.jpg',
                confidence=0.94,
                frame_index=50,
                video_source='video1.mov',
                notes='Test car 1'
            )
            
            vehicle2 = Vehicle(
                vehicle_id='vehicle_002',
                vehicle_type='motorcycle',
                license_plate='72C-98765',
                vehicle_colors=[{'rank': 1, 'name': 'Đỏ', 'rgb': (255, 0, 0)}, 
                               {'rank': 2, 'name': 'Đen', 'rgb': (0, 0, 0)}],
                location='Camera 2 - Zone B',
                timestamp=datetime.utcnow(),
                image_path='cropped_data/vehicles/motorcycle/frame_075.jpg',
                confidence=0.89,
                frame_index=75,
                video_source='video1.mov',
                notes='Test motorcycle'
            )
            
            # Tạo cảnh báo mẫu
            alert1 = Alert(
                alert_type='fire',
                person_id=None,
                vehicle_id=None,
                description='Detected fire smoke in zone C',
                location='Camera 3 - Zone C',
                timestamp=datetime.utcnow(),
                frame_index=200,
                severity='high',
                status='active',
                notes='Test alert 1'
            )
            
            db.session.add(person1)
            db.session.add(person2)
            db.session.add(vehicle1)
            db.session.add(vehicle2)
            db.session.add(alert1)
            db.session.commit()
            
            print("✓ Sample data inserted successfully")
            return True
    
    except Exception as e:
        print(f"✗ Sample data insertion error: {e}")
        return False

def main():
    """Hàm chính"""
    print("=" * 60)
    print("AI Detection System - Database Initialization")
    print("=" * 60)
    
    # Bước 1: Tạo database
    print("\n[1/3] Creating database...")
    if not create_database():
        print("✗ Failed to create database")
        return
    
    # Bước 2: Tạo bảng
    print("\n[2/3] Creating tables...")
    if not create_tables():
        print("✗ Failed to create tables")
        return
    
    # Bước 3: Chèn dữ liệu mẫu
    print("\n[3/3] Inserting sample data...")
    insert_sample_data()
    
    print("\n" + "=" * 60)
    print("✓ Database initialization completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Visit: http://localhost:5000")
    print("3. API Documentation: http://localhost:5000/")

if __name__ == '__main__':
    main()
