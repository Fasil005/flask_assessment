from flask import jsonify


def format_response(data=None, status_code=200, message='Success'):
    response = {
        'status_code': status_code,
        'message': message,
        'data': data
    }
    return jsonify(response)