import eventlet
eventlet.monkey_patch()
from pathlib import Path
import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from flask_migrate import Migrate
from flask_socketio import SocketIO


# 확장 도구들 임포트 (기존 경로 유지)
from apps.config import config
from apps.extensions import db, csrf, login_manager, socketio 
from apps.detector.AiStreamService import AiStreamService
from apps.detector.WebcamService import WebcamService
from apps.detector.UsbCamService import UsbCamService

load_dotenv()

# 전역 변수 설정
_usbcam_task_started = False
_cam_tasks = {}

def create_app(config_key="local"):
    app = Flask(__name__)
    
    # 1. 설정 로드
    app.config.from_object(config[config_key])

    # 2. SocketIO 초기화 (중복 제거 및 eventlet 고정)
    # 반드시 가상환경에 pip install eventlet 이 되어 있어야 합니다.
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet', 
        logger=False,
        engineio_logger=False
    )

    # 3. 기타 확장 도구 초기화
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.signup"
    login_manager.login_message = ""

    # 4. 에러 핸들러
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    # 5. 블루프린트 등록
    from apps.crud import views as crud_views
    app.register_blueprint(crud_views.crud, url_prefix="/crud")
    from apps.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix="/auth")
    from apps.detector import views as dt_views
    app.register_blueprint(dt_views.dt)

    # 6. HTTP 라우트
    @app.route('/ai-detect/aistream')
    def ai_stream():
        return render_template('detector/ai_stream.html')

    @app.route('/ai-detect/apistream')
    def api_stream():
        return render_template('detector/api_stream.html')

    @app.route('/ai-detect/api/cctv/list')
    def cctv_list():
        from apps.detector.Apiservice import ITSApiService
        api_key = app.config.get("ITS_API_KEY", "")
        service = ITSApiService(api_key)
        try:
            cctvs = service.get_cctv_list(
                type=request.args.get("type", "ex"),
                min_x=float(request.args.get("min_x", 126.7)),
                min_y=float(request.args.get("min_y", 37.4)),
                max_x=float(request.args.get("max_x", 127.2)),
                max_y=float(request.args.get("max_y", 37.7))
            )
            return jsonify({"ok": True, "count": len(cctvs), "cctvs": cctvs})
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({"ok": False, "error": str(e)}), 500

    # 7. 소켓 이벤트 핸들러 (함수 내부에 작성하여 클로저로 socketio 접근)
    @socketio.on('connect')
    def handle_connect():
        print("[SYSTEM] Client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("[SYSTEM] Client disconnected")

    @socketio.on('set_detection_target')
    def handle_target(data):
        AiStreamService.set_target(data.get('target', ''))

    @socketio.on('webcam_frame')
    def handle_webcam_frame(data):
        result = WebcamService.predict_frame(data['image'])
        if result:
            socketio.emit('webcam_result', {'image': result})

    @socketio.on('start_rtsp')
    def handle_start_rtsp(data):
        cam_id = data.get('cam_id')
        if cam_id in _cam_tasks and _cam_tasks[cam_id]:
            return
        _cam_tasks[cam_id] = True
        rtsp_url = os.environ.get(f"RTSP_URL_{cam_id}")
        socketio.start_background_task(run_cam_logic, cam_id, rtsp_url)
        print(f"[SYSTEM] CAM {cam_id} 시작")

    @socketio.on('stop_rtsp')
    def handle_stop_rtsp(data):
        cam_id = data.get('cam_id')
        _cam_tasks[cam_id] = False
        AiStreamService.stop(cam_id)
        print(f"[SYSTEM] CAM {cam_id} 정지")

    @socketio.on('start_usbcam')
    def handle_start_usbcam():
        global _usbcam_task_started
        if not _usbcam_task_started:
            _usbcam_task_started = True
            socketio.start_background_task(UsbCamService.run_usbcam_stream, socketio)
            print("[SYSTEM] USB 웹캠 시작")

    @socketio.on('stop_usbcam')
    def handle_stop_usbcam():
        global _usbcam_task_started
        _usbcam_task_started = False
        UsbCamService.stop()
        print("[SYSTEM] USB 웹캠 정지")

    return app

def page_not_found(e):
    return render_template("404.html"), 404

def internal_server_error(e):
    return render_template("500.html"), 500

def run_cam_logic(cam_id, rtsp_url):
    # 주의: 여기서 socketio 객체를 사용해야 하므로 전역 socketio를 사용합니다.
    AiStreamService.run_rtsp_stream(socketio, cam_id, rtsp_url)