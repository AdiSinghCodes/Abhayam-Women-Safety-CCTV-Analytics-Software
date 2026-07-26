import torch
import cv2
import os
import time
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import cloudinary
import cloudinary.uploader
import google.generativeai as genai
from twilio.rest import Client

# Cloudinary Configuration
cloudinary.config(
    cloud_name="x9hvkwqw",
    api_key="212353164148213",
    api_secret="w0r7fzNt6zsRsdcfvihIifICCbA"
)

# Twilio credentials
TWILIO_ACCOUNT_SID = 'ACb09fc5984472acf88bccc6e7009c7819'
TWILIO_AUTH_TOKEN = 'c29f51d881e980b17328f2a1661f3159'  # Replace with your actual token
TWILIO_PHONE_NUMBER = 'whatsapp:+14155238886'
TO_PHONE_NUMBER = 'whatsapp:+917304064579'

def send_whatsapp_alert(message, cloudinary_url):
    """
    Send a WhatsApp alert with the Cloudinary image as a direct photo
    """
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            to=TO_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            body=message,  # Text message
            media_url=[cloudinary_url]  # Cloudinary image URL as media
        )
        print(f"WhatsApp alert sent with image: {cloudinary_url}")
    except Exception as e:
        print(f"Error sending WhatsApp alert: {str(e)}")

# Configure Gemini API key and model
genai.configure(api_key="AQ.Ab8RN6J1AHXRFvc1_cd8YvnlFGatzuPfW3e8hVKBREGRtM6lmQ")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

# Load YOLOv5 model for detecting people
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Use small model for fast inference

# Function to detect people in an image using YOLOv5
def detect_people(image_path):
    # Load the image
    img = cv2.imread(image_path)
    
    # Perform inference with YOLO
    results = yolo_model(img)
    
    # Count the number of people (class 0 is for 'person')
    person_count = 0
    for result in results.xyxy[0].cpu().numpy():  # Move tensor to CPU before converting to NumPy
        if result[5] == 0:  # class_id for person
            person_count += 1
    
    return person_count

# Function to use Gemini to check if a woman is present in the image
def classify_gender_with_gemini(image_path):
    """
    Use Gemini to classify gender in the image.
    Returns True if a woman is detected, False otherwise.
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Define the prompt for Gemini
        prompt = """
        Analyze the image and determine if there is a woman present. 
        Focus on the following:
        1. Facial features (e.g., long hair, makeup, feminine traits).
        2. Clothing (e.g., dresses, skirts, or other feminine attire).
        3. Body structure (e.g., curves, posture).
        
        Respond with only 'yes' if a woman is detected, otherwise respond with 'no'.
        """
        
        # Use Gemini to analyze the image with the prompt
        response = model.generate_content([prompt, image])
        
        # Parse the response
        if "yes" in response.text.lower():
            return True  # Woman detected
        else:
            return False  # No woman detected
    except Exception as e:
        print(f"Error using Gemini for gender classification: {str(e)}")
        return False

# Function to apply modifications to the image
def modify_image(image_path):
    image = Image.open(image_path)
    # Example modification: resizing
    modified_image = image.resize((800, 800))
    modified_path = f"modified_{os.path.basename(image_path)}"
    modified_image.save(modified_path)
    return modified_path

# Check if the image has been previously modified
def is_already_modified(image_path):
    return os.path.exists(f"modified_{os.path.basename(image_path)}")

# Function to upload image to Cloudinary
def upload_to_cloudinary(image_path):
    result = cloudinary.uploader.upload(image_path, folder="one_female_images")
    return result['secure_url']

# Function to process the newly added image in one_female folder
def process_new_image(file_path):
    # Check if the image is inside the one_female folder or its subfolders
    if 'one_female' not in file_path.split(os.path.sep):
        print(f"Skipping image from outside 'one_female' folder: {file_path}")
        return  # Skip images not from 'one_female'

    # Skip images that already have '_modified' in the filename
    if "_modified" in os.path.basename(file_path):
        print(f"Skipping already modified image: {file_path}")
        return  # Skip already modified images
    
    # Detect people in the image
    person_count = detect_people(file_path)
    if person_count != 1:
        print(f"{file_path} has {person_count} person(s). Skipping without alert or deletion.")
        return

    # Use Gemini to check if the person is a woman
    is_woman = classify_gender_with_gemini(file_path)
    if not is_woman:
        print(f"{file_path} does not contain a woman. Skipping without alert or deletion.")
        return

    # Modify and upload the image to Cloudinary if valid
    modified_file_path = modify_image(file_path)
    cloudinary_url = upload_to_cloudinary(modified_file_path)
    send_whatsapp_alert("Lone Women Detected", cloudinary_url)

# Watchdog Event Handler to handle new image additions
class ImageProcessorHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"New image detected: {event.src_path}")
            process_new_image(event.src_path)

# Main function to start the Watchdog observer
def start_watchdog(base_directory):
    event_handler = ImageProcessorHandler()
    observer = Observer()
    observer.schedule(event_handler, path=base_directory, recursive=True)
    observer.start()
    print(f"Watching for new images in '{base_directory}'...")
    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("Stopped watching for new images.")

# Main entry point
if __name__ == "__main__":
    base_directory = os.getcwd()  # Or specify the path if it's different
    start_watchdog(base_directory)