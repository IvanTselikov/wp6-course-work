from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[
        DataRequired('Пожалуйста, введите логин.')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired('Пожалуйста, введите пароль.')
    ])
    submit = SubmitField('Войти')
