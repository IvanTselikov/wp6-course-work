from flask import redirect
from flask import jsonify, request

from app import app
from app.models import Mark, Model, Generation, Serie, Modification,\
    Color, Location, Ad

from sqlalchemy import or_

import os
from glob import glob
from datetime import datetime as dt


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
        'yearBegin': { 'value': app.config['MIN_CAR_RELEASE_YEAR'], 'isDefault': True },
        'yearEnd': { 'value': dt.now().year, 'isDefault': True },
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
