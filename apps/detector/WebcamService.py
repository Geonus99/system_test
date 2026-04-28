import cv2
import torch
import base64
import numpy as np
from ultralytics import YOLO

class WebcamService:
    _model = None
    _device = 'cuda' if torch.cuda.is_available() else 'cpu'

    @classmethod
    def load_model(cls):
        if cls._model is None:
            cls._model = YOLO('yolov8n.pt')
            cls._model.to(cls._device)
            print(f"[WebcamService] 모델 로드 완료 (Device: {cls._device})")
        return cls._model

    @classmethod
    def predict_frame(cls, image_base64):
        """브라우저에서 받은 base64 프레임 → YOLO 추론 → base64 반환"""
        try:
            # base64 → numpy frame
            img_data = base64.b64decode(image_base64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                print("[WebcamService] 프레임 디코딩 실패")
                return None

            model = cls.load_model()
            results = model.predict(frame, device=cls._device, conf=0.5, verbose=False, imgsz=640)

            annotated_frame = results[0].plot()
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return base64.b64encode(buffer).decode('utf-8')

        except Exception as e:
            print(f"[WebcamService] 추론 에러: {e}")
            return None