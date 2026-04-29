"""
Configuration Settings for AI Detection System
Tập trung tất cả cấu hình ở một nơi để dễ quản lý
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== DATABASE CONFIGURATION =====
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/ai_detection')
DB_ECHO = os.getenv('DB_ECHO', 'False').lower() == 'true'  # In SQL queries
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# ===== FLASK CONFIGURATION =====
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# ===== API CONFIGURATION =====
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '5000'))
API_WORKERS = int(os.getenv('API_WORKERS', '4'))

# ===== CORS CONFIGURATION =====
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'

# ===== WEBSOCKET CONFIGURATION =====
WEBSOCKET_PING_INTERVAL = int(os.getenv('WEBSOCKET_PING_INTERVAL', '25'))
WEBSOCKET_PING_TIMEOUT = int(os.getenv('WEBSOCKET_PING_TIMEOUT', '60'))

# ===== PAGINATION CONFIGURATION =====
DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

# ===== LOGGING CONFIGURATION =====
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'ai_detection.log')
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '10'))

# ===== FEATURE FLAGS =====
ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'True').lower() == 'true'
ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'True').lower() == 'true'
ENABLE_STATISTICS = os.getenv('ENABLE_STATISTICS', 'True').lower() == 'true'
ENABLE_SEARCH = os.getenv('ENABLE_SEARCH', 'True').lower() == 'true'

# ===== DATA RETENTION CONFIGURATION =====
# Tự động xóa dữ liệu cũ hơn N ngày
AUTO_DELETE_ENABLED = os.getenv('AUTO_DELETE_ENABLED', 'False').lower() == 'true'
AUTO_DELETE_DAYS = int(os.getenv('AUTO_DELETE_DAYS', '90'))  # Xóa dữ liệu > 90 ngày
AUTO_DELETE_INTERVAL_HOURS = int(os.getenv('AUTO_DELETE_INTERVAL_HOURS', '24'))  # Kiểm tra mỗi 24 giờ

# ===== API RATE LIMITING (tùy chọn) =====
ENABLE_RATE_LIMIT = os.getenv('ENABLE_RATE_LIMIT', 'False').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))  # Requests
RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # Seconds

# ===== FILE STORAGE =====
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '52428800'))  # 50MB
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,txt').split(','))

# ===== DETECTION CONFIGURATION =====
MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.5'))
MAX_PERSONS_PER_FRAME = int(os.getenv('MAX_PERSONS_PER_FRAME', '100'))
MAX_VEHICLES_PER_FRAME = int(os.getenv('MAX_VEHICLES_PER_FRAME', '50'))

# ===== ALERT THRESHOLDS =====
FIRE_ALERT_THRESHOLD = float(os.getenv('FIRE_ALERT_THRESHOLD', '0.7'))
SUSPICIOUS_ACTIVITY_THRESHOLD = float(os.getenv('SUSPICIOUS_ACTIVITY_THRESHOLD', '0.8'))

# ===== API CLIENT CONFIGURATION =====
API_REQUEST_TIMEOUT = int(os.getenv('API_REQUEST_TIMEOUT', '10'))  # seconds
API_RETRY_COUNT = int(os.getenv('API_RETRY_COUNT', '3'))
API_RETRY_DELAY = int(os.getenv('API_RETRY_DELAY', '1'))  # seconds

# ===== TIMEZONE CONFIGURATION =====
TIMEZONE = os.getenv('TIMEZONE', 'UTC')

# ===== EMAIL ALERTS (tùy chọn) =====
ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'False').lower() == 'true'
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

# ===== DATABASE BACKUP =====
ENABLE_AUTO_BACKUP = os.getenv('ENABLE_AUTO_BACKUP', 'False').lower() == 'true'
BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups')
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

# ===== SECURITY CONFIGURATION =====
JWT_ENABLED = os.getenv('JWT_ENABLED', 'False').lower() == 'true'
JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# ===== DATA VALIDATION =====
MAX_LOCATION_LENGTH = int(os.getenv('MAX_LOCATION_LENGTH', '255'))
MAX_NOTES_LENGTH = int(os.getenv('MAX_NOTES_LENGTH', '5000'))
MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '1000'))

# ===== BATCH OPERATIONS =====
BATCH_INSERT_SIZE = int(os.getenv('BATCH_INSERT_SIZE', '1000'))
BATCH_TIMEOUT_SECONDS = int(os.getenv('BATCH_TIMEOUT_SECONDS', '30'))

# ===== CACHING =====
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'False').lower() == 'true'
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '300'))  # 5 phút

# ===== COLOR DETECTION SETTINGS =====
NUM_COLORS_PERSON = int(os.getenv('NUM_COLORS_PERSON', '3'))
NUM_COLORS_VEHICLE = int(os.getenv('NUM_COLORS_VEHICLE', '5'))

# ===== PRINT CONFIGURATION (để debug) =====
def print_config():
    """In toàn bộ configuration (không in sensitive data)"""
    print("\n" + "="*60)
    print("AI Detection System - Configuration")
    print("="*60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'}")
    print(f"Flask Environment: {FLASK_ENV}")
    print(f"API: {API_HOST}:{API_PORT}")
    print(f"Default Page Size: {DEFAULT_PAGE_SIZE}")
    print(f"Log Level: {LOG_LEVEL}")
    print(f"WebSocket: {'Enabled' if ENABLE_WEBSOCKET else 'Disabled'}")
    print(f"Alerts: {'Enabled' if ENABLE_ALERTS else 'Disabled'}")
    print(f"Rate Limiting: {'Enabled' if ENABLE_RATE_LIMIT else 'Disabled'}")
    print(f"Auto Backup: {'Enabled' if ENABLE_AUTO_BACKUP else 'Disabled'}")
    print("="*60 + "\n")

if __name__ == '__main__':
    print_config()
