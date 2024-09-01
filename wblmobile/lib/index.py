from flask import Flask, request, jsonify
import cv2
import os
from flask_cors import CORS
from ultralytics import YOLO
import shutil
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load YOLOv8 model
model = YOLO('best74.pt')

# Define a directory to save frames
FRAMES_DIR = r'..\assets'

# Define the rate of frame capture
FRAME_SKIP = 20

@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video_file = request.files['video']
    video_path = os.path.join('', video_file.filename)
    video_file.save(video_path)

    cap = cv2.VideoCapture(video_path)
    frames_without_helmet = []

    # Delete the directory if it already exists and recreate it
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)

    frame_number = 0
    captured_frame_number = 0  # To keep track of the actual frame number for saving
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Skip frames based on the FRAME_SKIP value
        if frame_number % FRAME_SKIP == 0:
            results = model(frame)

            # Check for frames where a helmet is not worn
            for result in results:
                for det in result.boxes:
                    if det.cls != 'No-Helmet':  
                        break
                else:
                    # Generate timestamp for the frame
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    # Save the frame without helmet to directory
                    frame_filename = f"frame_{timestamp}.jpg"
                    frame_path = os.path.join(FRAMES_DIR, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    frames_without_helmet.append(frame_filename)
                    captured_frame_number += 1
        
        frame_number += 1

    cap.release()
    os.remove(video_path)

    if not frames_without_helmet:
        return jsonify(["All helmets were worn"]), 200

    # Return list of frame filenames
    return jsonify(frames_without_helmet), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
