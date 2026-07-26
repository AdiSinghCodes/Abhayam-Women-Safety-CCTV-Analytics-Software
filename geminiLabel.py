import os
import base64
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
from twilio.rest import Client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import winsound
import csv
from datetime import datetime

# Configure Gemini API key and model
genai.configure(api_key="AQ.Ab8RN6J1AHXRFvc1_cd8YvnlFGatzuPfW3e8hVKBREGRtM6lmQ")
model = genai.GenerativeModel("gemini-1.5-flash")

# Cloudinary Configuration
cloudinary.config(
    cloud_name="x9hvkwqw", 
    api_key="212353164148213", 
    api_secret="w0r7fzNt6zsRsdcfvihIifICCbA"
)

# Twilio Configuration
twilio_client = Client("ACb09fc5984472acf88bccc6e7009c7819", "c29f51d881e980b17328f2a1661f3159")
twilio_whatsapp_number = "whatsapp:+14155238886"
recipient_whatsapp_number = "whatsapp:+917304064579"

# CSV file path
csv_file_path = "violence_detection_logs.csv"

# Ensure the CSV file exists and has headers
if not os.path.exists(csv_file_path):
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Message"])
def write_to_csv(message):
    """
    Writes the message with a timestamp to the CSV file in a single line.
    """
    try:
        # Replace newlines and double quotes to avoid issues
        message = message.replace("\n", " ").replace("\r", " ").replace('"', "'")
        
        with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)  # Ensure correct CSV formatting
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message])
    except Exception as e:
        print(f"Error writing to CSV: {str(e)}")



def upload_to_cloudinary(image_path):
    """
    Uploads the image to Cloudinary and returns the secure URL.
    """
    try:
        upload_result = cloudinary.uploader.upload(
            image_path, 
            folder="threat_analysis",
            overwrite=True
        )
        return upload_result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return None

def analyze_image_with_gemini(image_path):
    """
    Analyzes the image using Google Gemini AI to detect violence.
    """
    try:
        # Read the image file
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()

        # Encode the image data as base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Determine the MIME type based on the file extension
        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            mime_type = "image/jpeg"
        elif image_path.lower().endswith('.png'):
            mime_type = "image/png"
        else:
            return "Error: Unsupported image format. Only JPEG and PNG are supported."

        # Define the prompt for Gemini
        prompt = "Analyze this image and determine if there is any physical violence, fighting, hitting, slapping, punching, attack, or physical aggression. Provide a clear 'YES' or 'NO' answer followed by a brief description of what is happening in the scene."

        # Prepare the request payload
        request_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }

        # Send the request to the Gemini API
        response = model.generate_content(request_payload)
        return response.text.strip()
    except Exception as e:
        return f"Error analyzing image with Gemini: {str(e)}"
        
def send_alert_via_twilio(image_url, gemini_analysis):
    """
    Sends an alert via Twilio with the analysis result and a URL link to the image.
    Also saves the message with a timestamp to a CSV file.
    """
    message_body = f"Violence detected: {gemini_analysis} {image_url}".replace("\n", " ").replace("\r", " ").strip()

    # Log message before sending
    write_to_csv(message_body)

    # Send the message via Twilio
    try:
        twilio_client.messages.create(
            body=message_body,
            from_=twilio_whatsapp_number,
            to=recipient_whatsapp_number
        )
        print("Alert sent successfully!")
    except Exception as e:
        print(f"Error sending alert via Twilio: {str(e)}")


def process_image(image_path):
    """
    Processes the image: analyzes it, uploads it if violence is detected, and sends an alert.
    """
    try:
        gemini_analysis = analyze_image_with_gemini(image_path)
        print(f"Gemini Analysis: {gemini_analysis}")

        # Play a beep sound whenever an image is detected
        winsound.Beep(1000, 500)  # Frequency = 1000 Hz, Duration = 500 ms

        # Check if the response indicates violence/aggression
        analysis_lower = gemini_analysis.lower()
        violence_keywords = ["yes", "violence", "fight", "fighting", "attack", "hit", "hitting", "punch", "punching", "slap", "slapping", "aggressive"]
        is_threat = any(keyword in analysis_lower for keyword in violence_keywords) and "no violence" not in analysis_lower

        if is_threat or "yes" in analysis_lower:
            # Upload image to Cloudinary and send alert
            image_url = upload_to_cloudinary(image_path)
            if image_url:
                send_alert_via_twilio(image_url, gemini_analysis)
        else:
            print(f"Image retained in folder without alert: {image_path}")
    except Exception as e:
        print(f"Error processing image: {str(e)}")

def find_violence_folders(root_directory):
    """
    Finds all folders named 'violence_against_women' within the root directory.
    """
    violence_folders = []
    for root, dirs, files in os.walk(root_directory):
        for dir_name in dirs:
            if dir_name == 'violence_against_women':
                violence_folders.append(os.path.join(root, dir_name))
    return violence_folders

class WatchdogHandler(FileSystemEventHandler):
    """
    Watchdog event handler to monitor the directory for new images.
    """
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            if 'violence_against_women' in event.src_path.split(os.path.sep):
                print(f"New violence image detected: {event.src_path}")
                process_image(event.src_path)

def start_watchdog(directory):
    """
    Starts the Watchdog observer to monitor the specified directory.
    """
    event_handler = WatchdogHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"Watching directory recursively for violence images: {directory}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    """
    Main function to start monitoring the directory.
    """
    start_watchdog("./")

if __name__ == "__main__":
    main()