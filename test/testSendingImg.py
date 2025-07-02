import requests
import os

def send_image_to_server(image_path, server_url):
    """
    Send an image file to the server
    
    Args:
        image_path (str): Path to the image file
        server_url (str): Server endpoint URL
    
    Returns:
        dict: Response from server
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return None
        
        # Open and read the image file
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            
            # Send POST request with the image
            response = requests.post(server_url, files=files)
            
            # Check response status
            if response.status_code == 200:
                print("Image sent successfully!")
                return response.json() if response.content else {"status": "success"}
            else:
                print(f"Error: Server responded with status code {response.status_code}")
                return {"error": f"HTTP {response.status_code}", "message": response.text}
                
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return {"error": "Request failed", "message": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "Unexpected error", "message": str(e)}

if __name__ == "__main__":
    # Configuration
    SERVER_URL = "http://127.0.0.1:5000/upload"  # Replace with your server URL
    IMAGE_PATH = "C:/Users/Ben Yedder/Desktop/stage/smart_enterprise/test/Musk/musk1.JPG"  # Replace with your image path
    
    # Send the image
    result = send_image_to_server(IMAGE_PATH, SERVER_URL)
    
    if result:
        print("Response:", result)
