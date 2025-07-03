from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import logging
from vision import FaceRecognizer
from database import DatabaseManager
from auth import AuthManager
from websocket_client import WebSocketClient
from api import APIManager
from config import UPLOAD_FOLDER, EMPLOYEES_FACES_FOLDER, DATABASE_FILE, ESP32_WEBSOCKET_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartEnterpriseServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your-secret-key-change-in-production'
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager()
        self.websocket_client = WebSocketClient()
        self.face_recognizer = FaceRecognizer()
        
        # Setup
        self._setup_directories()
        self._setup_database()
        self._load_known_faces()
        self._connect_to_esp32()
        self._setup_routes()
        self._setup_api()
    
    def _setup_directories(self):
        """Create necessary directories."""
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(EMPLOYEES_FACES_FOLDER, exist_ok=True)
    
    def _setup_database(self):
        """Initialize the database."""
        self.db_manager.init_database()
        
    def _load_known_faces(self):
        """Load known faces for recognition."""
        self.face_recognizer.load_known_faces(EMPLOYEES_FACES_FOLDER)
    
    def _connect_to_esp32(self):
        """Establish WebSocket connection to ESP32."""
        self.websocket_client.connect()
    
    def _setup_api(self):
        """Setup API routes."""
        api_manager = APIManager(self.face_recognizer, self.websocket_client)
        self.app.register_blueprint(api_manager.get_blueprint())
    
    def _setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/login')
        def login():
            from flask import session, redirect, url_for
            if 'user_id' in session:
                return redirect(url_for('index'))
            return render_template('login.html')
        
        @self.app.route('/')
        @self.auth_manager.login_required
        def index():
            return render_template('dashboard.html', websocket_url=ESP32_WEBSOCKET_URL)
        
        @self.app.route('/employees')
        @self.auth_manager.login_required
        def employees():
            try:
                employees_data = self.db_manager.get_all_employees()
                return render_template('employees.html', employees=employees_data)
            except Exception as e:
                logger.error(f"Error loading employees: {e}")
                return render_template('employees.html', employees=[])
        
        @self.app.route('/surveillance')
        @self.auth_manager.login_required
        def surveillance():
            try:
                cameras = self.db_manager.get_all_cameras()
                return render_template('surveillance.html', cameras=cameras)
            except Exception as e:
                logger.error(f"Error loading cameras: {e}")
                return render_template('surveillance.html', cameras=[])

        @self.app.route('/accessHistory')
        @self.auth_manager.login_required
        def accessHistory():
            try:
                photos = self.db_manager.get_all_photos()
                return render_template('accessHistory.html', photos=photos)
            except Exception as e:
                logger.error(f"Error loading access history: {e}")
                return render_template('accessHistory.html', photos=[])

        @self.app.route('/uploads/<filename>')
        def uploaded_file(filename):
            return send_from_directory(UPLOAD_FOLDER, filename)

        @self.app.route('/employees/<employee_name>/<filename>')
        @self.auth_manager.login_required
        def employee_image(employee_name, filename):
            """Serve employee images."""
            employee_dir = os.path.join(EMPLOYEES_FACES_FOLDER, employee_name)
            return send_from_directory(employee_dir, filename)

        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self._handle_upload()

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
                    self.websocket_client.send_command('open_door')
                    access_granted = True
                else:
                    logger.warning("Unknown face detected - access denied")
                    self.websocket_client.send_command('close_door')
            else:
                logger.info("No faces detected in image")
                self.websocket_client.send_command('close_door')
            
            # Save to database
            self.db_manager.save_photo_record(filename, recognized_names)

            return jsonify({
                "message": "File uploaded successfully",
                "recognized_faces": recognized_names,
                "access_granted": access_granted
            }), 200

        except Exception as e:
            logger.error(f"Error handling upload: {e}")
            return jsonify({"error": str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Run the Flask application."""
        logger.info(f"Starting server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Create and run the server
if __name__ == '__main__':
    server = SmartEnterpriseServer()
    server.run(host='0.0.0.0', port=5000, debug=True)