# 🛡️ Abhayam - AI-Powered Women's Safety & Threat Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-green.svg)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Object%20Tracking-orange.svg)](https://docs.ultralytics.com/)
[![OpenAI CLIP](https://img.shields.io/badge/OpenAI%20CLIP-Zero--Shot%20Classification-purple.svg)](https://huggingface.co/docs/transformers/model_doc/clip)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-red.svg)](https://developers.google.com/mediapipe)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash%20Vision-yellow.svg)](https://ai.google.dev/)

**Abhayam** is an end-to-end, multi-threaded AI surveillance analytics software designed to detect physical violence against women, lone female presence in vulnerable areas, and distress emergency hand gestures in real time. 

The platform integrates computer vision, deep learning feature embeddings, generative multimodal AI, cloud storage, real-time audio alarms, and automated WhatsApp alert dispatching alongside a central Web Management Dashboard.

---

## 🌟 Key Features

* **🖐️ Emergency Hand SOS Gesture Detection:**
  Uses Google MediaPipe 3D Hand Tracking (21 3D joint landmarks) to detect distress hand gestures (folding 4 fingers into a fist with thumb exposed). Triggers an alert when repeated **3 times within 10 seconds**.

* **👩 Lone Female Safety & Threat Verification:**
  Monitors surveillance frames, counts human presence using **YOLOv5**, and double-checks gender using **Google Gemini 1.5 Flash AI** to identify women left alone in dangerous or isolated locations.

* **🚨 Physical Violence Against Women Detection:**
  Combines **YOLOv8** (real-time object tracking) with **OpenAI CLIP** (vision-language zero-shot action/gender classifier) to spot violent actions (hitting, slapping, punching, attacking). Triggers an **audible computer sound alarm (`winsound`)**, generates an AI scene description using Gemini, and dispatches immediate alerts.

* **📱 Automated Cloud & WhatsApp Emergency Alerts:**
  Automatically uploads incident evidence screenshots to **Cloudinary** and dispatches high-priority **WhatsApp text alerts with image links** via the **Twilio API** directly to authorities or personal emergency contacts.

* **📍 Crime Hotspot & Data Intelligence Analytics:**
  Aggregates logged incident data using **Pandas**, identifies high-threat locations with >5 recorded violence events, and exports spatial threat reports (`hotspot.csv`).

* **🖥️ Central Admin Web Dashboard:**
  Built with **Flask**, featuring secure user authentication, process control (starting/stopping AI detection threads), live video streaming, and data visualization using **Matplotlib** and **Seaborn**.

---

## 🏗️ System Architecture & Workflow

```
                               +-----------------------------+
                               |     Flask Admin Dashboard   |
                               |           (a.py)            |
                               +--------------+--------------+
                                              | (Start Processing)
                                              v
       +--------------------------------------+--------------------------------------+
       |                                      |                                      |
       v                                      v                                      v
+--------------+                       +--------------+                       +--------------+
|   main.py    |                       |one_female.py |                       |geminiLabel.py|
|(Screen Region|                       |(Lone Female  |                       |(Violence AI  |
| Surveillance)|                       | Verifier)    |                       | & Beep Alarm)|
+------+-------+                       +------+-------+                       +------+-------+
       |                                      |                                      |
       +--------------------------------------+--------------------------------------+
                                              |
                                              v
                              +-------------------------------+
                              | 1. Saved to Local Location Dir|
                              | 2. Uploaded to Cloudinary     |
                              | 3. Winsound Beep Played       |
                              | 4. Twilio WhatsApp Dispatched |
                              +-------------------------------+
```

---

## 📁 Repository Directory Structure

```text
├── a.py                         # Main Flask Web Application Server & Dashboard APIs
├── main.py                      # Multi-region screen surveillance controller & threading engine
├── violence_tracker.py          # Real-time YOLOv8 + OpenAI CLIP violence & action detector
├── gesture.py                   # MediaPipe hand tracking & SOS gesture recognition module
├── one_female.py                # Watchdog-based lone female verifier using YOLOv5 & Gemini AI
├── geminiLabel.py               # Watchdog scene explainer, audio alarm & Gemini 1.5 Flash verifier
├── region_manager.py            # Tkinter GUI for selecting screen monitoring coordinates
├── analysis.py                  # Data analytics script to filter crime hotspots (>5 incidents)
├── webcam_processing.py         # Utility script for testing local OpenCV webcam feed
├── 1.py                         # Standalone HTTP webcam streamer
├── regions.json                 # JSON configuration storing camera region coordinates & labels
├── credentials.csv              # Hashed admin user credentials for dashboard authentication
├── violence_log.csv             # CSV database logging raw violence & gender detection events
├── violence_detection_logs.csv  # CSV database logging Gemini AI scene descriptions
├── sos_gestures.csv             # CSV database logging detected emergency hand gestures
├── hotspot.csv                  # Filtered output of high-risk threat locations
├── yolov8n.pt                   # Pre-trained YOLOv8 Nano model weights
├── yolov5s.pt                   # Pre-trained YOLOv5 Small model weights
├── templates/                   # HTML template files for Flask dashboard
└── static/                      # Static assets (CSS, JS, upload images)
```

---

## ⚙️ Prerequisites & Installation

### 1. Requirements
* Python `3.10` or higher
* Operating System: Windows 10/11 (for `winsound` and `pyautogui`)
* Webcam or active screen display playing CCTV feeds

### 2. Install Required Dependencies
Run the following command in your terminal:

```bash
pip install flask opencv-python pyautogui numpy pandas matplotlib seaborn pillow torch torchvision ultralytics transformers google-generativeai cloudinary twilio watchdog
```

---

## 🔐 API Credentials Configuration

Ensure your API keys are configured in the respective script files:

1. **Google Gemini API Key:** Configure in `geminiLabel.py` and `one_female.py`:
   ```python
   genai.configure(api_key="YOUR_GEMINI_API_KEY")
   ```

2. **Cloudinary Configuration:** Configure in `gesture.py`, `one_female.py`, `violence_tracker.py`, and `geminiLabel.py`:
   ```python
   cloudinary.config(
       cloud_name="YOUR_CLOUD_NAME",
       api_key="YOUR_API_KEY",
       api_secret="YOUR_API_SECRET"
   )
   ```

3. **Twilio WhatsApp Configuration:** Configure in `gesture.py`, `one_female.py`, `violence_tracker.py`, and `geminiLabel.py`:
   ```python
   account_sid = "YOUR_TWILIO_ACCOUNT_SID"
   auth_token = "YOUR_TWILIO_AUTH_TOKEN"
   from_whatsapp_number = "whatsapp:+14155238886"
   to_whatsapp_number = "whatsapp:+YOUR_PHONE_NUMBER"
   ```

> ⚠️ **Note:** To receive WhatsApp Sandbox alerts from Twilio, send `join <your-sandbox-code>` to `+1 415 523 8886` from your recipient mobile phone once.

---

## 🚀 How to Run the Project (Step-by-Step)

### Step 1: Configure Screen Regions (First Time Setup)
Before running the main application, set your monitoring screen regions:
```bash
python region_manager.py
```
* Enter `1` (for full screen) or `4`/`9` (for camera grid splits).
* Type a location label (e.g., `block b`) and click **Submit**.
* Click **Save and Quit** to close the configuration window.

### Step 2: Start the Web Dashboard
Launch the Flask web application server:
```bash
python a.py
```

### Step 3: Open Dashboard & Start Live Monitoring
1. Open your web browser and go to: `http://127.0.0.1:5000/`
2. Log in with your admin credentials.
3. On the main dashboard, click the green **`[▶ Start Processing]`** button.
4. The system will launch background detection engines and open **2 live OpenCV sub-windows** (`Gesture Tracker` and `Violence Tracker`).

### Step 4: Stop Monitoring
Click the red **`[■ Stop Processing]`** button on the web dashboard to stop all background AI detection processes.

---

## 📊 Analytics & Reporting

* **Hotspot Analytics (`/hotspot-analytics`):** View high-risk crime hotspot locations and download the `hotspot.csv` report.
* **General Analytics (`/general-analytics`):** View real-time visual charts including incident counts over time, crime breakdowns per location, and gesture vs. violence metrics.

---

## 📧 Contact & Support

For queries, contributions, or research collaborations, reach out to:
* **Developer:** Aditya Pradeep Singh
* **Email:** [adityapsingh565@gmail.com](mailto:adityapsingh565@gmail.com)
* **GitHub:** [AdiSinghCodes](https://github.com/AdiSinghCodes)
