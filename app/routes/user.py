from flask import render_template, flash
from flask import jsonify

from app import app, db
from app.forms import CreateAdForm, EditProfileForm, LoginForm, SignupForm, FiltersForm
from app.models import User, AdStatus, Location

from werkzeug.utils import secure_filename

from flask_login import current_user, login_required
from flask_breadcrumbs import register_breadcrumb

import os

from .functions import view_user_dlc, format_registration_date,\
    remove_profile_photo, upload_photo


@app.route('/user/<user_login>', methods=['get'])
@register_breadcrumb(app, '.user', '',
                    dynamic_list_constructor=view_user_dlc)
def get_user_page(user_login):
    user = User.query.filter_by(login=user_login).first()
    if user:
        kwargs = {
            'user': user,
            'registration_date': format_registration_date(user.registration_date)
        }

        ads = {
            'opened': [], 'closed': [], 'on_checking': [], 'on_revision': [], 'blocked': [],
            'me_opened': [], 'me_checking': [], 'me_revision': [], 'me_blocked': []
        }

        for ad in user.ads:
            if ad.status_id == AdStatus.OPENED:
                ads['opened'].append(ad)
            elif ad.status_id == AdStatus.CLOSED:
                ads['closed'].append(ad)
            elif ad.status_id == AdStatus.ON_CHECKING:
                ads['on_checking'].append(ad)
            elif ad.status_id == AdStatus.ON_REVISION:
                ads['on_revision'].append(ad)
            elif ad.status_id == AdStatus.BLOCKED:
                ads['blocked'].append(ad)

        for ad in user.moderated_ads:
            if ad.status_id == AdStatus.OPENED:
                ads['me_opened'].append(ad)
            elif ad.status_id == AdStatus.ON_CHECKING:
                ads['me_checking'].append(ad)
            elif ad.status_id == AdStatus.ON_REVISION:
                ads['me_revision'].append(ad)
            elif ad.status_id == AdStatus.BLOCKED:
                ads['me_blocked'].append(ad)
        
        kwargs.update({ 'ads': ads })

        if current_user.is_authenticated:
            ad_form = CreateAdForm()
            kwargs.update({ 'ad_form': ad_form })

            if current_user.login == user_login:
                edit_profile_form = EditProfileForm()
                kwargs.update({ 'edit_profile_form': edit_profile_form })
        else:
            login_form = LoginForm()
            signup_form = SignupForm()
            kwargs.update({ 'login_form': login_form, 'signup_form': signup_form })
    
        filters_form = FiltersForm()

        kwargs.update({ 'filters_form': filters_form })

        return render_template('profile.html', **kwargs)

    return {}, 404


@app.route('/user/<user_login>', methods=['put'])
@login_required
def update_user(user_login):
    user = User.query.filter_by(login=user_login).first()

    if user:
        if current_user.id == user.id:
            form = EditProfileForm()
            if form.validate():
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.patronymic = form.patronymic.data
                user.email = form.email.data
                user.phone_number = form.phone_number.data

                location_name = form.location.data
                if location_name:
                    location_id = Location.get_id(location_name)
                    if not location_id:
                        new_location = Location(name=location_name)
                        db.session.add(new_location)
                        db.session.commit()
                        location_id = new_location.id
                    user.location_id = location_id

                if form.new_password.data:
                    user.set_password(form.new_password.data)

                db.session.add(user)
                db.session.commit()

                if form.delete_photo.data or form.photo.data.filename:
                    remove_profile_photo(user)

                if form.photo.data.filename:
                    # сохранение нового фото
                    user_storage_path = os.path.join(
                        app.config['UPLOADS_FOLDER'],
                        user.login
                    )

                    photo_filename = secure_filename(form.photo.data.filename)
                    _, file_extension = os.path.splitext(photo_filename)

                    path_origin = os.path.join(
                        user_storage_path,
                        app.config['PROFILE_PHOTO_FILENAME'] + file_extension
                    )

                    path_small = os.path.join(
                        user_storage_path,
                        app.config['PROFILE_PHOTO_FILENAME']
                            + app.config['PHOTO_SMALL_PREFIX']
                            + file_extension
                    )
                    
                    path_tiny = os.path.join(
                        user_storage_path,
                        app.config['PROFILE_PHOTO_FILENAME']
                            + app.config['PHOTO_TINY_PREFIX']
                            + file_extension
                    )

                    upload_photo(
                        form.photo.data,
                        path_origin=path_origin,
                        path_small=path_small,
                        path_tiny=path_tiny
                    )
                
                flash('Изменения в профиле сохранены.')

                return {}, 200

            return jsonify(form.errors), 400
        return jsonify({ 'errors': ['Профиль пользователя может редактировать только он сам.'] }), 405
    return jsonify({ 'errors': ['Пользователь не найден.'] }), 400
