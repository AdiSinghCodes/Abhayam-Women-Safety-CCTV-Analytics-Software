import streamlit as st
import subprocess
import os
import signal
import psutil
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium

# Constants
CREDENTIALS_FILE = "credentials.csv"

# Helper Functions
def verify_credentials(username, password):
    """Verify credentials."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username and row[1] == password:
                    return True
    return False


def save_credentials(username, password):
    """Save credentials."""
    if not credentials_exist(username):
        with open(CREDENTIALS_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([username, password])
        return True
    return False


def credentials_exist(username):
    """Check if username exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    return True
    return False


def start_processing():
    """Start main.py for processing."""
    try:
        process = subprocess.Popen(["python", "main.py"])
        st.session_state["main_process"] = process
        st.success("Processing started successfully.")
    except Exception as e:
        st.error(f"Error starting main.py: {e}")


def stop_processing():
    """Stop main.py and all associated processes."""
    if "main_process" in st.session_state and st.session_state["main_process"]:
        try:
            # Terminate the specific `main.py` process
            st.session_state["main_process"].terminate()
            st.session_state["main_process"] = None

            # Close other Python processes related to gesture and violence detection
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if proc.info["name"] == "python" and any(
                    "gesture" in cmd or "violence" in cmd for cmd in proc.info["cmdline"]
                ):
                    os.kill(proc.info["pid"], signal.SIGTERM)

            st.success("Processing and associated processes stopped.")
        except Exception as e:
            st.error(f"Error stopping processing: {e}")

# Function to add a back arrow to navigate to previous page
def back_arrow():
    if st.button("← Back", key="back"):
        # Reset the location and subfolder selections when the back button is clicked
        st.session_state.selected_location = None
        st.session_state.selected_subfolder = None
        st.session_state["one_female_ran"] = False # Optional: Reset the state of "one_female_ran"
        st.rerun()

def display_detected_images():
    st.title("Detected Images")
    
    # Back arrow for navigation
    back_arrow()

    # Run one_female.py and geminLabel.py only when "Detected Images" is selected and "one_female_ran" is not set
    if "one_female_ran" not in st.session_state or not st.session_state["one_female_ran"]:
        with st.spinner("Running detection scripts..."):
            try:
                # Run both scripts concurrently
                one_female_process = subprocess.Popen(["python", "one_female.py"])
                geminiLabel_process = subprocess.Popen(["python", "geminiLabel.py"])

                # Wait for both processes to finish
                one_female_process.wait()
                geminiLabel_process.wait()

                # Mark one_female.py as ran
                st.session_state["one_female_ran"] = True
                st.success("Detection completed successfully.")
            except Exception as e:
                st.error(f"Error running detection scripts: {e}")
                return

    # Display folders once the script has completed
    if "selected_location" not in st.session_state or st.session_state["selected_location"] is None:
        folders = [f for f in os.listdir() if os.path.isdir(f) and f != "__pycache__" and f != ".streamlit"]
        if folders:
            for folder in folders:
                if st.button(folder):
                    st.session_state["selected_location"] = folder
                    st.rerun()  # Rerun to show subfolders
        else:
            st.warning("No detected images found.")
    elif "selected_subfolder" not in st.session_state or st.session_state["selected_subfolder"] is None:
        location = st.session_state["selected_location"]
        subfolders = ["one_female", "violence_against_women", "gesture"]  # Customize as per your folder structure
        for subfolder in subfolders:
            if st.button(subfolder):
                st.session_state["selected_subfolder"] = subfolder
                st.rerun()  # Rerun to display images
    else:
        location = st.session_state["selected_location"]
        subfolder = st.session_state["selected_subfolder"]
        folder_path = os.path.join(location, subfolder)

        # Check if the subfolder exists before trying to display images
        if not os.path.exists(folder_path):
            st.warning(f"Subfolder '{subfolder}' does not exist under {location}.")
            return
        
        images = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        # Display images or a message if no images are found
        if images:
            for img in images:
                img_path = os.path.join(folder_path, img)
                st.image(img_path, caption=img, use_container_width=True)
        else:
            st.warning(f"No images found in {subfolder} under {location}.")


