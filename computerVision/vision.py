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
        """Recognize faces in a single image"""
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
        
        return rgb_image, face_names, face_locations
    
    def recognize_faces_in_video(self, video_source: int = 0) -> None:
        """Recognize faces in real-time video stream"""
        video_capture = cv2.VideoCapture(video_source)
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"
                
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                        name = self.known_face_names[best_match_index]
                
                face_names.append(name)
            
            # Scale back up face locations
            face_locations = [(top*4, right*4, bottom*4, left*4) for (top, right, bottom, left) in face_locations]
            
            # Draw rectangles and names
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Face Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        video_capture.release()
        cv2.destroyAllWindows()
    
    def display_image_with_faces(self, image: np.ndarray, face_names: List[str], face_locations: List[Tuple[int, int, int, int]]) -> None:
        """Display image with recognized faces marked"""
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(image_bgr, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(image_bgr, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('Face Recognition', image_bgr)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    recognizer = FaceRecognizer()
    
    # Load known faces from directory structure like:
    # known_faces/
    #   ├── person1/
    #   │   ├── photo1.jpg
    #   │   └── photo2.jpg
    #   └── person2/
    #       └── photo1.jpg
    
    recognizer.load_known_faces("./known_faces")
    
    # Recognize faces in video stream
    recognizer.recognize_faces_in_video()
    
    # Or recognize faces in a single image
    # image, names, locations = recognizer.recognize_faces_in_image("path/to/test_image.jpg")
    # recognizer.display_image_with_faces(image, names, locations)
