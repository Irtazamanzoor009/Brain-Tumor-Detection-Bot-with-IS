import cv2
from ultralytics import YOLO
import os

model = YOLO("combest.pt")  # path to your .pt file

def detect_tumors(image_path):
    results = model.predict(source=image_path, save=False)
    tumor_info = []
    tumor_count = 0
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            label = int(box.cls[0])
            if label == 0:
                tumor_count += 1
                tumor_info.append({"confidence": confidence, "box": [x1, y1, x2, y2]})
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(img, f"Tumor: {confidence:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

    # result_path = f"annotated_{os.path.basename(image_path)}"
    # cv2.imwrite(result_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

     # Define annotated folder
    annotated_folder = "annotated"
    os.makedirs(annotated_folder, exist_ok=True)

    # Save the annotated image in the annotated folder
    result_filename = f"annotated_{os.path.basename(image_path)}"
    result_path = os.path.join(annotated_folder, result_filename)
    cv2.imwrite(result_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return result_path, tumor_info, tumor_count
