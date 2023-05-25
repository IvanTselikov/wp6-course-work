from flask import redirect, url_for, make_response, jsonify

from app import app
from app.forms import FiltersForm


@app.route('/filters', methods=['post'])
def filters():
    response = make_response(redirect(url_for('index')))

    filters_form = FiltersForm()
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
        # ошибки на форме
        return jsonify(filters_form.errors), 400

    response.set_cookie('page', '', 0)
    return response
