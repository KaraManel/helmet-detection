from flask import Flask, render_template, request
import os
from ultralytics import YOLO
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the YOLO model
model = YOLO("best.pt")


def process_video(file_path):
    cap = cv2.VideoCapture(file_path)
    frame_count = 0
    timestamps = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()  # Extract bounding boxes
            classes = result.boxes.cls.cpu().numpy()  # Extract classes
            for box, cls in zip(boxes, classes):
                if cls == 0:  # Class 'head' (no helmet)
                    timestamps.append(frame_count / frame_rate)

        frame_count += 1

    cap.release()

    # Aggregate timestamps into intervals
    if timestamps:
        intervals = []
        start_time = timestamps[0]
        end_time = timestamps[0]

        for time in timestamps[1:]:
            if time - end_time <= 0.5:  # If the next timestamp is within 0.5 seconds
                end_time = time
            else:
                intervals.append((start_time, end_time))
                start_time = time
                end_time = time

        # Add the last interval
        intervals.append((start_time, end_time))

        return intervals
    else:
        return []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        intervals = process_video(file_path)
        return render_template("index.html", intervals=intervals)


if __name__ == "__main__":
    app.run()
