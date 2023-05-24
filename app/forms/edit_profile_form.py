from wtforms import PasswordField, SubmitField, BooleanField, HiddenField
from wtforms.validators import ValidationError, Length, EqualTo, Optional

from app.forms import SignupForm
from app.models import User


class EditProfileForm(SignupForm):
    user_login = HiddenField()

    SignupForm.photo.label = 'Изменить фото профиля'

    delete_photo = BooleanField(label='Удалить фото профиля')

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
