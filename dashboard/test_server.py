from flask import Flask, request, render_template, send_from_directory
import sqlite3
import os

app = Flask(__name__)

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
