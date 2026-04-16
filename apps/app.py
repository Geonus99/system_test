from pathlib import Path
from apps.config import config
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config_key):
    # 플라스크 인스턴스 생성
    app = Flask(__name__)

    app.config.from_object(config[config_key])
    # 앱의 config 설정을 한다. 138p 제거
    # app.config.from_mapping(
    #     SECRET_KEY="flaskbooktest",
    #     SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
    #     SQLALCHEMY_TRACK_MODIFICATIONS=False,

    # # SQL을 콘솔 로그에 출력하는 설정
    #     SQLALCHEMY_ECHO=True,
    #     WTF_CSRF_SECRET_KEY="AuwzyszU5sugKN7KZs6f"
    # )

    csrf.init_app(app)
    # SQLAlchmey와 앱을 연계한다
    db.init_app(app)
    # Migrate와 앱을 연계한다
    Migrate(app, db)

    # 🚨 이 한 줄이 핵심입니다! 모델을 불러와야 Migrate가 인식해요.
    from apps.crud import models as crud_models

    from apps.crud import views as crud_views

    # register_blueprint를 사용해 views의 crud를 앱에 등록한다
    app.register_blueprint(crud_views.crud, url_prefix="/crud")

    return app