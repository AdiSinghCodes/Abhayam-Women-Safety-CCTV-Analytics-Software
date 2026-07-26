import cv2
import pyautogui
import json
from tkinter import Tk, Button, Label, Toplevel, Entry
import numpy as np

class RegionManager:
    def __init__(self):
        self.regions = []  # List to store regions
        self.region_locations = {}  # Dictionary to store region ID and location
        self.json_file = "regions.json"

        # Create the main tkinter window
        self.root = Tk()
        self.root.title("Region Manager")

        Label(self.root, text="Define Regions and Assign Locations").pack(pady=10)
        
        # Entry for number of regions
        Label(self.root, text="Enter number of regions (e.g., 4, 6, 9):").pack(pady=5)
        self.region_count_entry = Entry(self.root)
        self.region_count_entry.pack(pady=5)

        Button(self.root, text="Divide Screen", command=self.divide_screen_from_input).pack(pady=10)
        Button(self.root, text="Add Region Manually", command=self.add_region).pack(pady=10)
        Button(self.root, text="Save and Quit", command=self.save_and_quit).pack(pady=5)

    def divide_screen_from_input(self):
        """Divide the screen into specified number of regions based on user input and ask for location names."""
        num_regions_str = self.region_count_entry.get().strip()

        if not num_regions_str.isdigit():
            print("Please enter a valid number.")
            return

        num_regions = int(num_regions_str)
        screen_width, screen_height = pyautogui.size()

        regions = []
        region_width = screen_width // int(num_regions ** 0.5)
        region_height = screen_height // int(num_regions ** 0.5)

        for i in range(int(num_regions ** 0.5)):
            for j in range(int(num_regions ** 0.5)):
                start_x, start_y = i * region_width, j * region_height
                end_x, end_y = start_x + region_width, start_y + region_height
                region = (start_x, start_y, end_x - start_x, end_y - start_y)
                self.regions.append(region)
                region_id = len(self.regions)
                self.get_location_from_user(region_id)  # Ask for location name

        print(f"{num_regions} regions divided and locations requested.")

    def add_region(self):
        """Let the user manually select a region from the screen."""
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
    def get_location_from_user(self, region_id):
        """Prompt the user to enter a location for the region and ensure it waits before continuing."""
        top = Toplevel(self.root)
        top.title(f"Enter Location for Region {region_id}")

        Label(top, text=f"Enter location for Region {region_id}:").pack(padx=10, pady=10)
        location_entry = Entry(top)
        location_entry.pack(padx=10, pady=10)

        def on_submit():
            self.region_locations[region_id] = location_entry.get()
            top.destroy()  # Destroy the window after getting input

        Button(top, text="Submit", command=on_submit).pack(pady=5)

        self.root.wait_window(top)  # Wait until the window is closed **before continuing**



    def save_to_json(self):
        """Save regions and locations to a JSON file."""
        data = {
            "regions": {idx + 1: self.regions[idx] for idx in range(len(self.regions))},
            "locations": self.region_locations
        }
        with open(self.json_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Regions and locations saved to {self.json_file}")

    def save_and_quit(self):
        """Save data and exit the application."""
        self.save_to_json()
        self.root.quit()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = RegionManager()
    app.run()
