import random  # p227 추가
import uuid  # 파일명 랜덤 처리용
from pathlib import Path  # 파일 경로 처리용

import cv2  # p227 추가
import numpy as np  # p227 추가
import torch  # p227 추가
import torchvision  # p227 추가

# redirect url_for p211 추가
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required  # p211 추가(로그인 인증처리용)
from PIL import Image  # p227 추가
from sqlalchemy.exc import SQLAlchemyError  # p227추가

from apps.app import db  # p185 추가
from apps.crud.models import User  # p185 추가

# UploadImageForm을 import 한다
from apps.detector.forms import UploadImageForm  # p211 추가 업로드 이미지 객체
from apps.detector.forms import DeleteForm, DetectorForm  # / p235 추가 / p229 추가

#                                 p185            p227
from apps.detector.models import UserImage, UserImageTag

# template_folder를 지정한다(static은 지정하지 않는다)
dt = Blueprint("detector", __name__, template_folder="templates")
# Blueprint의 static 앤드포인트의 Rule은 /<url prefix>/<static folder name>이 되는데
# dectect 앱의 경우 url_prefix를 지정하지 않았음으로 /<static folder name>이 됨


# dt 애플리케이션을 사용하여 엔드포인트를 작성한다
@dt.route("/")
def index():

    # User와 UserImage를 Join하여 이미지 일람을 취득한다 p185 추가
    user_images = (
        db.session.query(User, UserImage)
        .join(UserImage)
        .filter(User.id == UserImage.user_id)
        .all()
    )

    # p229 추가 태그 리스트를 가져온다.
    user_image_tag_dict = {}
    for user_image in user_images:
        # 이미지에 연결된 태그 일람을 취득한다
        user_image_tags = (
            db.session.query(UserImageTag)
            .filter(UserImageTag.user_image_id == user_image.UserImage.id)
            .all()
        )
        user_image_tag_dict[user_image.UserImage.id] = user_image_tags

    # 물체 탐지 폼을 인스턴스화한다
    detector_form = DetectorForm()

    # DeleteForm을 인스턴스화한다 p236 추가
    delete_form = DeleteForm()

    return render_template(
        "detector/index.html",
        user_images=user_images,
        # 태그 일람을 템플릿에 건넨다
        user_image_tag_dict=user_image_tag_dict,
        # 물체 검지 폼을 템플릿에 건넨다
        detector_form=detector_form,
        # 이미지 삭제 폼을 템플릿에 건넨다 p236추가
        delete_form=delete_form,
    )

    # return render_template("detector/index.html", user_images=user_images)
    #                                                   p185 추가
    # 지금부터는 부트스트랩을 사용하여 디자인 하겠다.
    #


@dt.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    # send_from_directory 함수에 config.py에 있는 폴더 위치와 파일명을 리턴한다.
    # images 폴더에 사진을 넣고 호출 해보자.
    # http://localhost:5000/images/파일명
    # http://localhost:5000/images/파일명


# p212 추가
@dt.route("/upload", methods=["GET", "POST"])
# 로그인 필수로 한다
@login_required
def upload_image():
    # UploadImageForm을 이용해서 밸리데이션을 한다
    form = UploadImageForm()
    if form.validate_on_submit():
        # 업로드된 이미지 파일을 취득한다
        file = form.image.data  # html <input type=filename=image>

        # 파일의 파일명과 확장자를 취득하고, 파일명을 uuid로 변환한다
        ext = Path(file.filename).suffix
        image_uuid_file_name = (
            str(uuid.uuid4()) + ext
        )  # 파일명 중복등의 이유로 변환함.(보안성)

        # 이미지를 보존한다 apps/images
        image_path = Path(current_app.config["UPLOAD_FOLDER"], image_uuid_file_name)
        file.save(image_path)

        # DB에 보존한다
        user_image = UserImage(user_id=current_user.id, image_path=image_uuid_file_name)
        db.session.add(user_image)
        db.session.commit()

        return redirect(url_for("detector.index"))
    return render_template("detector/upload.html", form=form)


# p223 추가
# 이미지 물체에 테두리를 그리는 함수등을 구현한다.
def make_color(labels):
    # 테두리 선의 색을 랜덤으로 결정
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in labels]
    color = random.choice(colors)
    return color


def make_line(result_image):
    # 테두리 선을 작성
    line = round(0.002 * max(result_image.shape[0:2])) + 1
    return line


def draw_lines(c1, c2, result_image, line, color):
    # 사각형의 테두리 선을 이미지에 덧붙여 씀
    cv2.rectangle(result_image, c1, c2, color, thickness=line)
    return cv2


def draw_texts(result_image, line, c1, cv2, color, labels, label):
    # 감지한 텍스트 라벨을 이미지에 덧붙여 씀
    display_txt = f"{labels[label]}"
    font = max(line - 1, 1)
    t_size = cv2.getTextSize(display_txt, 0, fontScale=line / 3, thickness=font)[0]
    c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
    cv2.rectangle(result_image, c1, c2, color, -1)
    cv2.putText(
        result_image,
        display_txt,
        (c1[0], c1[1] - 2),
        0,
        line / 3,
        [225, 255, 255],
        thickness=font,
        lineType=cv2.LINE_AA,
    )
    return cv2


