
# Core Flask imports
from flask import Flask

from app import routes
# Third-party imports
from app.Database import db, create_facility_tables, create_employee_tables, create_employee_sublcass_tables, \
    create_insurance_tables, create_treats_tables, create_patient_table, create_appointments_tables, \
    create_invoice_tables

# App imports

db_manager = db


def create_app():
    app = Flask(__name__)

    db_manager.connect()
    session = db.get_db()
    create_facility_tables(session)
    create_employee_tables(session)
    create_employee_sublcass_tables(session)
    create_insurance_tables(session)
    create_patient_table(session)
    create_treats_tables(session)
    create_appointments_tables(session)
    create_invoice_tables(session)


    app.register_blueprint(routes.bp)

    return app