# Hotspot Analytics Section
def hotspot_analytics():
    """Display and download hotspot analytics."""
    st.title("Hotspot Analytics")

    # Check if the CSV file exists
    file_path = "hotspot.csv"
    if os.path.exists(file_path):
        # Load CSV data
        df = pd.read_csv(file_path)

        # Display data in tabular form
        st.subheader("Hotspot Data")
        st.dataframe(df, use_container_width=True)

        # Download button for the CSV file
        st.download_button(
            label="Download Hotspot CSV",
            data=df.to_csv(index=False),
            file_name="hotspot.csv",
            mime="text/csv",
        )
    else:
        st.error("Hotspot CSV file not found.")

def general_analytics(violence_log_path, sos_gestures_path): 
    # Load datasets
    violence_data = pd.read_csv(violence_log_path, parse_dates=['Timestamp'])
    sos_columns = ['Timestamp', 'Location', 'Image_URL']
    sos_data = pd.read_csv(sos_gestures_path, header=None, names=sos_columns, parse_dates=['Timestamp'])

    sns.set(style="whitegrid")

    # Create columns for 3x3 grid
    col1, col2, col3 = st.columns(3)

    # 1. Incidents Over Time
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        incident_counts = violence_data.groupby(['Timestamp']).size()
        incident_counts.plot(kind='line', ax=ax, title="Incidents Over Time", xlabel="Time", ylabel="Incident Count")
        st.pyplot(fig)

    # 2. Location-Based Analysis
    with col2:
        fig, ax = plt.subplots(figsize=(8, 6))
        location_counts = violence_data['Location'].value_counts()
        location_counts.plot(kind='bar', ax=ax, title="Incidents Per Location", xlabel="Location", ylabel="Incident Count")
        st.pyplot(fig)

    # 3. Gender Count Per Incident Type
    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        gender_incidents = violence_data.groupby(['Action Detected']).agg(
            male_count=('Male Count', 'sum'),
            female_count=('Female Count', 'sum')
        )
        gender_incidents.plot(kind='bar', stacked=True, ax=ax, title="Gender Count Per Incident Type", xlabel="Incident Type", ylabel="Count")
        st.pyplot(fig)

    # 4. Hourly Patterns
    col1, col2, col3 = st.columns(3)
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        violence_data['Hour'] = violence_data['Timestamp'].dt.hour
        hourly_incidents = violence_data.groupby('Hour').size()
        sns.heatmap(hourly_incidents.values.reshape(1, -1), annot=True, cmap="coolwarm", xticklabels=hourly_incidents.index, ax=ax)
        plt.title("Hourly Incident Frequency")
        st.pyplot(fig)

    # 5. SOS Alerts Over Time
    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sos_counts = sos_data.groupby(['Timestamp']).size()
        sos_counts.plot(kind='line', ax=ax, title="SOS Alerts Over Time", xlabel="Time", ylabel="SOS Alert Count")
        st.pyplot(fig)

    # 6. Location-Based SOS Alerts
    with col3:
        fig, ax = plt.subplots(figsize=(8, 6))
        sos_location_counts = sos_data['Location'].value_counts()
        sos_location_counts.plot(kind='bar', ax=ax, title="SOS Alerts Per Location", xlabel="Location", ylabel="SOS Alert Count")
        st.pyplot(fig)

    # 7. Hourly SOS Trends
    col1, col2, col3 = st.columns(3)
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sos_data['Hour'] = sos_data['Timestamp'].dt.hour
        hourly_sos = sos_data.groupby('Hour').size()
        sns.heatmap(hourly_sos.values.reshape(1, -1), annot=True, cmap="coolwarm", xticklabels=hourly_sos.index, ax=ax)
        plt.title("Hourly SOS Alert Frequency")
        st.pyplot(fig)

    # 8. SOS Alert Image Insights
    with col2:
        top_location = sos_location_counts.idxmax()
        top_location_sos = sos_data[sos_data['Location'] == top_location]
        st.write(f"Sample images for the top location ({top_location}):")
        st.write(top_location_sos['Image_URL'].head())

    # 9. Correlation Between SOS Alerts and Incidents
    with col3:
        fig, ax = plt.subplots(figsize=(10, 6))
        merged_data = pd.merge(violence_data, sos_data, on="Location", how="inner")
        incident_sos_counts = merged_data.groupby(['Timestamp_x']).size()
        incident_sos_counts.plot(kind='line', ax=ax, title="Correlation Between SOS Alerts and Incidents", xlabel="Time", ylabel="Count")
        st.pyplot(fig)

