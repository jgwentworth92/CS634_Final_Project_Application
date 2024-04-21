from flask import Blueprint

from app.views import error_views, static_views, employee, facility, insurance_companies
from app.Database import db
from app.views.insurance_companies import add_insurance_company

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
bp.add_url_rule("/add_employee/<job_class>", view_func=employee.add_employee, methods=['GET', 'POST'])
bp.add_url_rule('/add_facility/<ftype>',view_func=facility.add_facility, methods=['GET', 'POST'])
bp.add_url_rule('/add_insurance_company',view_func=insurance_companies.add_insurance_company, methods=['GET', 'POST'])

