from flask import Flask, request, render_template, send_from_directory, jsonify, session, redirect, url_for
import sqlite3
import os
import websocket
import logging
from vision import FaceRecognizer
from functools import wraps
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ESP32_WEBSOCKET_URL = "ws://192.168.1.16/ws"
UPLOAD_FOLDER = './accessHistory'
KNOWN_FACES_FOLDER = './employees'
DATABASE_FILE = 'entreprise.db'

class SmartEnterpriseServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your-secret-key-change-in-production'  # Change this in production!
        self.ws_connection = None
        self.face_recognizer = FaceRecognizer()
        self._setup_directories()
        self._setup_database()
        self._load_known_faces()
        self._setup_routes()
        #self._connect_to_esp32()
    
    def _setup_directories(self):
        """Create necessary directories."""
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(KNOWN_FACES_FOLDER, exist_ok=True)
    
    def _setup_database(self):
        """Initialize the database."""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    recognized_faces TEXT
                )
            ''')
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    national_id TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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
    def _load_known_faces(self):
        """Load known faces for recognition."""
        self.face_recognizer.load_known_faces(KNOWN_FACES_FOLDER)
    
    def _connect_to_esp32(self):
        """Establish WebSocket connection to ESP32."""
        try:
            self.ws_connection = websocket.WebSocket()
            self.ws_connection.connect(ESP32_WEBSOCKET_URL)
            logger.info("Connected to ESP32 WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to ESP32: {e}")
            self.ws_connection = None
    
    def _send_command(self, command: str) -> bool:
        """Send command to ESP32."""
        try:
            if self.ws_connection is None:
                self._connect_to_esp32()
            
            if self.ws_connection:
                self.ws_connection.send(command)
                logger.info(f"Sent command: {command}")
                return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.ws_connection = None
        return False
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password, password_hash):
        """Verify password against hash."""
        return self._hash_password(password) == password_hash
    
    def _login_required(self, f):
        """Decorator to require login for routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def _setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/login')
        def login():
            if 'user_id' in session:
                return redirect(url_for('index'))
            return render_template('login.html')
        
        @self.app.route('/api/login', methods=['POST'])
        def api_login():
            """Handle login requests."""
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                if not username or not password:
                    return jsonify({"error": "Username and password are required"}), 400
                
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, password_hash FROM users 
                    WHERE username = ? AND is_active = 1
                ''', (username,))
                user = cursor.fetchone()
                conn.close()
                
                if user and self._verify_password(password, user[2]):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    logger.info(f"User {username} logged in successfully")
                    return jsonify({"message": "Login successful"}), 200
                else:
                    logger.warning(f"Failed login attempt for username: {username}")
                    return jsonify({"error": "Invalid username or password"}), 401
                    
            except Exception as e:
                logger.error(f"Error during login: {e}")
                return jsonify({"error": "Login failed"}), 500
        
        @self.app.route('/api/logout', methods=['POST'])
        def api_logout():
            """Handle logout requests."""
            session.clear()
            return jsonify({"message": "Logout successful"}), 200
        
        @self.app.route('/')
        @self._login_required
        def index():
            return render_template('dashboard.html', websocket_url=ESP32_WEBSOCKET_URL)
        
        @self.app.route('/employees')
        @self._login_required
        def employees():
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM employees WHERE is_active = 1 ORDER BY name')
                employees_data = cursor.fetchall()
                conn.close()
                return render_template('employees.html', employees=employees_data)
            except Exception as e:
                logger.error(f"Error loading employees: {e}")
                return render_template('employees.html', employees=[])
        @self.app.route('/surveillance')
        @self._login_required
        def surveillance():
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ip_cameras WHERE is_active = 1 ORDER BY name')
                cameras = cursor.fetchall()
                conn.close()
                return render_template('surveillance.html', cameras=cameras)
            except Exception as e:
                logger.error(f"Error loading cameras: {e}")
                return render_template('surveillance.html', cameras=[])

        @self.app.route('/accessHistory')
        @self._login_required
        def accessHistory():
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM photos ORDER BY id DESC')
                photos = cursor.fetchall()
                conn.close()
                return render_template('accessHistory.html', photos=photos)
            except Exception as e:
                logger.error(f"Error loading access history: {e}")
                return render_template('accessHistory.html', photos=[])

        @self.app.route('/uploads/<filename>')
        def uploaded_file(filename):
            return send_from_directory(UPLOAD_FOLDER, filename)

        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self._handle_upload()
        
        @self.app.route('/api/status')
        @self._login_required
        def api_status():
            """API endpoint to check server status."""
            return jsonify({
                "status": "running",
                "esp32_connected": self.ws_connection is not None,
                "known_faces_loaded": len(self.face_recognizer.known_face_names)
            })
        
        @self.app.route('/api/cameras', methods=['GET'])
        @self._login_required
        def api_get_cameras():
            """Get all cameras."""
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ip_cameras ORDER BY name')
                cameras = cursor.fetchall()
                conn.close()
                return jsonify([{
                    "id": c[0], "name": c[1], "ip_address": c[2], "port": c[3],
                    "stream_path": c[4], "username": c[5], "password": c[6], "is_active": c[7]
                } for c in cameras])
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/cameras', methods=['POST'])
        @self._login_required
        def api_add_camera():
            """Add new camera."""
            try:
                data = request.get_json()
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ip_cameras (name, ip_address, port, stream_path, username, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (data['name'], data['ip_address'], data.get('port', 8080),
                      data.get('stream_path', '/stream'), data.get('username'),
                      data.get('password')))
                conn.commit()
                conn.close()
                return jsonify({"message": "Camera added successfully"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
        @self._login_required
        def api_delete_camera(camera_id):
            """Delete camera."""
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('UPDATE ip_cameras SET is_active = 0 WHERE id = ?', (camera_id,))
                conn.commit()
                conn.close()
                return jsonify({"message": "Camera deleted successfully"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/employees', methods=['GET'])
        @self._login_required
        def api_get_employees():
            """Get all employees."""
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM employees WHERE is_active = 1 ORDER BY name')
                employees_data = cursor.fetchall()
                conn.close()
                
                # Add image count for each employee
                employees_list = []
                for emp in employees_data:
                    emp_dir = os.path.join(KNOWN_FACES_FOLDER, emp[1])  # emp[1] is name
                    image_count = 0
                    if os.path.exists(emp_dir):
                        image_count = len([f for f in os.listdir(emp_dir) 
                                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))])
                    
                    employees_list.append({
                        "id": emp[0], "name": emp[1], "national_id": emp[2], 
                        "created_at": emp[3], "is_active": emp[4], "image_count": image_count
                    })
                
                return jsonify(employees_list)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/employees', methods=['POST'])
        @self._login_required
        def api_add_employee():
            """Add new employee with images."""
            try:
                name = request.form.get('name')
                national_id = request.form.get('national_id')
                
                if not name or not national_id:
                    return jsonify({"error": "Name and National ID are required"}), 400
                
                # Check if employee already exists
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM employees WHERE national_id = ? AND is_active = 1', (national_id,))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({"error": "Employee with this National ID already exists"}), 400
                
                # Add employee to database
                cursor.execute('''
                    INSERT INTO employees (name, national_id) VALUES (?, ?)
                ''', (name, national_id))
                employee_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # Create employee directory
                employee_dir = os.path.join(KNOWN_FACES_FOLDER, name)
                os.makedirs(employee_dir, exist_ok=True)
                
                # Save uploaded images
                saved_images = []
                for i in range(1, 4):  # image1, image2, image3
                    image_key = f'image{i}'
                    if image_key in request.files:
                        file = request.files[image_key]
                        if file and file.filename:
                            # Generate safe filename
                            ext = os.path.splitext(file.filename)[1].lower()
                            if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                                ext = '.jpg'
                            filename = f"{name}_{i}{ext}"
                            file_path = os.path.join(employee_dir, filename)
                            file.save(file_path)
                            saved_images.append(filename)
                            logger.info(f"Saved image: {file_path}")
                
                # Reload known faces
                self._load_known_faces()
                
                return jsonify({
                    "message": "Employee added successfully",
                    "employee_id": employee_id,
                    "saved_images": saved_images
                }), 201
                
            except Exception as e:
                logger.error(f"Error adding employee: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
        @self._login_required
        def api_delete_employee(employee_id):
            """Delete employee and their images."""
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                
                # Get employee info before deletion
                cursor.execute('SELECT name FROM employees WHERE id = ?', (employee_id,))
                employee = cursor.fetchone()
                if not employee:
                    conn.close()
                    return jsonify({"error": "Employee not found"}), 404
                
                employee_name = employee[0]
                
                # Mark employee as inactive
                cursor.execute('UPDATE employees SET is_active = 0 WHERE id = ?', (employee_id,))
                conn.commit()
                conn.close()
                
                # Remove employee directory and images
                employee_dir = os.path.join(KNOWN_FACES_FOLDER, employee_name)
                if os.path.exists(employee_dir):
                    import shutil
                    shutil.rmtree(employee_dir)
                    logger.info(f"Removed employee directory: {employee_dir}")
                
                # Reload known faces
                self._load_known_faces()
                
                return jsonify({"message": "Employee deleted successfully"})
                
            except Exception as e:
                logger.error(f"Error deleting employee: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/employees/<employee_name>/<filename>')
        @self._login_required
        def employee_image(employee_name, filename):
            """Serve employee images."""
            employee_dir = os.path.join(KNOWN_FACES_FOLDER, employee_name)
            return send_from_directory(employee_dir, filename)
        
        @self.app.route('/api/sensor-data', methods=['GET'])
        @self._login_required
        def api_get_sensor_data():
            """Get recent sensor data for charts."""
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT sensor_type, value, timestamp 
                    FROM sensor_data 
                    WHERE timestamp > datetime('now', '-1 hour')
                    ORDER BY timestamp DESC 
                    LIMIT 40
                ''')
                data = cursor.fetchall()
                conn.close()
                
                result = []
                for row in data:
                    result.append({
                        "sensor_type": row[0],
                        "value": row[1],
                        "timestamp": row[2]
                    })
                
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/sensor-data', methods=['POST'])
        @self._login_required
        def api_save_sensor_data():
            """Save sensor data."""
            try:
                data = request.get_json()
                sensor_type = data.get('sensor_type')
                value = data.get('value')
                
                if not sensor_type or value is None:
                    return jsonify({"error": "sensor_type and value are required"}), 400
                
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sensor_data (sensor_type, value) VALUES (?, ?)
                ''', (sensor_type, float(value)))
                conn.commit()
                conn.close()
                
                return jsonify({"message": "Sensor data saved successfully"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def _handle_upload(self):
        """Handle file upload and face recognition."""
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file provided"}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400

            # Save file
            filename = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            logger.info(f"File saved: {filename}")

            # Recognize faces
            recognized_names = self.face_recognizer.recognize_faces_in_image(file_path)
            
            # Process recognition results
            access_granted = False
            if recognized_names:
                if "Unknown" not in recognized_names:
                    logger.info(f"Access granted for: {recognized_names}")
                    self._send_command('open_door')
                    access_granted = True
                else:
                    logger.warning("Unknown face detected - access denied")
                    self._send_command('close_door')
            else:
                logger.info("No faces detected in image")
                self._send_command('close_door')
            
            # Save to database
            self._save_photo_record(filename, recognized_names)

            return jsonify({
                "message": "File uploaded successfully",
                "recognized_faces": recognized_names,
                "access_granted": access_granted
            }), 200

        except Exception as e:
            logger.error(f"Error handling upload: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _save_photo_record(self, filename: str, recognized_names: list):
        """Save photo record to database."""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
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
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Run the Flask application."""
        logger.info(f"Starting server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Create and run the server
if __name__ == '__main__':
    server = SmartEnterpriseServer()
    server.run(host='0.0.0.0', port=5000, debug=True)
