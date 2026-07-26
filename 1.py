from flask import Flask, Response, render_template
import cv2

app = Flask(__name__)

# Initialize the webcam
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    # Render a basic webpage
    return """
    <!doctype html>
    <title>Webcam Stream</title>
    <h1>Live Webcam Stream</h1>
    <img src="/video_feed">
    """

@app.route('/video_feed')
def video_feed():
    # Serve the video stream
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)