import sqlite3
import logging
import hashlib
from config import DATABASE_FILE

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_file = DATABASE_FILE

    def _get_connection(self):
        """Get a database connection."""
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
        
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_database(self):
        """Initialize the database with all required tables."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Photos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    recognized_faces TEXT
                )
            ''')
            
            # IP Cameras table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER DEFAULT 8080,
                    stream_path TEXT DEFAULT '/stream',
                    username TEXT,
                    password TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    national_id TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Sensor data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default admin user if no users exist
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                admin_password = self._hash_password('admin')
                cursor.execute('''
                    INSERT INTO users (username, password_hash) VALUES (?, ?)
                ''', ('admin', admin_password))
                logger.info("Created default admin user (username: admin, password: admin)")
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_photo_record(self, filename: str, recognized_names: list):
        """Save photo record to database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            faces_str = ', '.join(recognized_names) if recognized_names else 'None'
            cursor.execute(
                'INSERT INTO photos (filename, recognized_faces) VALUES (?, ?)',
                (filename, faces_str)
            )
            conn.commit()
            conn.close()
            logger.info(f"Photo record saved: {filename}")
        except Exception as e:
            logger.error(f"Error saving photo record: {e}")
    
    def get_user_by_username(self, username):
        """Get user by username."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            user = cursor.fetchone()
            conn.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_all_photos(self):
        """Get all photos from database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM photos ORDER BY id DESC')
            photos = cursor.fetchall()
            conn.close()
            return photos
        except Exception as e:
            logger.error(f"Error getting photos: {e}")
            return []
    
    def get_all_cameras(self):
        """Get all cameras from database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ip_cameras WHERE is_active = 1 ORDER BY name')
            cameras = cursor.fetchall()
            conn.close()
            return cameras
        except Exception as e:
            logger.error(f"Error getting cameras: {e}")
            return []
    
    def get_all_employees(self):
        """Get all employees from database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees WHERE is_active = 1 ORDER BY name')
            employees = cursor.fetchall()
            conn.close()
            return employees
        except Exception as e:
            logger.error(f"Error getting employees: {e}")
            return []
