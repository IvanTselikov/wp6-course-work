from flask import render_template, redirect, url_for, flash, make_response
from flask import jsonify, request

from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db
from app.forms import *
from app.functions import *
from app.models import *

from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse

from flask_login import current_user, login_user, logout_user, login_required
from flask_breadcrumbs import register_breadcrumb
from sqlalchemy import or_, and_, func

import os
from glob import glob

from humps import camelize

from .functions import set_location_cookie, get_filtered_ads


@app.route('/')
@app.route('/index')
@register_breadcrumb(app, '.', 'Главная')
def index():
    filters_form = FiltersForm()
    kwargs = { 'filters_form': filters_form }

    if current_user.is_authenticated:
        ad_form = CreateAdForm()
        kwargs.update({ 'ad_form': ad_form })
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})

    # фильтрация объявлений
    filter_params = {
        'page': parse_int_or_skip(request.args.get('page', default=1)),
        'per_page': app.config['ADS_PER_PAGE_DEFAULT']
    }

    for key, value in request.cookies.items():
        filter_params.update({ key: parse_int_or_skip(value) })
    
    ads, result_header = get_filtered_ads(filter_params)
    
    kwargs.update({
        'ads': ads,
        'ads_section_header': result_header
    })

    return render_template('index.html', **kwargs)
    

@app.route('/filters', methods=['post'])
def filters():
    response = make_response(redirect(url_for('index')))

    filters_form = FiltersForm()
    print('=================')
    print(filters_form.reset)
    print('=================')
    if filters_form.reset.data:
        # сброс фильтров
        response.set_cookie('is_filtered', '', 0)
        for field in filters_form:
            response.set_cookie(field.name, '', 0)
    elif filters_form.validate():
        # установка фильтров
        response.set_cookie('is_filtered', '1')
        for field in filters_form:
            if not field.name.startswith('csrf'):
                if field.data:
                    response.set_cookie(field.name, str(field.data))
                else:
                    response.set_cookie(field.name, '', 0)
    else:
        # ошибки в фильтрах
        return jsonify(filters_form.errors), 400
    
    return response


