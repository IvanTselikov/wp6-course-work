from flask import jsonify, request, render_template, redirect, url_for, flash

from app import app, db
from app.forms import CreateAdForm, LoginForm, SignupForm, FiltersForm,\
    AdActionConfirmForm, EditAdForm
from app.models import Ad, AdStatus, Location

from werkzeug.utils import secure_filename

from flask_login import current_user, login_required
from flask_breadcrumbs import register_breadcrumb

import os
from glob import glob

from .functions import upload_photo, parse_int_or_skip, view_ad_dlc, remove_ad_photo


@app.route('/ads/<int:ad_id>', methods=['get'])
@register_breadcrumb(app, '.ad', '',
                    dynamic_list_constructor=view_ad_dlc)
def get_ad(ad_id):
    if request.content_type == 'application/json':
        ad = Ad.query.filter_by(id=ad_id).first()
        if ad:
            return jsonify({
                'transport_type': ad.car.serie.generation.model.mark.transport_type.id,
                'mark': ad.car.serie.generation.model.mark.id,
                'model': ad.car.serie.generation.model.id,
                'generation': ad.car.serie.generation.id,
                'serie': ad.car.serie.id,
                'modification': ad.car_id,
                'color': ad.color_id,
                'location': ad.location_id,
                'description': ad.description,
                'pts_type': ad.pts_type_id
            })
        return {}, 404
    else:
        kwargs = {}
        if current_user.is_authenticated:
            photo_filename = glob(os.path.join(
                app.config['UPLOADS_FOLDER'],
                current_user.login,
                app.config['PROFILE_PHOTO_FILENAME'] + '.*'
            ))

            if photo_filename:
                photo_filename = photo_filename[0]
                photo_filename = os.path.join(*(photo_filename.split(os.path.sep)[1:]))

                kwargs.update({'photo_filename': photo_filename})
            
            ad_form = CreateAdForm()
            kwargs.update({ 'ad_form': ad_form })
        else:
            login_form = LoginForm()
            signup_form = SignupForm()
            kwargs.update({'login_form': login_form, 'signup_form': signup_form})

        filters_form = FiltersForm()
        edit_ad_form = EditAdForm()
        kwargs.update({ 'filters_form': filters_form, 'edit_ad_form': edit_ad_form })

        ad = Ad.query.filter_by(id=ad_id).first()
        kwargs.update({ 'ad': ad })

        ad_action_confirm_form = AdActionConfirmForm()
        kwargs.update({ 'ad_action_confirm_form': ad_action_confirm_form })

        return render_template('ad.html', **kwargs)


@app.route('/ads', methods=['post'])
@login_required
def create_ad():
    form = CreateAdForm()
    if form.validate():
        ad = Ad(
            car_id = form.modification.data,
            release_year = form.release_year.data,
            vin = form.vin.data,
            pts_type_id = form.pts_type.data,
            owners_count = form.owners_count.data,
            color_id = form.color.data or None,
            is_broken = form.is_broken.data,
            mileage = form.mileage.data,
            seller_id = current_user.id,
            price = form.price.data,
            description = form.description.data.strip()
        )

        # объявления администраторов публикуются сразу без модерации,
        # остальные - проходят проверку администратором
        if current_user.is_admin:
            ad.status_id = AdStatus.OPENED 
        else:
            ad.assign_admin()

        location_name = form.location.data
        if location_name:
            location_id = Location.get_id(location_name)
            if not location_id:
                new_location = Location(name=location_name)
                db.session.add(new_location)
                db.session.commit()
                location_id = new_location.id
            ad.location_id = location_id

        db.session.add(ad)
        db.session.commit()

        # создание хранилища для фото объявления
        ad_storage_path = os.path.join(
            app.config['UPLOADS_FOLDER'],
            current_user.login,
            str(ad.id)
        )
        os.makedirs(ad_storage_path, exist_ok=True)

        # сохранение фото объявления
        photos = [f for f in [form.photo_1, form.photo_2, form.photo_3]
                  if f.data.filename]

        for i, photo in enumerate(photos):
            photo_filename = secure_filename(photo.data.filename)
            _, file_extension = os.path.splitext(photo_filename)

            path_origin = os.path.join(
                ad_storage_path,
                str(i+1) + file_extension
            )
            
            path_small = os.path.join(
                ad_storage_path,
                str(i+1) + app.config['PHOTO_SMALL_PREFIX'] + file_extension
            )

            upload_photo(photo.data, path_origin=path_origin, path_small=path_small)
        return {}, 200
    return jsonify(form.errors), 400


