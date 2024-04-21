import logging

# Core Flask imports
from flask import Flask

from app import routes
# Third-party imports
from app.Database import db, create_facility_tables, create_employee_tables, create_employee_sublcass_tables, \
    create_insurance_tables, create_treats_tables, create_patient_table, create_appointments_tables, \
    create_invoice_tables
from flask_bootstrap import Bootstrap5

from app.crud import get_all_facility
from app.utils.common import setup_logging

# App imports

db_manager = db
setup_logging()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_really_secret_key_here'
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


    bootstrap = Bootstrap5(app)
    app.register_blueprint(routes.bp)

    return app
