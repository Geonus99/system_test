import cv2
import torch
import base64
from ultralytics import YOLO

class UsbCamService:
    _model = None
    _device = 'cuda' if torch.cuda.is_available() else 'cpu'
    _running = False

    @classmethod
    def load_model(cls):
        if cls._model is None:
            cls._model = YOLO('yolov8n.pt')
            cls._model.to(cls._device)
            print(f"[UsbCamService] 모델 로드 완료 (Device: {cls._device})")
        return cls._model

    @classmethod
    def stop(cls):
        cls._running = False
        print("[UsbCamService] USB 웹캠 정지 요청")

    @classmethod
    def run_usbcam_stream(cls, socketio, device_index=0):
        cls._running = True
        cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            print(f"[UsbCamService] /dev/video{device_index} 열기 실패")
            socketio.emit('usbcam_error', {'message': f'USB 웹캠 연결 실패 (video{device_index})'})
            cls._running = False
            return

        model = cls.load_model()
        frame_count = 0
        print(f"[UsbCamService] /dev/video{device_index} 스트리밍 시작")

        try:
            while cap.isOpened() and cls._running:
                ret, frame = cap.read()
                if not ret:
                    socketio.sleep(0.1)
                    continue

                frame = cv2.resize(frame, (640, 480))
                frame_count += 1
                if frame_count % 3 != 0:
                    continue

                results = model.predict(frame, device=cls._device, conf=0.5, verbose=False, imgsz=640)
                annotated_frame = results[0].plot()
                _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                encoded = base64.b64encode(buffer).decode('utf-8')

                socketio.emit('usbcam_result', {'image': encoded})
                socketio.sleep(0.01)

        except Exception as e:
            print(f"[UsbCamService] 에러: {e}")
        finally:
            cap.release()
            cls._running = False
            print(f"[UsbCamService] /dev/video{device_index} 종료")