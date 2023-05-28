from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import Optional, NumberRange

from app import app
from app.models import TransportType

from datetime import datetime as dt


class FiltersForm(FlaskForm):
    transport_type = SelectField(
        'Тип транспорта',
        choices=[(0, 'любой')],
        coerce=int,
        validate_choice=False
    )

    mark = SelectField(
        'Марка',
        choices=[(0, 'любая')],
        coerce=int,
        validate_choice=False
    )

    model = SelectField(
        'Модель',
        choices=[(0, 'любая')],
        coerce=int,
        validate_choice=False
    )

    generation = SelectField(
        'Поколение',
        choices=[(0, 'любое')],
        coerce=int,
        validate_choice=False
    )

    serie = SelectField(
        'Серия',
        choices=[(0, 'любая')],
        coerce=int,
        validate_choice=False
    )

    modification = SelectField(
        'Модификация',
        choices=[(0, 'любая')],
        coerce=int,
        validate_choice=False
    )

    price_begin = IntegerField(
        'От',
        description='Цена, руб.',
        validators=[
            Optional(),
            NumberRange(min=1, message='Минимальная цена должна быть положительным числом.')
        ]
    )

    price_end = IntegerField(
        'До',
        description='Цена, руб.',
        validators=[
            Optional(),
            NumberRange(min=1, message='Максимальная цена должна быть положительным числом.')
        ]
    )

    release_year_begin = IntegerField(
        'От',
        description='Год выпуска',
        validators=[
            Optional(),
            NumberRange(
                min=app.config['MIN_CAR_RELEASE_YEAR'],
                max=dt.now().year,
                message='Пожалуйста, укажите корректный минимальный год выпуска.'
            )
        ]
    )

    release_year_end = IntegerField(
        'До',
        description='Год выпуска',
        validators=[
            Optional(),
            NumberRange(
                min=app.config['MIN_CAR_RELEASE_YEAR'],
                max=dt.now().year,
                message='Пожалуйста, укажите корректный максимальный год выпуска.'
            )
        ]
    )

    mileage_begin = IntegerField(
        'От',
        description='Пробег, км',
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message='Минимальный пробег не может быть отрицательным числом.'
            )
        ]
    )

    mileage_end = IntegerField(
        'До',
        description='Пробег, км',
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message='Максимальный пробег не может быть отрицательным числом.'
            )
        ]
    )

    owners_count_begin = IntegerField(
        'От',
        description='Владельцев по ПТС',
        validators=[
            Optional(),
            NumberRange(
                min=1,
                message='Минимальное количество владельцев должно быть положительным числом.'
            )
        ]
    )

    owners_count_end = IntegerField(
        'До',
        description='Владельцев по ПТС',
        validators=[
            Optional(),
            NumberRange(
                min=1,
                message='Максимальное количество владельцев должно быть положительным числом.'
            )
        ]
    )

    color = SelectField(
        'Цвет',
        choices=[(0, 'любой')],
        coerce=int,
        validate_choice=False
    )

    is_broken = SelectField(
        'Состояние',
        choices=[(-1, 'Любое'), (0, 'Не битый'), (1, 'Битый')],
        coerce=int,
        validate_choice=False
    )

    location = StringField('Населённый пункт')

    per_page = SelectField(
        'Объявлений на странице',
        choices=[(count, str(count)) for count in app.config['ADS_PER_PAGE']],
        coerce=int,
        validate_choice=False
    )

    # search = StringField('Найти...')

    reset = SubmitField('Сбросить фильтры')
    submit = SubmitField('Применить фильтры')

    def __init__(self, *args, **kwargs):
        super(FiltersForm, self).__init__(*args, **kwargs)
        self.transport_type.choices.extend(
            [(tt.id, tt.name) for tt in TransportType.query.all()]
        )