@app.route('/ads', methods=['put'])
@login_required
def update_ad():
    form = EditAdForm()
    if form.validate():
        ad = Ad.query.filter_by(id=form.ad_id.data).first()
        if ad:
            ad.car_id = form.modification.data
            ad.release_year = form.release_year.data
            ad.vin = form.vin.data
            ad.pts_type_id = form.pts_type.data
            ad.owners_count = form.owners_count.data
            ad.color_id = form.color.data or None
            ad.is_broken = form.is_broken.data
            ad.mileage = form.mileage.data
            ad.seller_id = current_user.id
            ad.price = form.price.data
            ad.description = form.description.data.strip()

            ad.status_id = AdStatus.OPENED if current_user.is_admin\
                else AdStatus.ON_CHECKING

            db.session.add(ad)
            db.session.commit()

            if form.delete_photo_1.data or form.photo_1.data.filename:
                remove_ad_photo(ad, 1)
            if form.delete_photo_2.data or form.photo_2.data.filename:
                remove_ad_photo(ad, 2)
            if form.delete_photo_3.data or form.photo_3.data.filename:
                remove_ad_photo(ad, 3)

            ad_storage_path = os.path.join(
                app.config['UPLOADS_FOLDER'],
                current_user.login,
                str(ad.id)
            )
            
            photos = [f for f in [form.photo_1, form.photo_2, form.photo_3]
                  if f.data.filename]

            for i, photo in enumerate(photos):
                photo_filename = secure_filename(photo.data.filename)
                _, file_extension = os.path.splitext(photo_filename)
                # photo_filename = '{}{}'.format(i+1, file_extension)

                path_origin = os.path.join(
                    ad_storage_path,
                    str(i+1) + file_extension
                )
                
                path_small = os.path.join(
                    ad_storage_path,
                    str(i+1) + app.config['PHOTO_SMALL_PREFIX'] + file_extension
                )

                upload_photo(photo.data, path_origin=path_origin, path_small=path_small)
            
            return {}, 200
        return jsonify({'ad_id': 'Объявление не найдено.'}), 400
    return jsonify(form.errors), 400


@app.route('/ads/<ad_id>/status/<status_id>', methods=['post'])
@login_required
def set_ad_status(ad_id, status_id):
    ad_id = parse_int_or_skip(ad_id, default=None)
    status_id = parse_int_or_skip(status_id, default=None)

    ad = Ad.query.filter_by(id=ad_id).first()
    status = AdStatus.query.filter_by(id=status_id).first()

    form = AdActionConfirmForm()
    admin_message = form.message.data if form.data else None

    if ad and status and ad.change_status(
        current_user.id, int(status_id), admin_message
    ):
        db.session.add(ad)
        db.session.commit()
        return redirect(url_for('get_ad', ad_id=ad_id))

    return {'error': ['Некорректный id объявления или статуса.']}, 405


@app.route('/ads/<ad_id>', methods=['delete'])
@login_required
def delete_ad(ad_id):
    ad = Ad.query.filter_by(id=ad_id).first()
    if ad:
        if current_user.id == ad.seller_id:
            db.session.delete(ad)
            db.session.commit()
            flash('Объявление успешно удалено.')
            return redirect(url_for('index'))
        return {'errors': ['Удалить объявление может только его владелец.']}, 405
    return {'errors': ['Объявление не найдено.']}, 400
