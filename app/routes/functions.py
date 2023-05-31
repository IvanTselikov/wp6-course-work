from flask import request

from flask_login import current_user
from sqlalchemy import or_, and_, func

from app import app
from app.models import Ad, Modification, Serie, Generation, Model, Mark,\
    TransportType, Color, Location, User, AdStatus

from PIL import Image
import os
from glob import glob
import locale


def set_location_cookie(response):
    if current_user.is_authenticated and current_user.location and not\
    (request.args.get('page') and int(request.args.get('page')) > 1 or\
    request.cookies.get('page') and int(request.cookies.get('page')) > 1 or\
    request.cookies.get('is_filtered') or request.cookies.get('search')):
        response.set_cookie('is_filtered', '1')
        response.set_cookie('location', current_user.location.name)


def parse_int_or_skip(s, default=None):
    try:
        return int(s)
    except:
        return default or s


def get_filtered_ads(filter_params):
    # разбиваем запрос в поисковой строке на отдельные слова
    search_params = (
        list(map(lambda s: s.lower(), filter_params.get('search').split()))
            if filter_params.get('search') else []
    )

    ads = Ad.query\
        .filter(and_(
            # отображаем только открытые объявления других пользователей
            Ad.seller_id != current_user.id if current_user.is_authenticated else True,
            Ad.status_id == AdStatus.OPENED
        ))\
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

    return ads


def upload_photo(file_storage, path_origin, path_small=None, path_tiny=None):
    # сохранение оригинального размера
    file_storage.save(path_origin)

    # сохранение уменьшенного изображения
    if path_small:
        im = Image.open(path_origin)
        im.thumbnail((500,500), Image.Resampling.LANCZOS)
        im.save(path_small)

    # сохранение маленького изображения
    if path_tiny:
        im = Image.open(path_origin)
        im.thumbnail((100,100), Image.Resampling.LANCZOS)
        im.save(path_tiny)


def view_ad_dlc(*args, **kwargs):
    ad_id = request.view_args['ad_id']
    ad = Ad.query.get(ad_id)
    return [
        {
            'text': '{} {}, {}'.format(
                ad.car.serie.generation.model.mark.name,
                ad.car.serie.generation.model.name,
                ad.release_year
            ),
            'url': ''
        }
    ]


def view_user_dlc(*args, **kwargs):
    user_login = request.view_args['user_login']
    user = User.query.filter_by(login=user_login).first()
    return [
        {
            'text': user_login,
            'url': ''
        }
    ]


def remove_ad_photo(ad, photo_number):
    photo_filenames = glob(os.path.join(
        app.config['UPLOADS_FOLDER'],
        ad.seller.login,
        str(ad.id),
        '{}.*'.format(photo_number)
    ))

    for filename in photo_filenames:
        os.remove(filename)


def remove_profile_photo(user):
    photo_filenames = glob(os.path.join(
        app.config['UPLOADS_FOLDER'],
        user.login,
        '{}.*'.format(app.config['PROFILE_PHOTO_FILENAME'])
    ))

    for filename in photo_filenames:
        os.remove(filename)


def format_registration_date(registration_date):
    locale.setlocale(locale.LC_TIME, 'ru_RU')

    return registration_date.strftime('%d %b %Y').title()
