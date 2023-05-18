from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, SelectField,\
    IntegerField, BooleanField, HiddenField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Length,\
    regexp, NumberRange, NoneOf
from flask_wtf.file import FileAllowed

from app.models import TransportType, PtsType, Generation
from app.functions import *


class CreateAdForm(FlaskForm):
    ad_id = HiddenField()
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
            NumberRange(
                min=EARLIEST_RELEASE_YEAR,
                max=get_current_year(),
                message='Пожалуйста, укажите корректный год выпуска.'
            )
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

    delete_photo_1 = BooleanField(label='Удалить главное фото')
    delete_photo_2 = BooleanField(label='Удалить доп. фото 1')
    delete_photo_3 = BooleanField(label='Удалить доп. фото 2')

    price = IntegerField(
        'Цена, руб.*',
        validators=[
            InputRequired('Пожалуйста, укажите цену.'),
            NumberRange(min=1, message='Цена должна быть положительным числом.')
        ]
    )
    location = StringField('Населённый пункт')
    description = TextAreaField('Описание')

    submit = SubmitField('Создать объявление')

    def validate_release_year(self, field):
        generation = Generation.query.filter_by(id=self.generation.data).first()
        if generation:
            year_begin = generation.year_begin
            year_end = generation.year_end

            if field.data < year_begin or field.data > year_end:
                raise ValidationError(
                    'Пожалуйста, укажите корректный год выпуска.'
                )
        
    def change_release_year_limits(self, year_begin, year_end): # TODO: в интерфейс (без повторения кода)
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
