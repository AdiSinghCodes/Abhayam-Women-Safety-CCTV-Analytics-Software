import cv2
import pyautogui
import numpy as np
from tkinter import Tk, Button, Label, Toplevel, Entry
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import gesture
import violence_tracker
import queue

class RegionSelectorApp:
    def __init__(self):
        self.regions = []  # List to store regions
        self.region_locations = {}  # Dictionary to store region id and location
        self.running = False

        # Load YOLO model once outside the loop
        self.yolo_model_path = "yolov8n.pt"
        self.tracker = violence_tracker.ViolenceTracker(yolo_model_path=self.yolo_model_path)

        # ThreadPoolExecutor to manage concurrent threads
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Queue for frame passing
        self.frame_queue = queue.Queue(maxsize=20)  # Adjusted maxsize for smoother processing

        # Create the main tkinter window
        self.root = Tk()
        self.root.title("Region Selector")

        # Make the tkinter window always stay on top
        self.root.attributes('-topmost', 1)

        # Add widgets
        Label(self.root, text="Select regions for processing").pack(pady=10)
        Button(self.root, text="Add Region", command=self.add_region).pack(pady=5)
        Button(self.root, text="Start Processing", command=self.start_processing).pack(pady=5)
        Button(self.root, text="Quit", command=self.quit_app).pack(pady=5)

    def add_region(self):
        """Let the user select a region from the screen."""
        print("Select a region by dragging your mouse...")
        selected_region = self.select_region()
        if selected_region:
            region_id = len(self.regions) + 1
            self.regions.append(selected_region)
            print(f"Region {region_id} added: {selected_region}")
            self.get_location_from_user(region_id)
        else:
            print("No region selected.")

    def select_region(self):
        """Capture the screen and let the user drag to select a region."""
        frame = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        temp_frame = frame.copy()
        start_x, start_y, end_x, end_y = -1, -1, -1, -1
        region_selected = False

        def mouse_callback(event, x, y, flags, param):
            nonlocal start_x, start_y, end_x, end_y, region_selected, temp_frame
            if event == cv2.EVENT_LBUTTONDOWN:
                start_x, start_y = x, y
            elif event == cv2.EVENT_MOUSEMOVE and start_x != -1 and start_y != -1:
                temp_frame = frame.copy()
                cv2.rectangle(temp_frame, (start_x, start_y), (x, y), (0, 255, 0), 2)
                cv2.imshow("Select Region", temp_frame)
            elif event == cv2.EVENT_LBUTTONUP:
                end_x, end_y = x, y
                region_selected = True

        cv2.imshow("Select Region", frame)
        cv2.setMouseCallback("Select Region", mouse_callback)

        while not region_selected:
            cv2.imshow("Select Region", temp_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
        if start_x != -1 and start_y != -1 and end_x != -1 and end_y != -1:
            return start_x, start_y, end_x - start_x, end_y - start_y
        return None

    def normalize_region(self, region):
        """Normalize the selected region."""
        x1, y1, width, height = region
        x_start = min(x1, x1 + width)
        y_start = min(y1, y1 + height)
        return x_start, y_start, abs(width), abs(height)

    def capture_screen(self, region):
        """Capture a screenshot of the specified region."""
        x, y, width, height = self.normalize_region(region)
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return np.array(screenshot)

    def process_region_gesture(self, region, region_id, location):
        """Process a single region for gesture detection."""
        gesture_start_time = None
        gesture_count = 0
        is_open = False
        SOS_THRESHOLD_COUNT = 3
        SOS_TIMEFRAME = 10

        while self.running:
            frame = self.capture_screen(region)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = cv2.resize(frame, (640, 480))  # Resize for faster processing

            frame, gesture_start_time, gesture_count, is_open = gesture.process_frame_for_gesture(
                frame, gesture_start_time, gesture_count, is_open, SOS_THRESHOLD_COUNT, SOS_TIMEFRAME, location
            )

            try:
                self.frame_queue.put((f"Gesture Tracker - Region {region_id} - {location}", frame), timeout=0.1)
            except queue.Full:
                pass  # Ignore if the queue is full

    def process_region_violence(self, region, region_id, location):
        """Process a single region for violence detection."""
        while self.running:
            frame = self.capture_screen(region)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            processed_frame = self.tracker.process_frame(frame, location)

            processed_frame = cv2.resize(processed_frame, (640, 480))  # Resize for efficiency

            try:
                self.frame_queue.put((f"Violence Tracker - Region {region_id} - {location}", processed_frame), timeout=0.1)
            except queue.Full:
                pass  # Ignore if the queue is full

    def display_frames(self):
        """Display frames from the queue."""
        while self.running:
            try:
                window_name, frame = self.frame_queue.get(timeout=0.1)
                cv2.imshow(window_name, frame)
            except queue.Empty:
                continue

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break

    def get_location_from_user(self, region_id):
        """Prompt the user to enter a location for the region."""
        top = Toplevel(self.root)
        top.title(f"Enter Location for Region {region_id}")

        Label(top, text="Enter location:").pack(padx=10, pady=10)
        location_entry = Entry(top)
        location_entry.pack(padx=10, pady=10)

        def on_submit():
            self.region_locations[region_id] = location_entry.get()
            top.destroy()

        Button(top, text="Submit", command=on_submit).pack(pady=5)

    def start_processing(self):
        """Start processing all selected regions."""
        if not self.regions:
            print("No regions selected. Add a region first!")
            return

        self.running = True
        for i, region in enumerate(self.regions):
            region_id = i + 1
            location = self.region_locations.get(region_id, "Unknown")
            self.executor.submit(self.process_region_gesture, region, region_id, location)
            self.executor.submit(self.process_region_violence, region, region_id, location)

        self.display_frames()

    def quit_app(self):
        """Clean up and exit the application."""
        self.running = False
        self.executor.shutdown(wait=True)
        self.root.quit()
        cv2.destroyAllWindows()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = RegionSelectorApp()
    app.run()
