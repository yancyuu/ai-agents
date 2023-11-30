# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import time

from fastapi import request

from common_sdk.logging.logger import logger
from common_sdk.util import id_generator, context
from service.base_responses import jsonify_response
from service import error_codes
from service import errors


class RequestMiddleWare:

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        context.set_message_uuid(id_generator.generate_common_id())
        context.set_request_timestamp(int(time.time()))
        return self.wsgi_app(environ, start_response)


def init_blueprint(app):
    blueprints = []      

    @app.errorhandler(404)
    def error_404(e):
        response = jsonify_response(status_response=error_codes.PAGE_NOT_FOUND)
        response.status = error_codes.PAGE_NOT_FOUND[0]
        return response

    @app.errorhandler(Exception)
    def error_handler(e):
        logger.exception(e)
        if isinstance(e, errors.Error):
            return jsonify_response(status_response=(e.errcode, e.errmsg))
        if issubclass(type(e), errors.Error):
            return jsonify_response(status_response=(e.errcode, e.errmsg))
        return jsonify_response(status_response=error_codes.SERVER_ERROR)

    @app.before_request
    def before_request():
        user_ip = request.headers.get("X-Real-IP", "0.0.0.0")
        if request.is_json:
            logger.info(f"user_ip {user_ip}: {request.json}")
        else:
            logger.info(f"user_ip{user_ip}")
        context.set_user_ip(user_ip)

    @app.after_request
    def response_json(response):
        """ 记录请求参数和返回的errcode和errmsg
        """
        try:
            record_interface_cost(request, response)
        except Exception as ex:
            logger.exception(ex, stacklevel=3)
        return response

    def record_interface_cost(request, response):
        now = time.time()
        request_timestamp = context.get_request_timestamp()
        interface_cost = now - float(request_timestamp)
        url = request.url_rule
        user_ip = request.headers.get("X-Real-Ip", None)
        logger.info(f"{user_ip} 接口耗时: {interface_cost} url: {url}")

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    app.wsgi_app = RequestMiddleWare(app.wsgi_app)
