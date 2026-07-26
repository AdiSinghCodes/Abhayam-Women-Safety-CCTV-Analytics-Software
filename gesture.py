import time
import cv2
import mediapipe as mp
import cloudinary.uploader
import csv
from twilio.rest import Client
import os

class GestureProcessor:
    def __init__(self):
        # Initialize Mediapipe Hand Tracking
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Configure Cloudinary
        cloudinary.config(
            cloud_name="x9hvkwqw", 
            api_key="212353164148213", 
            api_secret="w0r7fzNt6zsRsdcfvihIifICCbA"
        )

    def send_whatsapp_alert(self, image_url):
        """Send a WhatsApp alert with the SOS image via Twilio"""
        account_sid = "ACb09fc5984472acf88bccc6e7009c7819"
        auth_token = "c29f51d881e980b17328f2a1661f3159"
        client = Client(account_sid, auth_token)

        from_whatsapp_number = "whatsapp:+14155238886"
        to_whatsapp_number = "whatsapp:+917304064579"

        try:
            message = client.messages.create(
                body="SOS Alert! Help required. See the attached image.",
                media_url=[image_url],
                from_=from_whatsapp_number,
                to=to_whatsapp_number
            )
            print(f"WhatsApp SOS alert sent with SID: {message.sid}")
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")

    def trigger_sos_alert(self, frame, location):
        """Save a screenshot, upload to Cloudinary, and send WhatsApp alert"""
        # Create location-based directories
        location_dir = f"{location}"
        gesture_subdir = os.path.join(location_dir, "gesture")
        os.makedirs(gesture_subdir, exist_ok=True)

        # Generate a unique filename using timestamp
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        local_path = os.path.join(gesture_subdir, f"sos_detected_{timestamp}.png")

        # Take a screenshot and save locally with the timestamp
        cv2.imwrite(local_path, frame)

        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(local_path)
            image_url = upload_result.get("secure_url")
            print(f"Image uploaded to Cloudinary: {image_url}")

            # Send WhatsApp alert
            self.send_whatsapp_alert(image_url)

            # Save the SOS gesture and location in a CSV file
            with open("sos_gestures.csv", mode="a", newline='') as file:
                writer = csv.writer(file)
                writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), location, image_url])
            print(f"SOS gesture details saved to CSV.")

        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")

    def sos_gesture_detection(self, hand_landmarks):
        """
        Detects an SOS gesture: closed fist with thumb alongside fingers
        Similar to the American Sign Language letter 'A'
        """
        # Extract landmarks for all finger tips
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        
        # Extract MCP joints (knuckles) for reference
        index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        middle_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        ring_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_MCP]
        pinky_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_MCP]
        
        # Wrist point
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # Check if fingers are curled into a fist
        # Fingers are curled when fingertips are closer to the wrist than their MCPs
        index_curled = index_tip.y > index_mcp.y
        middle_curled = middle_tip.y > middle_mcp.y
        ring_curled = ring_tip.y > ring_mcp.y
        pinky_curled = pinky_tip.y > pinky_mcp.y
        
        # All four fingers should be curled
        fingers_curled = index_curled and middle_curled and ring_curled and pinky_curled
        
        # Thumb should be visible and not tucked inside the fist
        # It should be positioned at the side of the hand
        thumb_visible = thumb_tip.x < index_mcp.x  # For right hand
        
        # Hand should be in vertical orientation (not perfectly horizontal)
        hand_vertical = abs(wrist.y - middle_mcp.y) > abs(wrist.x - middle_mcp.x) * 0.5
        
        # Detect the SOS gesture
        if fingers_curled and thumb_visible and hand_vertical:
            return True
        return False

    def process_frame_for_gesture(self, frame, gesture_start_time, gesture_count, is_open, SOS_THRESHOLD_COUNT, SOS_TIMEFRAME, location):
        """Process a frame for gesture detection."""
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        # Process hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # SOS gesture detection
                is_current_sos = self.sos_gesture_detection(hand_landmarks)
                
                # Visual feedback on current detection
                #detection_text = "SOS Detected!" if is_current_sos else "No SOS Detected"
                #detection_color = (0, 255, 0) if is_current_sos else (0, 0, 255)
                #cv2.putText(frame, detection_text, (10, 60), 
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, detection_color, 2)
                
                # Initialize gesture start time if not set
                if gesture_start_time is None:
                    gesture_start_time = time.time()
                
                # Track SOS gesture
                if is_current_sos and not is_open:
                    gesture_count += 1
                    is_open = True
                elif not is_current_sos and is_open:
                    is_open = False
                
                # Display count and time remaining
                cv2.putText(frame, f"Count: {gesture_count}/{SOS_THRESHOLD_COUNT}", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                time_remaining = max(0, SOS_TIMEFRAME - (time.time() - gesture_start_time))
                cv2.putText(frame, f"Time: {time_remaining:.1f}s", 
                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Handle SOS detection
                if time.time() - gesture_start_time > SOS_TIMEFRAME:
                    if gesture_count >= SOS_THRESHOLD_COUNT:
                        # Trigger the SOS alert
                        self.trigger_sos_alert(frame, location)
                    
                    # Reset tracking
                    gesture_start_time = None
                    gesture_count = 0
        else:
            # No hands detected
            cv2.putText(frame, "No hands detected", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame, gesture_start_time, gesture_count, is_open