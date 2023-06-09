from flask import request, redirect, url_for, make_response, jsonify, flash

from app import app
from app.forms import LoginForm
from app.models import User

from werkzeug.urls import url_parse

from flask_login import current_user, login_user

from .functions import set_location_cookie


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

            # при входе в аккаунт отображаются только объявления из региона пользователя
            response = make_response(redirect(url_for('index')))
            set_location_cookie(response)

            return response
    return jsonify(form.errors), 400
