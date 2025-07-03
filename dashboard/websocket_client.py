import websocket
import logging
from config import ESP32_WEBSOCKET_URL

logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self):
        self.ws_connection = None
        self.websocket_url = ESP32_WEBSOCKET_URL
        self.db_manager = None
    
    def set_database_manager(self, db_manager):
        """Set the database manager for status tracking."""
        self.db_manager = db_manager
    
    def connect(self):
        """Establish WebSocket connection to ESP32."""
        try:
            self.ws_connection = websocket.WebSocket()
            self.ws_connection.connect(self.websocket_url)
            logger.info("Connected to ESP32 WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ESP32: {e}")
            self.ws_connection = None
            return False
    
    def send_command(self, command: str) -> bool:
        """Send command to ESP32 and track device status."""
        try:
            if self.ws_connection is None:
                self.connect()
            
            if self.ws_connection:
                self.ws_connection.send(command)
                logger.info(f"Sent command: {command}")
                
                # Track device status based on command
                if self.db_manager:
                    if command == 'turn_on_lamp':
                        self.db_manager.update_device_status('lamp', 'on')
                        self.db_manager.save_energy_event('lamp', 'on')
                    elif command == 'turn_off_lamp':
                        self.db_manager.update_device_status('lamp', 'off')
                        self.db_manager.save_energy_event('lamp', 'off')
                    elif command == 'turn_on_pris':
                        self.db_manager.update_device_status('outlet', 'on')
                        self.db_manager.save_energy_event('outlet', 'on')
                    elif command == 'turn_off_pris':
                        self.db_manager.update_device_status('outlet', 'off')
                        self.db_manager.save_energy_event('outlet', 'off')
                
                return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.ws_connection = None
        return False
    
    def is_connected(self):
        """Check if WebSocket is connected."""
        return self.ws_connection is not None
