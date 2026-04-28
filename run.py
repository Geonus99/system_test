from apps.app import create_app, socketio # create_app 위치에 맞게 수정

app = create_app("local")

if __name__ == '__main__':
    # host='0.0.0.0'을 해야 WSL 밖에서 접속이 가능합니다.
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)