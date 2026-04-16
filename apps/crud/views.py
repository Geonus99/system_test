from flask import Blueprint, render_template, redirect, url_for

# db를 import한다
from apps.app import db
# User 클래스를 import한다
from apps.crud.models import User
from apps.crud.forms import UserForm

# Blueprint로 crud 앱을 생성한다.
crud = Blueprint(
    "crud",
    __name__,
    template_folder="templates",
    static_folder="static",
)

# index 엔드포인트를 작성하고 index.html을 반환한다.
@crud.route("/")
def index():
    return render_template("crud/index.html")

@crud.route("/sql")
def sql():
    db.session.query(User).all()
    # 모델 객체 이용하는 방법도 있음
    # User.query.all()
    return "콘솔 로그를 확인해 주세요"

@crud.route("/users/new", methods=["GET","POST"])
def create_user():
    # UserForm을 인스턴스화한다
    form = UserForm()
    # 폼의 값을 검증한다
    if form.validate_on_submit():
        # 사용자를 작성한다
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        # 사용자를 추가하고 커밋한다
        db.session.add(user)
        db.session.commit()
        # 사용자의 일람 화면으로 리다이렉트한다
        return redirect(url_for("crud.users"))
    return render_template("crud/create.html", form=form)

@crud.route("/users")
def users():
    """사용자의 일람을 취득한다"""
    user = User.query.all()
    return render_template("crud/index.html",users=user)

@crud.route("/users/<int:user_id>", methods=["GET","POST"])
def edit_user(user_id):
    form = UserForm()

    # User 모델을 이용하여 사용자를 취득한다
    user = User.query.filter_by(id=user_id).first()

    # form으로부터 제출된 경우는 사용자를  갱신하여 사용자의 일람 화면으로 리다에릭트한다.
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("crud.users"))
    
    # GET의 경우는 HTML을 반환한다.
    return render_template("crud/edit.html", user=user, form=form)

@crud.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    user=User.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("crud.users"))