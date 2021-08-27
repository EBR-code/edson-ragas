from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    current_user,
    logout_user,
)
from forms import CreatePostForm, CreateSignupForm, LoginForm, CommentForm, ContactForm
from flask_gravatar import Gravatar
from functools import wraps
import smtplib
import os


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

ckeditor = CKEditor(app)
Bootstrap(app)

gravatar = Gravatar(
    app,
    size=100,
    rating="g",
    default="retro",
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None,
)

##SMTP SETUP
BLOG_EMAIL = os.environ.get("BLOG_EMAIL")
BLOG_PW = os.environ.get("BLOG_PW")

# CONNECT TO DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///blog.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# FLASK_LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)


# userloader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Create admin-only decorator
def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # if id is not 1 thenr return abord with 403 error
        if current_user.id != 1:
            return abort(403)
        # otherwise continue with the route function
        return function(*args, **kwargs)

    return decorated_function


# CONFIGURE TABLES


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


# db.create_all()


@app.route("/")
def portfolio():
    return render_template("portfolio.html", logged_in=current_user.is_authenticated)


@app.route("/blog")
def blog():
    posts = BlogPost.query.all()
    return render_template(
        "blog.html", all_posts=posts, logged_in=current_user.is_authenticated
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    signup_form = CreateSignupForm()
    if signup_form.validate_on_submit():

        if User.query.filter_by(email=signup_form.email.data).first():
            flash("You've already signed up with this email, log in instead.")
            return redirect(url_for("login"))
        else:

            hash_and_salted_pw = generate_password_hash(
                password=signup_form.password.data,
                method="pbkdf2:sha256",
                salt_length=8,
            )
            new_user = User(
                email=signup_form.email.data,
                password=hash_and_salted_pw,
                name=signup_form.name.data,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("blog"))
    return render_template(
        "register.html", form=signup_form, logged_in=current_user.is_authenticated
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password=password):
                login_user(user)
                return redirect(url_for("blog"))
            else:
                flash(message="Wrong password, please try again.")
                return redirect(url_for("login"))
        else:
            flash(message="Email doesn't exist in our database, please Sign Up.")
            return redirect(url_for("login"))
    return render_template(
        "login.html", form=login_form, logged_in=current_user.is_authenticated
    )


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("blog"))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash(message="You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment.data,
            comment_author=current_user,
            parent_post=requested_post,
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template(
        "post.html",
        post=requested_post,
        logged_in=current_user.is_authenticated,
        form=comment_form,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        email_send(
            name=contact_form.name.data,
            email=contact_form.email.data,
            phone=contact_form.phone.data,
            message=contact_form.message.data,
        )
        print("email_send")
        return render_template(
            "contact.html",
            form=contact_form,
            logged_in=current_user.is_authenticated,
            msg_sent=True,
        )

    return render_template(
        "contact.html",
        form=contact_form,
        logged_in=current_user.is_authenticated,
        msg_sent=False,
    )


def email_send(name, email, phone, message):
    email_message = f"Subject: Mail from Porfolio\n\nName:{name},\nEmail:{email},\nPhone:{phone},\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=BLOG_EMAIL, password=BLOG_PW)
        connection.sendmail(
            from_addr=BLOG_EMAIL, to_addrs="ragasedson@gmail.com", msg=email_message
        )


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("blog"))
    return render_template(
        "make-post.html", form=form, logged_in=current_user.is_authenticated
    )


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template(
        "make-post.html",
        form=edit_form,
        is_edit=True,
        logged_in=current_user.is_authenticated,
    )


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("blog"))


if __name__ == "__main__":
    app.run(debug=True)
