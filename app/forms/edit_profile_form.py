from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField,\
    HiddenField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Email, Length, EqualTo,\
    regexp, Optional
from flask_wtf.file import FileAllowed

from app import app
from app.models import User

import phonenumbers


class EditProfileForm(FlaskForm):
    user_login = HiddenField()

    photo = FileField(
        label='Изменить фото профиля',
        description='допустимые форматы - ' + ','.join(
            app.config['PHOTO_FILE_EXTENTIONS']
        ),
        validators=[
            FileAllowed(
                app.config['PHOTO_FILE_EXTENTIONS'],
                'Недопустимый формат файла.'
            )
        ]
    )

    delete_photo = BooleanField(label='Удалить фото профиля')

    last_name = StringField(
        label='Фамилия*',
        validators=[
            DataRequired('Пожалуйста, введите вашу фамилию.'),
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

    first_name = StringField(
        label='Имя*',
        validators=[
            DataRequired('Пожалуйста, введите ваше имя.'),
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

    patronymic = StringField(
        label='Отчество (при наличии)',
        validators=[
            Length(max=100, message='Слишком длинное значение.')
        ]
    )

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

    new_password = PasswordField(
        label='Новый пароль',
        description='длина пароля - от 8 до 20 символов',
        validators=[
            Optional(),
            Length(min=8, message='Пароль слишком короткий.'),
            Length(max=20, message='Пароль слишком длинный.'),
            EqualTo('confirm_new_password', message='Пароли должны совпадать.')
        ]
    )

    confirm_new_password = PasswordField('Повторите пароль')

    submit = SubmitField('Сохранить изменения')
    
    def validate_email(self, field):
        current_user_login = self.user_login.data
        same_email_user = User.query.filter_by(email=field.data).first()
        if same_email_user is not None\
            and same_email_user.login != current_user_login:
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
