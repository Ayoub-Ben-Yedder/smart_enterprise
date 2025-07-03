import os
import logging
import shutil
from flask import Blueprint, request, jsonify
from database import DatabaseManager
from auth import AuthManager
from config import EMPLOYEES_FACES_FOLDER

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, face_recognizer, websocket_client):
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager()
        self.face_recognizer = face_recognizer
        self.websocket_client = websocket_client
        self.api_bp = Blueprint('api', __name__, url_prefix='/api')
        self._setup_api_routes()
    
    def _setup_api_routes(self):
        """Setup API routes."""
        
        @self.api_bp.route('/login', methods=['POST'])
        def api_login():
            """Handle login requests."""
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                success, message = self.auth_manager.authenticate_user(username, password)
                
                if success:
                    return jsonify({"message": message}), 200
                else:
                    return jsonify({"error": message}), 401
                    
            except Exception as e:
                logger.error(f"Error during login: {e}")
                return jsonify({"error": "Login failed"}), 500
        
        @self.api_bp.route('/logout', methods=['POST'])
        def api_logout():
            """Handle logout requests."""
            success, message = self.auth_manager.logout_user()
            return jsonify({"message": message}), 200
        
        @self.api_bp.route('/status')
        @self.auth_manager.login_required
        def api_status():
            """API endpoint to check server status."""
            return jsonify({
                "status": "running",
                "esp32_connected": self.websocket_client.is_connected(),
                "known_faces_loaded": len(self.face_recognizer.known_face_names)
            })
        
        @self.api_bp.route('/cameras', methods=['GET'])
        @self.auth_manager.login_required
        def api_get_cameras():
            """Get all cameras."""
            try:
                cameras = self.db_manager.get_all_cameras()
                return jsonify([{
                    "id": c[0], "name": c[1], "ip_address": c[2], "port": c[3],
                    "stream_path": c[4], "username": c[5], "password": c[6], "is_active": c[7]
                } for c in cameras])
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.api_bp.route('/cameras', methods=['POST'])
        @self.auth_manager.login_required
        def api_add_camera():
            """Add new camera."""
            try:
                data = request.get_json()
                conn = self.db_manager._get_connection()
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
        @self.api_bp.route('/cameras/<int:camera_id>', methods=['DELETE'])
        @self.auth_manager.login_required
        def api_delete_camera(camera_id):
            """Delete a camera by ID."""
            try:
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM ip_cameras WHERE id = ?', (camera_id,))
                conn.commit()
                conn.close()
                return jsonify({"message": "Camera deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.api_bp.route('/employees', methods=['GET'])
        @self.auth_manager.login_required
        def api_get_employees():
            """Get all employees."""
            try:
                employees_data = self.db_manager.get_all_employees()
                
                # Add image count for each employee
                employees_list = []
                for emp in employees_data:
                    emp_dir = os.path.join(EMPLOYEES_FACES_FOLDER, emp[1])
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

        @self.api_bp.route('/employees', methods=['POST'])
        @self.auth_manager.login_required
        def api_add_employee():
            """Add new employee with images."""
            try:
                name = request.form.get('name')
                national_id = request.form.get('national_id')
                
                if not name or not national_id:
                    return jsonify({"error": "Name and National ID are required"}), 400
                
                # Check if employee already exists
                conn = self.db_manager._get_connection()
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
                
                # Create employee directory and save images
                employee_dir = os.path.join(EMPLOYEES_FACES_FOLDER, name)
                os.makedirs(employee_dir, exist_ok=True)
                
                saved_images = []
                for i in range(1, 4):
                    image_key = f'image{i}'
                    if image_key in request.files:
                        file = request.files[image_key]
                        if file and file.filename:
                            ext = os.path.splitext(file.filename)[1].lower()
                            if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                                ext = '.jpg'
                            filename = f"{name}_{i}{ext}"
                            file_path = os.path.join(employee_dir, filename)
                            file.save(file_path)
                            saved_images.append(filename)
                
                # Reload known faces
                self.face_recognizer.load_known_faces(EMPLOYEES_FACES_FOLDER)
                
                return jsonify({
                    "message": "Employee added successfully",
                    "employee_id": employee_id,
                    "saved_images": saved_images
                }), 201
                
            except Exception as e:
                logger.error(f"Error adding employee: {e}")
                return jsonify({"error": str(e)}), 500
        @self.api_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
        @self.auth_manager.login_required
        def api_delete_employee(employee_id):
            """Delete an employee by ID."""
            try:
                # Get employee name to delete images
                conn = self.db_manager._get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM employees WHERE id = ?', (employee_id,))
                employee = cursor.fetchone()
                
                if not employee:
                    return jsonify({"error": "Employee not found"}), 404
                
                employee_name = employee[0]
                
                # Delete employee from database
                cursor.execute('UPDATE employees SET is_active = 0 WHERE id = ?', (employee_id,))
                conn.commit()
                conn.close()
                
                # Delete employee directory and images
                employee_dir = os.path.join(EMPLOYEES_FACES_FOLDER, employee_name)
                if os.path.exists(employee_dir):
                    shutil.rmtree(employee_dir)
                
                # Reload known faces
                self.face_recognizer.load_known_faces(EMPLOYEES_FACES_FOLDER)
                
                return jsonify({"message": "Employee deleted successfully"}), 200
                
            except Exception as e:
                logger.error(f"Error deleting employee: {e}")
                return jsonify({"error": str(e)}), 500

        @self.api_bp.route('/energy/usage', methods=['GET'])
        @self.auth_manager.login_required
        def api_get_energy_usage():
            """Get energy usage statistics."""
            try:
                # Get current device status from database
                lamp_status = self.db_manager.get_device_status('lamp')
                outlet_status = self.db_manager.get_device_status('outlet')
                
                # Calculate usage time for energy calculations
                lamp_today = self.db_manager.calculate_device_usage_time('lamp', 1)
                lamp_week = self.db_manager.calculate_device_usage_time('lamp', 7)
                outlet_today = self.db_manager.calculate_device_usage_time('outlet', 1)
                outlet_week = self.db_manager.calculate_device_usage_time('outlet', 7)
                
                return jsonify({
                    "lamp_status": lamp_status,
                    "outlet_status": outlet_status,
                    "lamp_today_minutes": lamp_today,
                    "lamp_week_minutes": lamp_week,
                    "outlet_today_minutes": outlet_today,
                    "outlet_week_minutes": outlet_week
                })
            except Exception as e:
                logger.error(f"Error getting energy usage: {e}")
                return jsonify({"error": str(e)}), 500

        @self.api_bp.route('/energy/event', methods=['POST'])
        @self.auth_manager.login_required
        def api_save_energy_event():
            """Save energy event."""
            try:
                data = request.get_json()
                device = data.get('device')
                action = data.get('action')
                
                if not device or not action:
                    return jsonify({"error": "Device and action are required"}), 400
                
                self.db_manager.save_energy_event(device, action)
                self.db_manager.update_device_status(device, action)
                return jsonify({"message": "Energy event saved"}), 200
                
            except Exception as e:
                logger.error(f"Error saving energy event: {e}")
                return jsonify({"error": str(e)}), 500

        @self.api_bp.route('/energy/activity', methods=['GET'])
        @self.auth_manager.login_required
        def api_get_energy_activity():
            """Get recent energy activity."""
            try:
                limit = request.args.get('limit', 20, type=int)
                activities = self.db_manager.get_recent_energy_activity(limit)
                
                return jsonify([{
                    "id": a[0],
                    "device": a[1],
                    "action": a[2],
                    "timestamp": a[3],
                    "duration": a[4] if len(a) > 4 else None
                } for a in activities])
            except Exception as e:
                logger.error(f"Error getting energy activity: {e}")
                return jsonify({"error": str(e)}), 500

    def get_blueprint(self):
        """Return the API blueprint."""
        return self.api_bp