@app.route('/login', methods=['post'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate():
        user = User.query.filter_by(login=form.login.data).first()
        if user is None or not user.check_password(form.password.data):
            errors = {'other': ['Неправильное имя пользователя или пароль']}
            return jsonify(errors), 400
        else:
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            
            # при входе в аккаунт отображаются только объявления из региона пользователя
            response = make_response(redirect(next_page))
            set_location_cookie(response)
            return response
    return jsonify(form.errors), 400


@app.route('/signup', methods=['POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = SignupForm()
    if form.validate():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            patronymic=form.patronymic.data,
            login=form.signup_login.data,
            password=form.signup_password.data,
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

            # form.photo.data.save(os.path.join(user_storage_path, photo_filename))
        return redirect(url_for('index'))
    return jsonify(form.errors), 400


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/marks/<transport_type_id>', methods=['get'])
def marks(transport_type_id):
    marks = Mark.query.filter(
        or_(Mark.transport_type_id == transport_type_id, Mark.transport_type_id == None)
    )
    return jsonify({ m.id : m.name for m in marks }), 200 if marks.count() else 404


@app.route('/models/<mark_id>', methods=['get'])
def models(mark_id):
    models = Model.query.filter_by(mark_id=mark_id)
    return jsonify({ m.id : m.name for m in models }), 200 if models.count() else 404


@app.route('/generations/<model_id>', methods=['get'])
def generations(model_id):
    generations = Generation.query.filter_by(model_id=model_id)
    response = {}
    for g in generations:
        generation_info = g.name
        if g.year_begin or g.year_end:
            generation_info += ' ({} - {})'.format(g.year_begin, g.year_end)
        response.update({g.id: generation_info})
    return jsonify(response), 200 if generations.count() else 404


@app.route('/series/<generation_id>', methods=['get'])
def series(generation_id):
    series = Serie.query.filter_by(generation_id=generation_id)
    return jsonify({ s.id : s.name for s in series }), 200 if series.count() else 404


@app.route('/modifications/<serie_id>', methods=['get'])
def modifications(serie_id):
    modifications = Modification.query.filter_by(serie_id=serie_id)
    return jsonify({ m.id : m.name for m in modifications }), 200 if modifications.count() else 404


@app.route('/release_years/<generation_id>', methods=['get'])
def release_years(generation_id):
    response = {
        'yearBegin': { 'value': EARLIEST_RELEASE_YEAR, 'isDefault': True },
        'yearEnd': { 'value': get_current_year(), 'isDefault': True },
    }

    generation = Generation.query.filter_by(id=generation_id).first()
    if generation:
        if generation.year_begin:
            response['yearBegin'] = {
                'value': generation.year_begin,
                'isDefault': False
            }
        if generation.year_end:
            response['yearEnd'] = {
                'value': generation.year_end,
                'isDefault': False
            }

    return jsonify(response)


@app.route('/colors', methods=['get'])
def colors():
    colors = Color.query.all()
    return jsonify({
        c.id: {
            'name': c.name,
            'red': c.red,
            'green': c.green,
            'blue': c.blue
        } for c in colors
    })


@app.route('/locations', methods=['get'])
def locations():
    locations = Location.query.all()
    return jsonify({ loc.id : loc.name for loc in locations})


@app.route('/ad', methods=['post'])
@login_required
def ad():
    form = CreateAdForm()
    if form.validate():
        ad = Ad(
            car_id = form.modification.data,
            release_year = form.release_year.data,
            vin = form.vin.data,
            pts_type_id = form.pts_type.data,
            owners_count = form.owners_count.data,
            color_id = form.color.data,
            is_broken = form.is_broken.data,
            mileage = form.mileage.data,
            seller_id = current_user.id,
            price = form.price.data,
            description = form.description.data.strip()
        )

        location_name = form.location.data
        if location_name:
            location_id = Location.get_id(location_name)
            if not location_id:
                new_location = Location(name=location_name)
                db.session.add(new_location)
                db.session.commit()
                location_id = new_location.id
            ad.location_id = location_id

        # объявления администраторов публикуются сразу без модерации,
        # остальные - проходят проверку администратором
        if not current_user.is_admin:
            ad.assign_admin()
        
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

            # photo.data.save(os.path.join(ad_storage_path, photo_filename))

        return {}, 200
    return jsonify(form.errors), 400


@app.route('/images', methods=['get'])
def images():
    user_login = request.args.get('user')
    ad_id = request.args.get('ad')
    photo_number = request.args.get('photo')

    size_prefixes = {
        'origin': '',
        'small': app.config['PHOTO_SMALL_PREFIX'],
        'tiny': app.config['PHOTO_TINY_PREFIX']
    }

    size = request.args.get('size')
    size_prefix = (size_prefixes[size] if size else '')

    photo_filename = ''
    if user_login:
        # фото профиля
        photo_filename = glob(os.path.join(
            app.config['UPLOADS_FOLDER'],
            user_login,
            app.config['PROFILE_PHOTO_FILENAME'] + size_prefix + '.*'
        ))
    elif ad_id and photo_number:
        # фото объявления
        seller_login = Ad.query.filter_by(id=ad_id).first().seller.login
        photo_filename = glob(os.path.join(
            app.config['UPLOADS_FOLDER'],
            seller_login,
            ad_id,
            photo_number + size_prefix + '.*'
        ))

    if photo_filename:
        photo_filename = photo_filename[0]
        photo_filename = os.path.join(*(photo_filename.split(os.path.sep)[1:]))

        return redirect(photo_filename)
    
    # изображения по умолчанию
    if user_login:
        return redirect('static/img/profile_stock.svg')
    elif ad_id and photo_number:
        return redirect('static/img/car_stock.svg')

    return '', 404


@app.route('/ads/<int:ad_id>', methods=['get'])
@register_breadcrumb(app, '.ad', '',
                    dynamic_list_constructor=view_ad_dlc)
def ads(ad_id):
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


@app.route('/ads/<ad_id>/status/<status_id>', methods=['get','post'])
@login_required
def ad_status(ad_id, status_id):
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
        return redirect(url_for('ads', ad_id=ad_id))

    return {'error': 'Некорректный id объявления или статуса.'}, 405


@app.route('/ad_json/<ad_id>', methods=['get','post'])
def ad_json(ad_id):
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

@app.route('/ad', methods=['put'])
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
            ad.color_id = form.color.data
            ad.is_broken = form.is_broken.data
            ad.mileage = form.mileage.data
            ad.seller_id = current_user.id
            ad.price = form.price.data
            ad.description = form.description.data.strip()
            ad.status_id = AdStatus.ON_CHECKING
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


@app.route('/ad/<ad_id>', methods=['delete'])
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


@app.route('/user/<user_login>', methods=['get'])
@register_breadcrumb(app, '.user', '',
                    dynamic_list_constructor=view_user_dlc)
def open_user_page(user_login):
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

                user.password_hash = generate_password_hash(form.new_password.data)

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
