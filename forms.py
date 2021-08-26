from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from wtforms.fields.html5 import EmailField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField(label="Blog Post Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    img_url = StringField(label="Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Blog Content", validators=[DataRequired()])
    submit = SubmitField(label="Submit Post")

class CreateSignupForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    name = StringField(label="Name", validators=[DataRequired()])
    submit = SubmitField(label="Sign me up!")

class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Log in")

class CommentForm(FlaskForm):
    comment = CKEditorField(label="Comment", validators=[DataRequired()])
    submit = SubmitField(label="Submit Comment")

class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = EmailField(label="Email", validators=[DataRequired()])
    phone = StringField(label="Phone Number", validators=[DataRequired()])
    message = TextAreaField(label="Message", validators=[DataRequired()])
