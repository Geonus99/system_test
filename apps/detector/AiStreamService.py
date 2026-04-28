import cv2
import torch
import base64
import time
import os
from ultralytics import YOLO

class AiStreamService:
    _model = None
    _target_label = ""
    _device = 'cuda' if torch.cuda.is_available() else 'cpu'
    _running = {}  # {cam_id: True/False} 카메라별 독립 관리

    @classmethod
    def load_model(cls):
        if cls._model is None:
            cls._model = YOLO('yolov8n.pt')
            cls._model.to(cls._device)
            print(f"[INFO] AI Model Loaded on: {cls._device}")
        return cls._model

    @classmethod
    def set_target(cls, target):
        cls._target_label = target
        print(f"[INFO] 감시 타겟 변경: {target}")

    @classmethod
    def stop(cls, cam_id):
        cls._running[cam_id] = False
        print(f"[INFO] CAM {cam_id} 스트림 정지 요청")

    @classmethod
    def run_rtsp_stream(cls, socketio, cam_id, rtsp_url):
        cls._running[cam_id] = True
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"

        print(f"[INFO] CAM {cam_id} RTSP 연결 시도: {rtsp_url}")

        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print(f"[ERROR] CAM {cam_id} 연결 실패")
            socketio.emit('stream_error', {'cam_id': cam_id, 'message': f'CAM {cam_id} 연결 실패'})
            cls._running[cam_id] = False
            return

        model = cls.load_model()
        frame_count = 0
        print(f"[START] CAM {cam_id} 모니터링 시작")

        try:
            while cap.isOpened() and cls._running.get(cam_id, False):
                ret, frame = cap.read()
                if not ret:
                    socketio.sleep(0.1)
                    continue

                frame = cv2.resize(frame, (640, 480))
                frame_count += 1
                if frame_count % 3 != 0:
                    continue

                results = model.predict(frame, device=cls._device, conf=0.7, verbose=False, imgsz=640)
                boxes = results[0].boxes

                annotated_frame = results[0].plot()
                _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                encoded_image = base64.b64encode(buffer).decode('utf-8')

                socketio.emit('ai_frame', {
                    'cam_id': cam_id,
                    'image': encoded_image,
                })

                if cls._target_label:
                    detected_names = [model.names[int(i)].lower() for i in boxes.cls.tolist()]
                    if cls._target_label in detected_names:
                        socketio.emit('detection_alert', {
                            'cam_id': cam_id,
                            'label': cls._target_label,
                            'time': time.strftime('%H:%M:%S')
                        })

                socketio.sleep(0.01)

        except Exception as e:
            print(f"[CRITICAL] CAM {cam_id} 에러: {e}")
        finally:
            cap.release()
            cls._running[cam_id] = False
            print(f"[STOP] CAM {cam_id} 연결 종료")