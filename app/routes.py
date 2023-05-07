# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for
from flask import jsonify, request
from app import app, db
from app.forms import LoginForm, SignupForm, AdForm, FiltersForm
from app.functions import *

from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse

from app.models import User, Mark, Model, Generation, Serie, Modification, Color, Location, Ad
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_

import os
from glob import glob


@app.route('/')
@app.route('/index')
def index():
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
        
        ad_form = AdForm()
        kwargs.update({ 'ad_form': ad_form })
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})

    filters_form = FiltersForm()


    try:
        page = int(request.args.get('page'))
    except:
        page = 1


    ads = Ad.query.filter_by().order_by(Ad.updated_at.desc()).paginate(
        page=page, per_page=1, error_out=False
    )

    kwargs.update({
        'filters_form': filters_form,
        'ads_section_header': 'Новые объявления на сайте',
        'ads': ads
    })
    return render_template('index.html', **kwargs)


@app.route('/login', methods=['POST'])
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
            return redirect(next_page)
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
    generation = Generation.query.filter_by(id=generation_id).first()

    if generation:
        year_begin = generation.year_begin or EARLIEST_RELEASE_YEAR
        year_end = generation.year_end or get_current_year()
    else:
        return {}, 404

    # form = request.args.get('form')
    # if form:
    #     if form == 'createAd':  # TODO: в константы
    #         form = AdForm()
    #     elif form == 'filters':
    #         form = FiltersForm()
    #     year_begin, year_end = form.change_release_year_limits(year_begin, year_end)

    return jsonify({ 'yearBegin': year_begin, 'yearEnd': year_end })


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
    form = AdForm()
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
        photos = list(
            filter(
                lambda f: f.data.filename,
                [form.photo_1, form.photo_2, form.photo_3]
            )
        )
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
