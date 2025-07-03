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
            
            # Energy usage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS energy_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration_minutes REAL DEFAULT 0
                )
            ''')
            
            # Device status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL UNIQUE,
                    current_state TEXT NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Initialize default device states
            cursor.execute('SELECT COUNT(*) FROM device_status')
            status_count = cursor.fetchone()[0]
            if status_count == 0:
                cursor.execute('INSERT INTO device_status (device_name, current_state) VALUES (?, ?)', ('lamp', 'off'))
                cursor.execute('INSERT INTO device_status (device_name, current_state) VALUES (?, ?)', ('outlet', 'off'))
                logger.info("Initialized default device states")
            
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
    
    def save_energy_event(self, device_name, state, timestamp=None):
        """Save energy usage event to database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if timestamp:
                cursor.execute('''
                    INSERT INTO energy_usage (device_name, state, timestamp) 
                    VALUES (?, ?, ?)
                ''', (device_name, state, timestamp))
            else:
                cursor.execute('''
                    INSERT INTO energy_usage (device_name, state) 
                    VALUES (?, ?)
                ''', (device_name, state))
            
            conn.commit()
            conn.close()
            logger.info(f"Energy event saved: {device_name} - {state}")
        except Exception as e:
            logger.error(f"Error saving energy event: {e}")
    
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
    
    def get_energy_usage(self, device_name=None, days=7):
        """Get energy usage data for the past N days."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if device_name:
                cursor.execute('''
                    SELECT * FROM energy_usage 
                    WHERE device_name = ? AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days), (device_name,))
            else:
                cursor.execute('''
                    SELECT * FROM energy_usage 
                    WHERE timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days))
            
            usage_data = cursor.fetchall()
            conn.close()
            return usage_data
        except Exception as e:
            logger.error(f"Error getting energy usage: {e}")
            return []
    
    def calculate_device_usage_time(self, device_name, days=7):
        """Calculate total usage time for a device in the past N days."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get all events for the device in the time period
            cursor.execute('''
                SELECT state, timestamp FROM energy_usage 
                WHERE device_name = ? AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp ASC
            '''.format(days), (device_name,))
            
            events = cursor.fetchall()
            conn.close()
            
            if not events:
                return 0
            
            total_minutes = 0
            last_on_time = None
            
            for state, timestamp in events:
                from datetime import datetime
                event_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                
                if state == 'on':
                    last_on_time = event_time
                elif state == 'off' and last_on_time:
                    duration = (event_time - last_on_time).total_seconds() / 60
                    total_minutes += duration
                    last_on_time = None
            
            # If device is still on, calculate time until now
            if last_on_time:
                from datetime import datetime
                duration = (datetime.now() - last_on_time).total_seconds() / 60
                total_minutes += duration
            
            return total_minutes
        except Exception as e:
            logger.error(f"Error calculating usage time: {e}")
            return 0
        
    def get_device_status(self, device_name):
        """Get current status of a device."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT current_state FROM device_status WHERE device_name = ?', (device_name,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 'off'
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return 'off'
    
    def update_device_status(self, device_name, state):
        """Update device status."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO device_status (device_name, current_state, last_updated)
                VALUES (?, ?, datetime('now'))
            ''', (device_name, state))
            conn.commit()
            conn.close()
            logger.info(f"Device status updated: {device_name} - {state}")
        except Exception as e:
            logger.error(f"Error updating device status: {e}")

    def get_recent_energy_activity(self, limit):
        """Get recent energy activity records."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM energy_usage ORDER BY timestamp DESC LIMIT ?', (limit,))
            records = cursor.fetchall()
            conn.close()
            return records
        except Exception as e:
            logger.error(f"Error getting recent energy activity: {e}")
            return []