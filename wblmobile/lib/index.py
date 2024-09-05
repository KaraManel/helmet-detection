import os
import cv2
import torch
from flask import Flask, request, jsonify
from ultralytics import YOLO
import base64
import tempfile
import numpy as np
from io import BytesIO

app = Flask(__name__)

# Load  trained YOLO model
model_path = 'best74.pt'  
model = YOLO(model_path)

# Define the No-helmet class label to detect
target_class = "No-Helmet"

# Get the index of the target class from the model.names dictionary
target_class_index = None
for key, value in model.names.items():
    if value == target_class:
        target_class_index = key
        break

if target_class_index is None:
    raise ValueError(f"Class '{target_class}' not found in model.names")

def frame_to_base64(frame):
    """Convert a video frame (image) to base64-encoded string."""
    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

@app.route('/process_video', methods=['POST'])
def process_video():
    # Check if the POST request has the file part
    if 'video' not in request.files:
        return "No video file provided.", 400

    video_file = request.files['video']
     # Create a temporary file to save the video
    input_video_path = tempfile.mktemp(suffix='.mp4') 
    video_file.save(input_video_path)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        return "Error: Could not open video file.", 400
    
    # List to store base64-encoded screenshots
    screenshots_base64 = []  
    frame_count = 0  # To keep track of frame numbers

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Perform object detection
        results = model(frame)

        # Process results
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            labels = result.boxes.cls.cpu().numpy()

            for box, score, label in zip(boxes, scores, labels):
                if int(label) == target_class_index and score > 0.5:  # "No-Helmet" detected
                    x1, y1, x2, y2 = map(int, box)

                    # Draw bounding box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f'{target_class} {score:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                    # Convert the frame to base64 and store it
                    screenshot_base64 = frame_to_base64(frame)
                    screenshots_base64.append(screenshot_base64)

    cap.release()

    if not screenshots_base64:
        return jsonify( ["All helmets were worn"]), 200

    # Return list of base64-encoded screenshots as JSON
    return jsonify(screenshots_base64), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

