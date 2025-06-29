import requests

url = "http://localhost:5000/upload"
file_path = "test_face1.JPG"
# Open the image in binary mode
with open(file_path, "rb") as img:
    # Send only the filename, not the full path
    filename = file_path.split("/")[-1]  # Extract just the filename
    files = {"file": (filename, img, "image/jpeg")}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response:", response.text)

