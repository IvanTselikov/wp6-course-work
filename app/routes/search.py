from flask import request, redirect, url_for, make_response
from app import app


@app.route('/search', methods=['post'])
def search():
    response = make_response(redirect(url_for('index')))

    response.set_cookie('search', request.form.get('search'))
    response.set_cookie('page', '', 0)

    return response
