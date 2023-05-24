from flask_wtf import FlaskForm
from wtforms import TextAreaField


class AdActionConfirmForm(FlaskForm):
    message = TextAreaField('Описание')
