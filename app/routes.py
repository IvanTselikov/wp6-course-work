# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for
from flask import jsonify, request
from app import app, db
from app.forms import LoginForm, SignupForm, AdForm

from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse

from app.models import User, Mark, Model, Generation, Serie, Modification, Color
from flask_login import current_user, login_user, logout_user
from sqlalchemy import or_, not_

import os
import pathlib
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
        kwargs.update({'ad_form': ad_form})
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})

    return render_template('index.html', **kwargs)


@app.route('/login', methods=['POST'])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))
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
    form = SignupForm()
    if form.validate():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            patronymic=form.patronymic.data,
            login=form.signup_login.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            is_admin=0
        )

        user.set_location(form.location.data)
        user.set_password(form.signup_password.data)

        db.session.add(user)
        db.session.commit()
        login_user(user)

        # создание хранилища для фото пользователя
        user_storage_path = os.path.join(app.config['UPLOADS_FOLDER'], user.login)
        os.makedirs(user_storage_path, exist_ok=True)

        # сохранение фото профиля
        photo_filename = secure_filename(form.photo.data.filename)
        _, file_extension = os.path.splitext(photo_filename)
        photo_filename = '{}.{}'.format(app.config['PROFILE_PHOTO_FILENAME'], file_extension)
        form.photo.data.save(os.path.join(user_storage_path, photo_filename))

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
        return jsonify({ 'yearBegin': generation.year_begin, 'yearEnd': generation.year_end })
    return {}, 404

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
