import requests
import os
import sys
from typing import Optional

def upload_image(file_path: str, server_url: str = "http://localhost:5000/upload") -> Optional[dict]:
    """
    Upload an image file to the server for face recognition.
    
    Args:
        file_path: Path to the image file
        server_url: URL of the upload endpoint
    
    Returns:
        Response data as dictionary or None if failed
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return None
    
    if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
        print(f"Error: Unsupported file format - {file_path}")
        return None
    
    try:
        with open(file_path, "rb") as img:
            filename = os.path.basename(file_path)
            files = {"file": (filename, img, "image/jpeg")}
            
            print(f"Uploading {filename}...")
            response = requests.post(server_url, files=files, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response: {result}")
                    return result
                except:
                    print(f"Response: {response.text}")
                    return {"message": response.text}
            else:
                print(f"Error: {response.text}")
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    """Main function to handle command line usage."""
    if len(sys.argv) != 2:
        print("Usage: python test_send.py <image_file_path>")
        print("Example: python test_send.py zuck.JPG")
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = upload_image(file_path)
    
    if result:
        print("Upload successful!")
    else:
        print("Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    # Default behavior for backwards compatibility
    if len(sys.argv) == 1:
        file_path = "zuck.JPG"
        upload_image(file_path)
    else:
        main()

