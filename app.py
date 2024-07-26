from flask import Flask, render_template, request, url_for
import os
from ultralytics import YOLO
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
SNAPSHOT_FOLDER = "static/snapshots"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

# Load the YOLO model
model = YOLO("best.pt")


def process_video(file_path):
    cap = cv2.VideoCapture(file_path)
    frame_count = 0
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    first_detection = None

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
                    timestamp = frame_count / frame_rate
                    if first_detection is None:
                        first_detection = (frame, timestamp)
                        break
            if first_detection:
                break

        frame_count += 1
        if first_detection:
            break

    cap.release()

    if first_detection:
        frame, timestamp = first_detection
        snapshot_filename = f"{os.path.basename(file_path)}.jpg"
        snapshot_path = os.path.join(SNAPSHOT_FOLDER, snapshot_filename)
        cv2.imwrite(snapshot_path, frame)
        return snapshot_filename, timestamp
    else:
        return None, None


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
        snapshot_filename, timestamp = process_video(file_path)
        if snapshot_filename:
            snapshot_url = url_for("static", filename=f"snapshots/{snapshot_filename}")
            return render_template(
                "index.html", snapshot_url=snapshot_url, timestamp=timestamp
            )
        else:
            return render_template(
                "index.html", message="No head detected in the video."
            )


if __name__ == "__main__":
    app.run()
