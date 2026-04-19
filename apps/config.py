# 앱은 개발 환경, 스테이징 환경, 라이브 환경 등 각각의 환경에서 설정해야 하는 config 값이 바뀐다.
# 그래서 app.py에 있는 config 값을 직접 기입하면 환경별로 소스코드를 바꿔 써야한다.

# 환경을 쉽게 변경할 수 있도록 config를 읽어 들이는 방법을 변경하겠다.
# 환경파일이 이곳 저곳에 펼처 있으면 관리도 힘들다.

# from_object, from_mapping, from_envvar, from_pyfile, from_file 등!
# 지금은 from_object를 사용하겠다.


from pathlib import Path

basedir = Path(__file__).parent.parent
# pathlib.Path는 경로를 객체로 지정할 때 사용한다.
# Path.resolve() : resolve 메소드는 파일이 존재하는 전체 full 디렉토리를 말한다. 절대적인 경로를 찾는다.
# .parent 메소드는 지금 파일이 있는 디렉토리 혹은 path로 지정한 경로보다 상위 디렉토리이다.
# Path('.').resolve().parent : 따라서 Path에서 지정한 '현재 디렉토리' 보다 상위 디렉토리를 가리킨다.
# Path 뒤에 /' ' 으로 경로를 직접 붙여서 입력할 수 있다.


# BaseConfig 클래스를 작성한다
class BaseConfig:
    SECRET_KEY = "12345678901234567890"
    WTF_CSRF_SECRET_KEY = "09876543210987654321"

    # 이미지 업로드용 경로 설정 apps/images를 지정 p207
    UPLOAD_FOLDER = str(Path(basedir, "apps", "images"))

    # 물체 감지에 이용하는 라벨 p222 추가
    LABELS = [
        "unlabeled",
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "street sign",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "hat",
        "backpack",
        "umbrella",
        "shoe",
        "eye glasses",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "plate",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "mirror",
        "dining table",
        "window",
        "desk",
        "toilet",
        "door",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "blender",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]


# BaseConfig 클래스를 상속하여 LocalConfig 클래스를 작성한다
class LocalConfig(
    BaseConfig
):  # BaseConfig 클래스를 상속하여 LocalConfig를 작성하고 config를 상속한다.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True


# BaseConfig 클래스를 상속하여 TestingConfig 클래스를 작성한다
class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    # testing 에선 CSRF를 무효하기 위해서 False로 설정


# config 사전에 매핑한다
config = {
    "testing": TestingConfig,
    "local": LocalConfig,
}

# 설정 후에 apps/app.py에 연결한다.