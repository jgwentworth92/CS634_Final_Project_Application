from flask import Blueprint

from app.views import error_views, static_views, employee, facility, insurance_companies, patient_management, \
    appointment_management
from app.Database import db

bp = Blueprint('routes', __name__)

# Database connection management
@bp.before_app_request
def before_request():
    db.connect()

@bp.teardown_app_request
def shutdown_session(response_or_exc):
    db.disconnect()

# Error handling
bp.register_error_handler(404, error_views.not_found_error)
bp.register_error_handler(500, error_views.internal_error)

# Public views
bp.add_url_rule("/", view_func=static_views.index)
bp.add_url_rule("/add_employee/<job_class>", view_func=employee.add_employee, methods=['GET', 'POST'])
bp.add_url_rule('/add_facility/<ftype>', view_func=facility.add_facility, methods=['GET', 'POST'])
bp.add_url_rule('/add_insurance_company', view_func=insurance_companies.add_insurance_company, methods=['GET', 'POST'])
bp.add_url_rule("/view_employees", view_func=employee.view_employees, methods=['GET', 'POST'])
bp.add_url_rule('/view_facility', view_func=facility.view_facilities, methods=['GET', 'POST'])
bp.add_url_rule('/view_insurance_companies', view_func=insurance_companies.view_insurance_companies, methods=['GET', 'POST'])
bp.add_url_rule('/update_insurance_company/<insurance_id>',view_func=insurance_companies.update_insurance_company,methods=['GET', 'POST'])
bp.add_url_rule('/add_patient_record',view_func=patient_management.add_patient_record, methods=['GET', 'POST'])
bp.add_url_rule('/view_patient_list',view_func=patient_management.view_patient_list, methods=['GET', 'POST'])
bp.add_url_rule('/edit_patient/<patient_id>',view_func=patient_management.edit_patient,methods=['GET', 'POST'])
bp.add_url_rule('/delete_patient_record/<patient_id>',view_func=patient_management.delete_patient_record,methods=['GET', 'POST'])
bp.add_url_rule('/make_appointment',view_func=appointment_management.make_appointment,methods=['GET', 'POST'])
bp.add_url_rule('/search_appointments',view_func=appointment_management.search_appointments,methods=['GET', 'POST'])
bp.add_url_rule('/update_cost/<int:patient_id>/<int:facility_id>/<int:doctor_id>/<date_time>',view_func=appointment_management.update_cost, methods=['GET', 'POST'])
bp.add_url_rule('/edit_appointment/<int:patient_id>/<int:facility_id>/<int:doctor_id>/<date_time>',view_func=appointment_management.edit_appointment, methods=['GET', 'POST'])
bp.add_url_rule('/daily_invoices',view_func=appointment_management.daily_invoices,methods=['GET', 'POST'])
bp.add_url_rule('/delete_insurance_company/<insurance_id>',view_func=insurance_companies.delete_insurance_company,methods=['GET', 'POST'])
bp.add_url_rule('/update_facility/<int:surgery>/<int:office>',view_func=facility.update_facility,methods=['GET', 'POST'])
bp.add_url_rule('/update_employee/<int:employee_id>/<string:job_class>',view_func=employee.update_employee,methods=['GET', 'POST'])
