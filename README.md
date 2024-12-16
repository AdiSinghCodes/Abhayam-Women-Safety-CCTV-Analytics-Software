# Abhayam: Women Safety CCTV Analytics Software

Abhayam is an advanced software solution designed to analyze CCTV footage for enhancing women's safety. The software combines cutting-edge computer vision techniques to detect gestures, monitor violence, and manage screen regions effectively.

## Features

- Detect and classify gestures in real-time.
- Monitor and identify potential acts of violence.
- Manage and process multiple screen regions for enhanced surveillance.
- Easy-to-use interface for region configuration and analysis.

## Prerequisites

Before running the application, ensure that the following libraries and dependencies are installed:

### Python Libraries

- `torch`
- `opencv-python`
- `numpy`
- `Pillow`
- `pyautogui`
- `json`
- `tkinter`
- `streamlit`

### Installation

You can install all required libraries using the following command:

```bash
pip install torch opencv-python numpy Pillow pyautogui streamlit
```

## Setup

1. Clone this repository to your local machine.
2. Ensure all required libraries are installed.
3. Run the application using the following command:

```bash
streamlit run app.py
```

## File Descriptions

### 1. `app.py`
This is the main entry point for the application. It provides a Streamlit-based interface to interact with all the features of Abhayam.

### 2. `one_female.py`
This script:
- Detects people using YOLOv5.
- Classifies the gender of individuals in images using the CLIP model.
- Deletes images containing more than one female in specified folders.

### 3. `region_manager.py`
This script:
- Allows users to configure screen regions for monitoring.
- Saves region configurations in a JSON file.

### 4. `main.py`
This script:
- Processes screen regions for gesture detection and violence monitoring.
- Displays analyzed frames in real-time using OpenCV.

## How to Use

1. **Configure Regions**:
   - Run `region_manager.py` to divide and manage screen regions.
   - Save your configurations.

2. **Analyze Screen Regions**:
   - Run `main.py` to start monitoring and analyzing the configured regions.

3. **Delete Images with Multiple Females**:
   - Run `one_female.py` to clean up folders by removing images with more than one female detected.

4. **Run the App**:
   - Launch the main application using `streamlit run app.py`.

## Notes

- Ensure that your system supports the required hardware and software configurations.
- The application leverages GPU acceleration (if available) for faster processing.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- YOLOv5 for object detection.
- OpenAI's CLIP for advanced image and text processing.

---

For any issues or contributions, feel free to open an issue or submit a pull request.

