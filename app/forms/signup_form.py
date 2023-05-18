from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, Length, EqualTo,\
    regexp, Optional
from flask_wtf.file import FileAllowed

from app import app
from app.models import User

import phonenumbers


class SignupForm(FlaskForm):
    photo = FileField(
        label='Фото профиля',
        description='допустимые форматы - PNG, JPG, JPEG',
        validators=[
            FileAllowed(
                app.config['PHOTO_FILE_EXTENTIONS'],
                'Недопустимый формат файла.'
            )
        ]
    )

    first_name = StringField(
        label='Имя*',
        validators=[
            DataRequired('Пожалуйста, введите ваше имя.'),
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

    last_name = StringField(
        label='Фамилия*',
        validators=[
            DataRequired('Пожалуйста, введите вашу фамилию.'),
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

    patronymic = StringField(
        label='Отчество (при наличии)',
        validators=[
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

    login = StringField(
        label='Логин*',
        description='длина логина - от 6 до 20 символов (буквы, цифры, подчёркивание)',
        validators=[
            DataRequired('Пожалуйста, введите логин.'),
            Length(min=6, message='Логин слишком короткий.'),
            Length(max=20, message='Логин слишком длинный.'),
            regexp(r'^\w+$', message='Логин может содержать только буквы, цифры, подчёркивания.')
        ]
    )

    password = PasswordField(
        label='Пароль*',
        description='длина пароля - от 8 до 20 символов',
        validators=[
            DataRequired('Пожалуйста, введите пароль.'),
            Length(min=8, message='Пароль слишком короткий.'),
            Length(max=20, message='Пароль слишком длинный.'),
            EqualTo('confirm_password', message='Пароли должны совпадать.')
        ]
    )

    confirm_password = PasswordField('Повторите пароль*')

    email = StringField('Email',
        validators=[
            Optional(),
            Email(message='Неправильный email-адрес.')
        ]
    )

    phone_number = StringField('Номер телефона*',
        validators=[
            DataRequired('Пожалуйста, введите номер телефона.'),
            Length(max=20, message='Телефон слишком длинный.')
        ]
    )

    location = StringField('Населённый пункт')

    submit = SubmitField('Зарегистрироваться')
    
    def validate_login(self, field):
        user = User.query.filter_by(login=field.data).first()
        if user is not None:
            raise ValidationError(
                'Пользователь с таким логином уже существует.'
            )
    
    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email is not None:
            raise ValidationError(
                'Данный email уже используется.'
            )
    
    def validate_phone_number(self, field):
        try:
            phone = phonenumbers.parse(field.data)
            if not phonenumbers.is_valid_number(phone):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Неправильный номер телефона.')
