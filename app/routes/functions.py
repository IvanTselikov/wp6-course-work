from flask import request, url_for

from flask_login import current_user
from sqlalchemy import or_, and_, func

from app.models import Ad, Modification, Serie, Generation, Model, Mark,\
    TransportType, Color, Location
from app.forms import FiltersForm


def set_location_cookie(response):
    if current_user.location and not\
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

    result_header = 'Новые объявления на сайте'

    if filter_params.get('search'):
        result_header = 'Результаты поиска по запросу: "{}"'.format(
            filter_params.get('search').strip()
        )

    return ads, result_header

def set_location_recommendations(response):
    if not (request.cookies.get('is_filtered') or request.cookies.get('search')):
        r
        set_location_cookie(response)
