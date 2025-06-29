import cv2
import face_recognition
import numpy as np
import os
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, tolerance: float = 0.6):
        """Initialize face recognizer with configurable tolerance."""
        self.known_face_encodings = []
        self.known_face_names = []
        self.tolerance = tolerance
        
    def load_known_faces(self, faces_directory: str) -> None:
        """Load known faces from a directory containing subdirectories for each person."""
        if not os.path.exists(faces_directory):
            logger.error(f"Faces directory not found: {faces_directory}")
            return
            
        loaded_count = 0
        for person_name in os.listdir(faces_directory):
            person_dir = os.path.join(faces_directory, person_name)
            if os.path.isdir(person_dir):
                for image_file in os.listdir(person_dir):
                    if self._is_image_file(image_file):
                        image_path = os.path.join(person_dir, image_file)
                        if self._add_known_face(image_path, person_name):
                            loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} known faces from {faces_directory}")
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if file is a supported image format."""
        return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
    
    def _add_known_face(self, image_path: str, name: str) -> bool:
        """Add a single known face to the recognizer."""
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                logger.warning(f"No faces found in {image_path}")
                return False
                
            self.known_face_encodings.append(encodings[0])
            self.known_face_names.append(name)
            logger.info(f"Added face for {name} from {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading {image_path}: {e}")
            return False
    
    def recognize_faces_in_image(self, image_path: str) -> List[str]:
        """Recognize faces in a single image and return the names of recognized faces."""
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []
            
        try:
            image = face_recognition.load_image_file(image_path)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                logger.info(f"No faces detected in {image_path}")
                return []
            
            face_names = []
            for face_encoding in face_encodings:
                name = self._identify_face(face_encoding)
                face_names.append(name)
                logger.info(f"Face identified as: {name}")
            
            return face_names
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return []
    
    def _identify_face(self, face_encoding) -> str:
        """Identify a single face encoding."""
        if not self.known_face_encodings:
            return "Unknown"
            
        matches = face_recognition.compare_faces(
            self.known_face_encodings, face_encoding, tolerance=self.tolerance
        )
        
        if not any(matches):
            return "Unknown"
            
        face_distances = face_recognition.face_distance(
            self.known_face_encodings, face_encoding
        )
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            return self.known_face_names[best_match_index]
        
        return "Unknown"