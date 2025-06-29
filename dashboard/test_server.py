from flask import Flask, request, render_template, send_from_directory, jsonify
import sqlite3
import os
import websocket
import logging
from vision import FaceRecognizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ESP32_WEBSOCKET_URL = "ws://192.168.1.28/ws"
UPLOAD_FOLDER = './uploads'
KNOWN_FACES_FOLDER = './known_faces'
DATABASE_FILE = 'photos.db'

class SmartEnterpriseServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.ws_connection = None
        self.face_recognizer = FaceRecognizer()
        self._setup_directories()
        self._setup_database()
        self._load_known_faces()
        self._setup_routes()
        self._connect_to_esp32()
    
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
    
    def _setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')

        @self.app.route('/gallery')
        def gallery():
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM photos ORDER BY id DESC')
                photos = cursor.fetchall()
                conn.close()
                return render_template('gallery.html', photos=photos)
            except Exception as e:
                logger.error(f"Error loading gallery: {e}")
                return render_template('gallery.html', photos=[])

        @self.app.route('/uploads/<filename>')
        def uploaded_file(filename):
            return send_from_directory(UPLOAD_FOLDER, filename)

        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self._handle_upload()
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint to check server status."""
            return jsonify({
                "status": "running",
                "esp32_connected": self.ws_connection is not None,
                "known_faces_loaded": len(self.face_recognizer.known_face_names)
            })
    
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
