from wtforms import SubmitField, BooleanField, HiddenField
from app.forms import CreateAdForm


class EditAdForm(CreateAdForm):
    ad_id = HiddenField()

    delete_photo_1 = BooleanField(label='Удалить главное фото')
    delete_photo_2 = BooleanField(label='Удалить доп. фото 1')
    delete_photo_3 = BooleanField(label='Удалить доп. фото 2')

    submit = SubmitField('Редактировать объявление')

    def validate_ad_id(self, field):
        pass
