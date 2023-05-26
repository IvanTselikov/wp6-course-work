from flask import redirect, url_for, make_response, jsonify

from app import app, db
from app.forms import SignupForm
from app.models import User, Location

from werkzeug.utils import secure_filename

from flask_login import current_user, login_user

import os

from .functions import set_location_cookie, upload_photo



@app.route('/signup', methods=['post'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = SignupForm()
    if form.validate():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            patronymic=form.patronymic.data,
            login=form.login.data,
            password=form.password.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            is_admin=0
        )

        location_name = form.location.data
        if location_name:
            location_id = Location.get_id(location_name)
            if not location_id:
                new_location = Location(name=location_name)
                db.session.add(new_location)
                db.session.commit()
                location_id = new_location.id
            user.location_id = location_id
        
        db.session.add(user)
        db.session.commit()

        login_user(user)

        # создание хранилища для фото пользователя
        user_storage_path = os.path.join(app.config['UPLOADS_FOLDER'], user.login)
        os.makedirs(user_storage_path, exist_ok=True)

        # сохранение фото профиля
        photo_filename = form.photo.data.filename
        if photo_filename:
            photo_filename = secure_filename(form.photo.data.filename)
            _, file_extension = os.path.splitext(photo_filename)

            path_origin = os.path.join(
                user_storage_path,
                app.config['PROFILE_PHOTO_FILENAME'] + file_extension
            )

            path_small = os.path.join(
                user_storage_path,
                app.config['PROFILE_PHOTO_FILENAME'] + app.config['PHOTO_SMALL_PREFIX'] + file_extension
            )
            
            path_tiny = os.path.join(
                user_storage_path,
                app.config['PROFILE_PHOTO_FILENAME'] + app.config['PHOTO_TINY_PREFIX'] + file_extension
            )

            upload_photo(
                form.photo.data,
                path_origin=path_origin,
                path_small=path_small,
                path_tiny=path_tiny
            )

        response = make_response(redirect(url_for('index')))
        set_location_cookie(response)
        return response
    return jsonify(form.errors), 400
