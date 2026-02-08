from flask import jsonify


def error_response(message, code="BAD_REQUEST", error="Bad Request", status=400):
    return jsonify(
        {
            "error": error,
            "message": message,
            "code": code,
        }
    ), status
