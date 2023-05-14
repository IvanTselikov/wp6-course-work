# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for
from flask import jsonify, request

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


@app.route('/')
@app.route('/index')
@register_breadcrumb(app, '.', 'Главная')
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

    filter_params = { k: parse_int_or_skip(v) for k, v in request.args.items() }

    # значения по умолчанию для пропущенных параметров
    filter_params.update({
        'page': parse_int_or_skip(request.args.get('page'), default=1),
        'per_page': parse_int_or_skip(request.args.get('per_page'), default=10),
    })

    if current_user.is_authenticated \
        and current_user.location\
        and not filter_params.keys() - ['page', 'per_page']:
        # по умолчанию - объявления в текущем регионе
        filter_params.update({ 'location': current_user.location.name })
    
    # разбиваем запрос в поисковой строке на отдельные слова
    search_params = (
        list(map(lambda s: s.lower(), filter_params.get('search').split()))
            if filter_params.get('search') else []
    )
    
    ads = Ad.query\
            .join(Modification).join(Serie).join(Generation)\
            .join(Model).join(Mark).join(TransportType)\
            .join(Color, isouter=True).join(Location, isouter=True)\
            .filter(and_(
                # фильтрация по запросу в поисковой строке
                *[or_(
                    func.lower(TransportType.name) == param,
                    func.lower(Mark.name) == param,
                    func.lower(Mark.name_rus) == param,
                    func.lower(Model.name) == param,
                    func.lower(Model.name_rus) == param,
                    func.lower(Generation.name) == param,
                    func.lower(Serie.name) == param,
                    func.lower(Modification.name) == param,
                    func.lower(Location.name) == param,
                    Ad.release_year == param
                ) for param in search_params]
            ))\
            .filter(and_(
                # фильтрация по основным параметрам поиска
                (Modification.id == filter_params.get('modification') 
                    if filter_params.get('modification') else True),

                (Serie.id == filter_params.get('serie')
                    if filter_params.get('serie') else True),

                (Generation.id == filter_params.get('generation')
                    if filter_params.get('generation') else True),
                    
                (Model.id == filter_params.get('model')
                    if filter_params.get('model') else True),
            
                (Mark.id == filter_params.get('mark')
                    if filter_params.get('mark') else True),
                
                (TransportType.id == filter_params.get('transport_type')
                    if filter_params.get('transport_type') else True)
            ))\
            .filter(and_(
                # фильтрация по дополнительным параметрам поиска
                (Color.id == filter_params.get('color')
                    if filter_params.get('color') else True),

                (Ad.price >= filter_params.get('price_begin')
                    if filter_params.get('price_begin') else True),
                
                (Ad.price <= filter_params.get('price_end')
                    if filter_params.get('price_end') else True),

                (Ad.release_year >= filter_params.get('release_year_begin')
                    if filter_params.get('release_year_begin') else True),
                
                (Ad.release_year <= filter_params.get('release_year_end')
                    if filter_params.get('release_year_end') else True),

                (Ad.mileage >= filter_params.get('mileage_begin')
                    if filter_params.get('mileage_begin') else True),
                
                (Ad.mileage <= filter_params.get('mileage_end')
                    if filter_params.get('mileage_end') else True),

                (Ad.owners_count >= filter_params.get('owners_count_begin')
                    if filter_params.get('owners_count_begin') else True),

                (Ad.owners_count <= filter_params.get('owners_count_end')
                    if filter_params.get('owners_count_end') else True),
                
                (Ad.is_broken == filter_params.get('is_broken')
                    if filter_params.get('is_broken') in [0,1] else True),
                
                (Location.name == filter_params.get('location')
                    if filter_params.get('location') else True),
            ))\
            .order_by(Ad.updated_at.desc())\
            .paginate(
                page=filter_params.get('page'),
                per_page=filter_params.get('per_page'),
                error_out=False
    )

    if current_user.is_authenticated:
        ads_section_header = 'Рекомендуемые объявления'
    else:
        ads_section_header = 'Новые объявления на сайте'

    if request.args.get('search'):
        ads_section_header = 'Результаты поиска по запросу: "{}"'.format(
            request.args.get('search').strip()
        )

    kwargs.update({
        'filters_form': filters_form,
        'ads_section_header': ads_section_header,
        'ads': ads
    })

    return render_template('index.html', **kwargs)
    

@app.route('/filter', methods=['post'])
def filter():
    filters_form = FiltersForm()
    print(filters_form.data)
    if filters_form.validate():
        return {}, 200
    return jsonify(filters_form.errors), 400


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
        
        ad_form = AdForm()
        kwargs.update({ 'ad_form': ad_form })
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})

    filters_form = FiltersForm()
    edit_ad_form = AdForm()
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
    form = AdForm()
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