# Streamlit App
st.set_page_config(page_title="CCTV Monitoring", layout="wide")
st.markdown("""
    <style>
        .logo {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
    </style>
""", unsafe_allow_html=True)

# Make sure to use correct file path or URL for the logo
st.image("abhayamWhite.png", width=100)
st.title("Abhayam: Empowering Safety, Protecting Women.")

# Custom CSS for buttons and icons (Font Awesome icons used here)
st.markdown("""
    <style>
        .sidebar-button {
            display: block;
            padding: 10px;
            margin: 10px 0;
            background-color: #0073e6;
            color: white;
            border: none;
            border-radius: 5px;
            text-align: center;
            font-size: 16px;
            font-weight: bold;
        }
        .sidebar-button:hover {
            background-color: #005bb5;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar buttons with Font Awesome icons
st.sidebar.title("Navigation")

# Initialize `nav_option`
if "nav_option" not in st.session_state:
    st.session_state["nav_option"] = None

if st.sidebar.button("Login", key="login", help="Login to the system", use_container_width=True):
    st.session_state["nav_option"] = "Login"
elif st.sidebar.button("Signup", key="signup", help="Sign up for a new account", use_container_width=True):
    st.session_state["nav_option"] = "Signup"
elif st.sidebar.button("About Us", key="about_us", help="Learn more about us", use_container_width=True):
    st.session_state["nav_option"] = "About Us"
elif st.sidebar.button("Main Menu", key="main_menu", help="Go to main menu", use_container_width=True):
    st.session_state["nav_option"] = "Main Menu"
elif st.sidebar.button("Detected Images", key="detected_images", help="View detected images", use_container_width=True):
    st.session_state["nav_option"] = "Detected Images"
if st.sidebar.button("Hotspot Analytics", key="hotspot_analytics", help="View hotspot analytics", use_container_width=True):
    st.session_state["nav_option"] = "Hotspot Analytics"
if st.sidebar.button("General Analytics", key="general_analytics", help="View general analytics", use_container_width=True):
    st.session_state["nav_option"] = "General Analytics"



# Initialize session state for login status if it doesn't exist
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

nav_option = st.session_state["nav_option"]

if nav_option == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_credentials(username, password):
            st.success("Login successful!")
            st.session_state["logged_in"] = True  # Set the login state
        else:
            st.error("Invalid username or password.")

elif nav_option == "Signup":
    st.subheader("Signup")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    if st.button("Signup"):
        if save_credentials(username, password):
            st.success("Signup successful!")
        else:
            st.error("Username already exists.")

elif nav_option == "About Us":
    st.title("About Us")
    st.subheader("Our Mission")
    st.write("Abhayam is a cutting-edge women safety analytics solution designed to enhance public safety by leveraging real-time surveillance and advanced analytical techniques. Our mission is to create safer environments for women and empower law enforcement agencies to act proactively in preventing crimes. Through Abhayam, we provide continuous monitoring and gender classification, ensuring that potential threats such as lone women at night, unusual gestures, or women surrounded by men are detected before escalation. By analyzing gender distribution, recognizing SOS gestures, and identifying hotspots, Abhayam offers valuable insights to help safeguard women in urban areas. Our system plays a crucial role in fostering a secure atmosphere and contributing to strategic safety planning, aiming to reduce crime and improve the safety of women everywhere.")
    st.subheader("Our Team")
    st.write("Our team consists of passionate developers dedicated to using AI for public safety.")
    st.subheader("Contact Us")
    st.write("You can reach us at eshanikaamballa@gmail.com")

elif nav_option == "Main Menu":
    if st.session_state["logged_in"]:
        st.subheader("Main Menu")

        # Start Processing Button
        if st.button("Start Processing"):
            start_processing()

        # Stop Processing Button
        if st.button("Stop Processing"):
            stop_processing()

    else:
        st.error("Please log in to access this section.")

elif nav_option == "Detected Images":
    if st.session_state["logged_in"]:
        display_detected_images()
    else:
        st.error("Please log in to access this section.")

elif nav_option == "Hotspot Analytics":
    if st.session_state["logged_in"]:
        hotspot_analytics()
    else:
        st.error("Please log in to access this section.")

elif nav_option == "General Analytics":
    if st.session_state["logged_in"]:
        general_analytics('violence_log.csv','sos_gestures.csv')
    else:
        st.error("Please log in to access this section.")


