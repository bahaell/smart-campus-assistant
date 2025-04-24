from ultralytics import YOLO
import cv2
import numpy as np

class YOLOv5Detector:
    def __init__(self, model_path='yolov5s.pt'):
        """
        Initialize YOLO model for object detection.
        Args:
            model_path (str): Path to the YOLOv5 model (default: yolov5su.pt).
        """
        self.model = YOLO(model_path)  # Use ultralytics.YOLO

    def detect(self, image_path):
        """
        Detect objects in an image.
        Args:
            image_path (str): Path to the input image.
        Returns:
            list: List of dictionaries containing detected object labels and confidence scores.
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Perform detection
        results = self.model(img)
        
        # Extract labels and confidence scores
        detections = []
        for result in results:
            for box in result.boxes:
                label = self.model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                detections.append({"name": label, "confidence": conf})
        
        return detections

if __name__ == "__main__":
    detector = YOLOv5Detector()
    detections = detector.detect('Backend/lost-and-found/data/sample_item.jpg')
    print(detections)