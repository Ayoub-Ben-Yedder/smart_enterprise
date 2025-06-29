import cv2
import face_recognition
import numpy as np
import os
from typing import List, Tuple, Optional

class FaceRecognizer:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        
    def load_known_faces(self, faces_directory: str) -> None:
        """Load known faces from a directory containing subdirectories for each person"""
        for person_name in os.listdir(faces_directory):
            person_dir = os.path.join(faces_directory, person_name)
            if os.path.isdir(person_dir):
                for image_file in os.listdir(person_dir):
                    if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_path = os.path.join(person_dir, image_file)
                        self._add_known_face(image_path, person_name)
    
    def _add_known_face(self, image_path: str, name: str) -> None:
        """Add a single known face to the recognizer"""
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                self.known_face_encodings.append(encodings[0])
                self.known_face_names.append(name)
                print(f"Added face for {name}")
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
    
    def recognize_faces_in_image(self, image_path: str) -> Tuple[np.ndarray, List[str], List[Tuple[int, int, int, int]]]:
        """Recognize faces in a single image and return the name of the recognized faces"""
        image = face_recognition.load_image_file(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"
            
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                name = self.known_face_names[best_match_index]
            
            face_names.append(name)
        
        return face_names