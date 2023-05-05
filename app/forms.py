from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField, IntegerField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, Length, EqualTo, regexp, Optional, NumberRange, NoneOf
from flask_wtf.file import FileAllowed, FileRequired
from flask_uploads import UploadSet, IMAGES

from app.models import User, TransportType, Mark, Model, PtsType

import re
import phonenumbers

IMAGES_SET = UploadSet('images', IMAGES)


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[
        DataRequired('Пожалуйста, введите логин.')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired('Пожалуйста, введите пароль.')
    ])
    submit = SubmitField('Войти')


class SignupForm(FlaskForm):
    photo = FileField(
        label='Фото профиля',
        description='допустимые форматы - PNG, JPG, JPEG',
        validators=[
            FileAllowed(['png', 'jpg', 'jpeg'], 'Недопустимый формат файла.')
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

    signup_login = StringField(
        label='Логин*',
        description='длина логина - от 6 до 20 символов (буквы, цифры, подчёркивание)',
        validators=[
            DataRequired('Пожалуйста, введите логин.'),
            Length(min=6, message='Логин слишком короткий.'),
            Length(max=20, message='Логин слишком длинный.'),
            regexp(r'^\w+$', message='Логин может содержать только буквы, цифры, подчёркивания.')
        ]
    )

    signup_password = PasswordField(
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

    signup_submit = SubmitField('Зарегистрироваться')

    # def validate_photo(form, field):
    #     if field.data:
    #         field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)
    
    def validate_signup_login(self, field):
        user = User.query.filter_by(login=field.data).first()
        if user is not None:
            raise ValidationError(
                'Пользователь с таким логином уже существует.')
    
    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email is not None:
            raise ValidationError(
                'Данный email уже используется.')
    
    def validate_phone_number(self, field):
        try:
            phone = phonenumbers.parse(field.data)
            if not phonenumbers.is_valid_number(phone):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Неправильный номер телефона.')


class AdForm(FlaskForm):
    transport_type = SelectField(
        'Тип транспорта*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите тип транспорта.'),
            NoneOf([0], 'Пожалуйста, укажите тип транспорта.')
        ]
    )
    mark = SelectField(
        'Марка*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите марку автомобиля.'),
            NoneOf([0], 'Пожалуйста, укажите марку автомобиля.')
        ]
    )
    model = SelectField(
        'Модель*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите модель автомобиля.'),
            NoneOf([0], 'Пожалуйста, укажите модель автомобиля.')
        ]
    )
    generation = SelectField(
        'Поколение*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите поколение.'),
            NoneOf([0], 'Пожалуйста, укажите поколение.')
        ]
    )
    serie = SelectField(
        'Серия*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите серию.'),
            NoneOf([0], 'Пожалуйста, укажите серию.')
        ]
    )
    modification = SelectField(
        'Модификация*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите модификацию.'),
            NoneOf([0], 'Пожалуйста, укажите модификацию.')
        ]
    )
    release_year = IntegerField(
        'Год выпуска*',
        validators=[
            InputRequired('Пожалуйста, укажите год выпуска.'),
            NumberRange(min=1900, max=2100, message='Пожалуйста, укажите корректный год выпуска.')
        ]
    )
    mileage = IntegerField(
        'Пробег, км*',
        validators=[
            InputRequired('Пожалуйста, укажите пробег.'),
            NumberRange(min=0, message='Пробег не может быть отрицательным числом.')
        ]
    )
    pts_type = SelectField(
        'Тип ПТС*',
        choices=[(0, 'не выбрано')],
        coerce=int,
        validate_choice=False,
        validators=[
            InputRequired('Пожалуйста, укажите тип ПТС.'),
            NoneOf([0], 'Пожалуйста, укажите тип ПТС.')
        ]
    )
    owners_count = IntegerField(
        'Владельцев по ПТС*',
        validators=[
            InputRequired('Пожалуйста, укажите количество владельцев по ПТС.'),
            NumberRange(min=1, message='Количество владельцев не может быть меньше 1.')
        ]
    )
    is_broken = SelectField(
        'Состояние*',
        choices=[(0, 'Не битый'), (1, 'Битый')],
        coerce=int,
        validate_choice=False,
        validators=[InputRequired('Пожалуйста, укажите состояние автомобиля.')]
    )
    color = SelectField(
        'Цвет',
        choices=[(0, 'другой')],
        coerce=int,
        validate_choice=False
    )
    vin = StringField(
        'VIN*',
        description='состоит из 17 символов (цифры, буквы латинского алфавита)',
        validators=[
            DataRequired('Пожалуйста, введите VIN.'),
            Length(min=17, max=17, message='VIN должен содержать 17 символов.'),
            regexp(r'^[(A-H|J-N|P|R-Z|0-9)]{17}$', message='Указанный VIN имеет некорректный формат.')
        ]
    )
    photo_1 = FileField(
        label='Главное фото',
        description='будет отображаться как баннер объявления',
        validators=[
            FileAllowed(['png', 'jpg', 'jpeg'], 'Недопустимый формат файла.')
        ]
    )
    photo_2 = FileField(
        label='Доп. фото 1',
        validators=[
            FileAllowed(['png', 'jpg', 'jpeg'], 'Недопустимый формат файла.')
        ]
    )
    photo_3 = FileField(
        label='Доп. фото 2',
        validators=[
            FileAllowed(['png', 'jpg', 'jpeg'], 'Недопустимый формат файла.')
        ]
    )
    price = IntegerField(
        'Цена*',
        validators=[
            InputRequired('Пожалуйста, укажите цену.'),
            NumberRange(min=1, message='Цена должна быть положительным числом.')
        ]
    )
    location = StringField('Населённый пункт')
    description = TextAreaField('Описание')

    submit = SubmitField('Создать объявление')

    # def validate_release_year(self, field):
    #     user = User.query.filter_by(login=field.data).first()
    #     if user is not None:
    #         raise ValidationError(
    #             'Пользователь с таким логином уже существует.')

    def change_release_year_limits(self, year_begin, year_end):
        validators = self.release_year.validators
        nrange_validator = list(filter(lambda v: isinstance(v, NumberRange), validators))[0]

        year_begin = year_begin or 1900  # TODO: в константу
        year_end = year_end or 2100
        nrange_validator.min = year_begin
        nrange_validator.max = year_end
        return year_begin, year_end


    def __init__(self, *args, **kwargs):
        super(AdForm, self).__init__(*args, **kwargs)
        self.transport_type.choices.extend([(tt.id, tt.name) for tt in TransportType.query.all()])
        self.pts_type.choices.extend([(p.id, p.name) for p in PtsType.query.all()])
