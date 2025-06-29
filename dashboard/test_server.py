from flask import Flask, request, render_template, send_from_directory
import sqlite3
import os
import websocket
import threading
from vision import FaceRecognizer  

# Initialize face recognizer
face_recognizer = FaceRecognizer()
face_recognizer.load_known_faces("./known_faces")


app = Flask(__name__)

# WebSocket connection to ESP32
ws_connection = None

def connect_to_esp32():
    global ws_connection
    try:
        ws_connection = websocket.WebSocket()
        ws_connection.connect("ws://192.168.1.28/ws")
        print("Connected to ESP32 WebSocket")
    except Exception as e:
        print(f"Failed to connect to ESP32: {e}")
        ws_connection = None

def send_command(command):
    global ws_connection
    try:
        if ws_connection is None:
            connect_to_esp32()
        
        if ws_connection:
            ws_connection.send(command)
            print(f"Sent command: {command}")
    except Exception as e:
        print(f"Error sending command: {e}")
        ws_connection = None

# Initialize WebSocket connection on startup
connect_to_esp32()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/gallery')
def gallery():
    # Get all photos from database
    conn = sqlite3.connect('photos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM photos ORDER BY id DESC')
    photos = cursor.fetchall()
    conn.close()
    return render_template('gallery.html', photos=photos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('./uploads', filename)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return "No data received", 400  # This is where your error comes from

        file = request.files['file']

        if file.filename == '':
            return "No file selected", 400

        # Create uploads directory if it doesn't exist
        os.makedirs('./uploads', exist_ok=True)

        # Extract just the filename without path
        filename = os.path.basename(file.filename)
        file.save(f"./uploads/{filename}")

        # Recognize faces in the uploaded image
        print(f"Processing file: {filename}")
        names = face_recognizer.recognize_faces_in_image(f"./uploads/{filename}")
        
        if len(names)!=0:
            if "Unknown" in names:
                print("Face not recognized or access denied")
            else:
                print(f"Face recognized: {names[0]}")
                send_command('open_door')
        else:
            print("No faces found in the image")
    

        # connect to SQLite database
        conn = sqlite3.connect('photos.db')
        cursor = conn.cursor()
        # create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL
            )
        ''')
        # insert file information into the database
        cursor.execute('INSERT INTO photos (filename) VALUES (?)', (filename,))
        conn.commit()
        conn.close()

        return "File uploaded successfully", 200
    
    except Exception as e:
        return f"Error uploading file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