def exec_detect(target_image_path):
    # 라벨 읽어 들이기
    labels = current_app.config["LABELS"]

    # 이미지 읽어 들이기
    image = Image.open(target_image_path)

    # 이미지 데이터를 텐서형의 수치 데이터로 변환
    image_tensor = torchvision.transforms.functional.to_tensor(image)

    # model.pt를 detector 폴더 하위로 이동한다. , weights_only=False 추가하여 오류 해결
    model = torch.load(
        Path(current_app.root_path, "detector", "model.pt"), weights_only=False
    )

    # 모델의 추론 모드로 전환
    model = model.eval()

    # 추론의 실행
    output = model([image_tensor])[0]
    tags = []
    result_image = np.array(image.copy())

    # 학습 완료 모델이 감지한 각 물체만큼 이미지에 덧붙여 씀
    for box, label, score in zip(output["boxes"], output["labels"], output["scores"]):
        if score > 0.5 and labels[label] not in tags:
            print(score)
            print(labels[label])
            # 테두리 선의 색 결정
            color = make_color(labels)
            # 테두리 선의 작성
            line = make_line(result_image)
            # 감지 이미지의 테두리 선과 텍스트 라벨의 테두리 선의 위치 정보
            c1 = (int(box[0]), int(box[1]))
            c2 = (int(box[2]), int(box[3]))
            # 이미지에 테두리 선을 덧붙여 씀
            cv2 = draw_lines(c1, c2, result_image, line, color)
            # 이미지에 텍스트 라벨을 덧붙여 씀
            cv2 = draw_texts(result_image, line, c1, cv2, color, labels, label)
            tags.append(labels[label])

    # 감지 후의 이미지 파일명을 생성한다
    detected_image_file_name = str(uuid.uuid4()) + ".jpg"

    # 이미지 복사처 패스를 취득한다
    detected_image_file_path = str(
        Path(current_app.config["UPLOAD_FOLDER"], detected_image_file_name)
    )
    # 변환 후의 이미지 파일을 보존처로 복사한다
    cv2.imwrite(detected_image_file_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
    return tags, detected_image_file_name


def save_detected_image_tags(user_image, tags, detected_image_file_name):
    # 감지 후 이미지의 보존처 패스를 DB에 보존한다
    user_image.image_path = detected_image_file_name
    # 감지 플래그를 True로 한다
    user_image.is_detected = True
    db.session.add(user_image)
    # user_images_tags 레코드를 작성한다
    for tag in tags:
        user_image_tag = UserImageTag(user_image_id=user_image.id, tag_name=tag)
        db.session.add(user_image_tag)
    db.session.commit()


# p226 추가 끝 apps/detector/view.py에 태그 정보를 설정하고 데이터베이스에 저장한다.


# 상단에 import 하고 p228 추가
@dt.route("/detect/<string:image_id>", methods=["POST"])
# login_required 데코레이터를 붙여서 로그인 필수로 한다
@login_required
def detect(image_id):
    # user_images 테이블로부터 레코드를 취득한다
    user_image = db.session.query(UserImage).filter(UserImage.id == image_id).first()
    if user_image is None:
        flash("물체 대상의 이미지가 존재하지 않습니다.")
        return redirect(url_for("detector.index"))

    # 물체 검지 대상의 이미지 패스를 취득한다
    target_image_path = Path(current_app.config["UPLOAD_FOLDER"], user_image.image_path)
    # 물체 검지를 실행하여 태그와 변환 후의 이미지 패스를 취득한다
    tags, detected_image_file_name = exec_detect(target_image_path)

    try:
        # 데이터베이스에 태그와 변환 후의 이미지 패스 정보를 보존한다
        save_detected_image_tags(user_image, tags, detected_image_file_name)
    except SQLAlchemyError as e:
        flash("물체 검지 처리에서 오류가 발생했습니다. ")
        # 롤백한다
        db.session.rollback()
        # 오류 로그 출력
        current_app.logger.error(e)
        return redirect(url_for("detector.index"))
    return redirect(url_for("detector.index"))


# p234 삭제 엔드포인트 생성
@dt.route("/images/delete/<string:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    try:
        # user_image_tags 테이블로부터 레코드를 삭제한다
        db.session.query(UserImageTag).filter(
            UserImageTag.user_image_id == image_id
        ).delete()

        # user_images 테이블로부터 레코드를 삭제한다
        db.session.query(UserImage).filter(UserImage.id == image_id).delete()

        db.session.commit()
    except SQLAlchemyError as e:
        flash("이미지 삭제 처리에서 오류가 발생했습니다.")
        # 오류 로그 출력
        current_app.logger.error(e)
        db.session.rollback()
    return redirect(url_for("detector.index"))