from datetime import timedelta, datetime

from faker import Faker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import random
from app.Database import db
from crud_helpers.appointment_crud import create_appointment, search_appointments_db, update_appointment_cost_db
from crud_helpers.employee_crud import create_employee, get_all_doctors

from crud_helpers.facility_crud import create_facility, retrieve_facilities
from crud_helpers.insurance_crud import create_insurance_company, retrieve_insurance_companies
from crud_helpers.patient_crud import create_patient, get_all_patients


# Assuming db.get_db() and other necessary imports are handled elsewhere

def populate_database():
    fake = Faker()
    db.connect()
    # Create a session
    session = db.get_db()

    try:
        # Generate data for 10 facilities
        for _ in range(10):
            facility_type = random.choice(['Office', 'OutpatientSurgery'])
            facility_data = {
                'address': fake.address(),
                'size': random.randint(1000, 5000),  # Example size in square feet
                'ftype': facility_type
            }

            if facility_type == 'Office':
                subtype_data = {
                    'office_count': random.randint(1, 10)
                }
            else:
                subtype_data = {
                    'room_count': random.randint(1, 5),
                    'description': fake.text(),
                    'p_code': fake.postcode()
                }

            create_facility(session, facility_data, subtype_data)
            insurance_data = {
                'name': fake.company(),
                'address': fake.address()
            }
            create_insurance_company(session, insurance_data)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.disconnect()


def populate_employees():
    fake = Faker()
    db.connect()

    session = db.get_db()

    try:
        facilities = retrieve_facilities(session)
        if not facilities:
            raise Exception("No facilities available to assign employees.")

        for _ in range(40):  # Generate data for 20 employees
            facility = random.choice(facilities)
            job_class = random.choice(['Doctor', 'Nurse', 'Admin', 'OtherHCP'])
            employee_data = {
                'ssn': random.randint(100000000, 999999999),
                'fname': fake.first_name(),
                'lname': fake.last_name(),
                'salary': random.randint(30000, 130000),
                'hire_date': fake.date_between(start_date='-5y', end_date='today'),
                'job_class': job_class,
                'address': fake.address(),
                'facility_id': facility['facility_id']
            }

            subclass_data = {}
            if job_class == 'Doctor':
                subclass_data = {'speciality': fake.job(),
                                 'bc_date': fake.date_between(start_date='-10y', end_date='today')}
            elif job_class == 'Nurse':
                subclass_data = {'certification': 'Certified Registered Nurse Anesthetist'}
            elif job_class == 'Admin':
                subclass_data = {'job_title': 'Administrative Assistant'}
            elif job_class == 'OtherHCP':
                subclass_data = {'job_title': fake.job()}

            empid = create_employee(session, employee_data, subclass_data)
            print(f"Created employee with EMPID: {empid}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.disconnect()

def populate_patients():
    fake = Faker()
    db.connect()
    session = db.get_db()

    try:
        doctors = get_all_doctors(session)
        if not doctors:
            raise Exception("No doctors available.")

        insurance_companies = retrieve_insurance_companies(session)
        if not insurance_companies:
            raise Exception("No insurance companies available.")

        # Generate data for 20 patients
        for _ in range(400):
            doctor = random.choice(doctors)
            insurance_company = random.choice(insurance_companies)
            patient_data = {
                'fname': fake.first_name(),
                'lname': fake.last_name(),
                'primary_doc_id': doctor['EMPID'],
                'insurance_id': insurance_company['insurance_id']
            }

            create_patient(session, patient_data)
            print(f"Created patient: {patient_data['fname']} {patient_data['lname']}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.disconnect()

def populate_appointments():
    fake = Faker()
    db.connect()
    session = db.get_db()

    try:
        patients = get_all_patients(session)
        doctors = get_all_doctors(session)
        facilities = retrieve_facilities(session)

        if not patients or not doctors or not facilities:
            raise Exception("Missing entities required to create appointments.")

        # Generate data for 20 appointments
        for _ in range(200):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            facility = random.choice(facilities)
            date_time = datetime.now() + timedelta(days=random.randint(1, 30))
            description = fake.sentence()

            create_appointment(session, patient['patient_id'], facility['facility_id'], doctor['EMPID'], date_time, description)
            print(f"Created appointment for patient {patient['fname']} {patient['lname']} at {date_time}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.disconnect()
def update_all_appointments_costs():
    db.connect()
    session = db.get_db()
    try:
        appointments = search_appointments_db(session)
        for appointment in appointments:
            new_cost = random.randint(100, 500)  # Example of new cost generation
            update_appointment_cost_db(session, appointment['patient_id'], appointment['facility_id'], appointment['doctor_id'], appointment['date_time'], new_cost)

    except Exception as e:
        print(f"An error occurred while updating appointment costs: {str(e)}")
    finally:
        db.disconnect()
if __name__ == "__main__":
    populate_database()
    populate_employees()
    populate_patients()
    populate_appointments()
    update_all_appointments_costs()
