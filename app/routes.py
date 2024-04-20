from flask import Blueprint

from app.views import error_views, static_views
from app.Database import db


bp = Blueprint('routes', __name__)




# alias
# Request management
@bp.before_app_request
def before_request():
    db.connect()


@bp.teardown_app_request
def shutdown_session(response_or_exc):

    db.disconnect()


# Error views
bp.register_error_handler(404, error_views.not_found_error)

bp.register_error_handler(500, error_views.internal_error)

# Public views
bp.add_url_rule("/", view_func=static_views.index)
