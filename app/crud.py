import logging
from typing import Union, List

from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from app.schemas import EmployeeModel, JobClass, Doctor, Nurse, Admin, OtherHCP, OutpatientSurgery, Facility, Office, \
    InsuranceCompany


def create_employee(session, employee_data, subclass_data):
    try:
        # Insert into Employee table
        employee_insert = text("""
            INSERT INTO Employee (SSN, fname, lname, salary, hire_date, job_class, address, facility_id)
            VALUES (:ssn, :fname, :lname, :salary, :hire_date, :job_class, :address, :facility_id);
        """)
        session.execute(employee_insert, employee_data)
        session.commit()

        # Execute the query to get the last inserted EMPID
        empid_query = session.execute(text("SELECT LAST_INSERT_ID();"))
        empid = None
        for row in empid_query:
            empid = row[0]  # Access the first column of the first row
            break  # Break after the first row to mimic fetchone behavior

        if empid is None:
            raise Exception("Failed to fetch the new employee ID.")

        # Prepare subclass-specific insert statement based on job_class
        if employee_data['job_class'] == 'Doctor':
            subclass_insert = text("""
                INSERT INTO Doctor (EMPID, speciality, bc_date)
                VALUES (:empid, :speciality, :bc_date);
            """)
        elif employee_data['job_class'] == 'Nurse':
            subclass_insert = text("""
                INSERT INTO Nurse (EMPID, certification)
                VALUES (:empid, :certification);
            """)
        elif employee_data['job_class'] == 'Admin':
            subclass_insert = text("""
                INSERT INTO Admin (EMPID, job_title)
                VALUES (:empid, :job_title);
            """)
        elif employee_data['job_class'] == 'OtherHCP':
            subclass_insert = text("""
                INSERT INTO OtherHCP (EMPID, job_title)
                VALUES (:empid, :job_title);
            """)
        else:
            return empid  # If no subclass, just return the EMPID

        subclass_data['empid'] = empid  # Include the EMPID in subclass data for insertion
        session.execute(subclass_insert, subclass_data)
        session.commit()

        return empid

    except SQLAlchemyError as e:
        session.rollback()  # Roll back the transaction on error
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")


def retrieve_all_employees(session):
    try:
        employee_query = text("""
            SELECT EMPID, SSN, fname, lname, salary, hire_date, job_class, address, facility_id
            FROM Employee;
        """)
        employee_result = session.execute(employee_query)

        result_list = []

        # Process each row as a tuple
        for emp in employee_result:
            emp_data = {
                'empid': emp[0],  # EMPID
                'ssn': emp[1],  # SSN
                'fname': emp[2],  # First Name
                'lname': emp[3],  # Last Name
                'salary': float(emp[4]),  # Salary
                'hire_date': emp[5],  # Hire Date
                'job_class': emp[6],  # Job Class
                'address': emp[7],  # Address
                'facility_id': emp[8]  # Facility ID
            }

            if emp[6] == JobClass.doctor.value:
                doctor_query = text("SELECT speciality, bc_date FROM Doctor WHERE EMPID = :empid")
                for doctor in session.execute(doctor_query, {'empid': emp[0]}):
                    result_list.append(Doctor(speciality=doctor[0], bc_date=doctor[1], **emp_data))

            elif emp[6] == JobClass.nurse.value:
                nurse_query = text("SELECT certification FROM Nurse WHERE EMPID = :empid")
                for nurse in session.execute(nurse_query, {'empid': emp[0]}):
                    result_list.append(Nurse(certification=nurse[0], **emp_data))

            elif emp[6] == JobClass.admin.value:
                admin_query = text("SELECT job_title FROM Admin WHERE EMPID = :empid")
                for admin in session.execute(admin_query, {'empid': emp[0]}):
                    result_list.append(Admin(job_title=admin[0], **emp_data))

            elif emp[6] == JobClass.otherhcp.value:
                otherhcp_query = text("SELECT job_title FROM OtherHCP WHERE EMPID = :empid")
                for otherhcp in session.execute(otherhcp_query, {'empid': emp[0]}):
                    result_list.append(OtherHCP(job_title=otherhcp[0], **emp_data))

        return result_list

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")


def create_appointment(session, patient_id, facility_id, doctor_id, date_time):
    try:
        # Get insurance_id from Patient
        insurance_query = text("SELECT insurance_id FROM Patient WHERE patient_id = :patient_id")
        insurance_result = session.execute(insurance_query, {'patient_id': patient_id}).fetchone()
        insurance_id = insurance_result[0] if insurance_result else None

        if not insurance_id:
            raise ValueError("No insurance found for patient")

        # Date only for the invoice
        invoice_date = date_time.date()

        # Check for existing invoice or create new one
        invoice_query = text("""
            SELECT invoice_id FROM Invoice
            WHERE insurance_id = :insurance_id AND date = :invoice_date
        """)
        invoice_result = session.execute(invoice_query,
                                         {'insurance_id': insurance_id, 'invoice_date': invoice_date}).fetchone()

        if invoice_result:
            invoice_id = invoice_result[0]
        else:
            insert_invoice = text("""
                INSERT INTO Invoice (date, total_cost, insurance_id)
                VALUES (:invoice_date, 0, :insurance_id)
            """)
            session.execute(insert_invoice, {'invoice_date': invoice_date, 'insurance_id': insurance_id})
            invoice_id = session.execute(text('SELECT LAST_INSERT_ID()')).scalar()

        # Insert into Appointments
        appointment_insert = text("""
            INSERT INTO Appointments (patient_id, facility_id, doctor_id, date_time)
            VALUES (:patient_id, :facility_id, :doctor_id, :date_time)
        """)
        session.execute(appointment_insert,
                        {'patient_id': patient_id, 'facility_id': facility_id, 'doctor_id': doctor_id,
                         'date_time': date_time})

        # Initialize InvoiceDetails
        invoice_details_insert = text("""
            INSERT INTO InvoiceDetails (invoice_id, cost, patient_id, facility_id, doctor_id, date_time)
            VALUES (:invoice_id, 0, :patient_id, :facility_id, :doctor_id, :date_time)
        """)
        session.execute(invoice_details_insert,
                        {'invoice_id': invoice_id, 'patient_id': patient_id, 'facility_id': facility_id,
                         'doctor_id': doctor_id, 'date_time': date_time})

        # Insert into Treats if not exists
        check_treats = text("""
            SELECT 1 FROM Treats WHERE patient_id = :patient_id AND doctor_id = :doctor_id
        """)
        treats_exists = session.execute(check_treats, {'patient_id': patient_id, 'doctor_id': doctor_id}).scalar()

        if not treats_exists:
            insert_treats = text("""
                INSERT INTO Treats (patient_id, doctor_id)
                VALUES (:patient_id, :doctor_id)
            """)
            session.execute(insert_treats, {'patient_id': patient_id, 'doctor_id': doctor_id})

        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to create appointment: {str(e)}")

def add_patient(session, patient_data):
    try:
        insert_query = text("""
            INSERT INTO Patient (fname, lname, primary_doc_id, insurance_id)
            VALUES (:fname, :lname, :primary_doc_id, :insurance_id);
        """)
        session.execute(insert_query, patient_data)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to add patient: {str(e)}")


def update_patient(session, patient_id, update_data):
    try:
        update_query = text("""
            UPDATE Patient
            SET fname = :fname, lname = :lname, primary_doc_id = :primary_doc_id, insurance_id = :insurance_id
            WHERE patient_id = :patient_id;
        """)
        session.execute(update_query, {**update_data, 'patient_id': patient_id})
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to update patient: {str(e)}")


def get_all_patients(session):
    try:
        select_query = text("""
            SELECT patient_id, fname, lname, primary_doc_id, insurance_id
            FROM Patient;
        """)
        result = session.execute(select_query)
        patients = []
        for row in result:
            patient = {
                'patient_id': row[0],  # Assuming result row can be accessed as dict
                'fname': row[1],
                'lname': row[2],
                'primary_doc_id': row[3],
                'insurance_id': row[4]
            }
            patients.append(patient)
        return patients
    except SQLAlchemyError as e:
        raise Exception(f"Failed to retrieve all patients: {str(e)}")


def get_patient(session, patient_id):
    try:
        # Define the SQL query to select a patient by ID
        select_query = text("""
            SELECT patient_id, fname, lname, primary_doc_id, insurance_id
            FROM Patient WHERE patient_id = :id;
        """)

        # Execute the query passing the patient_id
        result = session.execute(select_query, {'id': patient_id})

        # Initialize patient to None
        patient = None

        # Iterate through the result set
        for row in result:
            # Convert the first result into a dictionary and break the loop
            patient = {
                'patient_id': row[0],  # Access by index
                'fname': row[1],
                'lname': row[2],
                'primary_doc_id': row[3],
                'insurance_id': row[4]
            }
            break  # Only process the first row since patient_id should be unique

        return patient  # Return the patient dictionary or None if not found

    except SQLAlchemyError as e:
        # Proper error handling for database issues
        print(f"Failed to retrieve patient: {str(e)}")
        return None


def delete_patient(session, patient_id):
    try:
        delete_query = text("""
            DELETE FROM Patient WHERE patient_id = :patient_id;
        """)
        session.execute(delete_query, {'patient_id': patient_id})
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to delete patient: {str(e)}")


def get_all_doctors(session):
    try:
        # Constructing the SQL query
        query = text("SELECT EMPID, fname, lname FROM Employee WHERE job_class = 'Doctor';")

        # Executing the query
        result = session.execute(query)

        # Fetching all results
        doctors = []
        for row in result:
            # Create a dictionary for each doctor and append to the list
            doctor = {
                'EMPID': row[0],  # Accessing EMPID
                'fname': row[1],  # Accessing first name
                'lname': row[2]  # Accessing last name
            }
            doctors.append(doctor)

        return doctors

    except SQLAlchemyError as e:
        # Proper error handling
        print(f"Error accessing database: {e}")
        return []


def get_all_insurance_companies(session):
    # Placeholder SQL query
    query = text("SELECT insurance_id, name FROM InsuranceCompany;")
    result = session.execute(query)
    rtn_list = []
    for row in result:
        insurance_company = {"insurance_id": row[0], "name": row[1]}
        rtn_list.append(insurance_company)
    return rtn_list


def get_patient(session, patient_id):
    try:
        select_query = text("""
            SELECT patient_id, fname, lname, primary_doc_id, insurance_id
            FROM Patient
            WHERE patient_id = :patient_id;
        """)
        result = session.execute(select_query, {'patient_id': patient_id})
        patient = None
        for row in result:
            patient = {
                'patient_id': row[0],
                'fname': row[1],
                'lname': row[2],
                'primary_doc_id': row[3],
                'insurance_id': row[4]
            }
            break  # Since there should only be one record, break after the first iteration
        return patient
    except SQLAlchemyError as e:
        raise Exception(f"Failed to get patient details: {str(e)}")


def create_insurance_company(session, insurance_data):
    try:

        insurance_insert = text("""
             INSERT INTO InsuranceCompany (name,address)
             VALUES (:name,:address);
                            """)
        session.execute(insurance_insert, insurance_data)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()  # Roll back the transaction on error
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")


def retrieve_insurance_companies(session) -> List[InsuranceCompany]:
    try:
        # SQL query to fetch all insurance companies
        query = text("""
            SELECT insurance_id, name, address FROM InsuranceCompany;
        """)
        result = session.execute(query).fetchall()  # This returns a list of tuples

        # Convert tuples into list of InsuranceCompany models
        insurance_companies = [InsuranceCompany(insurance_id=company[0], name=company[1], address=company[2]) for
                               company in result]
        return insurance_companies

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")


def get_insurance_company_by_id(session, insurance_id):
    try:
        # Prepare the SQL query using text() for safe parameter binding
        query = text("SELECT insurance_id, name, address FROM InsuranceCompany WHERE insurance_id = :id")
        result = session.execute(query, {'id': insurance_id})

        if result is None:
            return None  # Return None if no insurance company is found

        # Convert the result tuple into a Pydantic model
        insurance_company = InsuranceCompany(
            insurance_id=result[0],
            name=result[1],
            address=result[2]
        )
        return insurance_company

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to fetch insurance company: {str(e)}")


def update_insurance_company_data(session, insurance_id, name, address):
    try:
        # Prepare the SQL update statement using text() for parameter safety
        update_stmt = text("""
            UPDATE InsuranceCompany
            SET name = :name, address = :address
            WHERE insurance_id = :insurance_id;
        """)
        ic("is my log showing____________________", {'insurance_id': insurance_id, 'name': name, 'address': address})
        session.execute(update_stmt, {'insurance_id': insurance_id, 'name': name, 'address': address})
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to update insurance company: {str(e)}")


def get_all_facility(session):
    query = text("SELECT facility_id, ftype FROM Facility")
    result = session.execute(query)
    rtn_list = []
    for value in result:
        ic("--- Summary Content Start ---")
        ic(value)
        rtn_list.append(value)
        ic("---Summary Content End ---\n")
    ic(rtn_list)
    return rtn_list


def create_facility(session, facility_data, subtype_data):
    try:
        # Insert into Facility table
        facility_insert = text("""
            INSERT INTO Facility (address, size, ftype)
            VALUES (:address, :size, :ftype);
        """)
        session.execute(facility_insert, facility_data)
        session.commit()

        # Execute the query to get the last inserted facility_id
        facility_id_query = session.execute(text("SELECT LAST_INSERT_ID();"))
        facility_id = None
        for row in facility_id_query:
            facility_id = row[0]  # Access the first column of the first row
            break  # Only need the first result

        if facility_id is None:
            raise Exception("Failed to fetch the new facility ID.")

        # Check facility type and insert into the corresponding subtype table
        if facility_data['ftype'] == 'Office':
            office_insert = text("""
                INSERT INTO Office (facility_id, office_count)
                VALUES (:facility_id, :office_count);
            """)
            subtype_data['facility_id'] = facility_id
            session.execute(office_insert, subtype_data)

        elif facility_data['ftype'] == 'OutpatientSurgery':
            surgery_insert = text("""
                INSERT INTO OutpatientSurgery (facility_id, room_count, description, p_code)
                VALUES (:facility_id, :room_count, :description, :p_code);
            """)
            subtype_data['facility_id'] = facility_id
            session.execute(surgery_insert, subtype_data)

        else:
            raise ValueError("Invalid facility type")

        session.commit()

    except SQLAlchemyError as e:
        session.rollback()  # Roll back the transaction on error
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")


def retrieve_facilities(session):
    try:
        # Query to fetch facilities with details from subtypes if available
        facilities_query = text("""
            SELECT 
                f.facility_id, 
                f.address, 
                f.size, 
                f.ftype,
                o.office_count,
                s.room_count, 
                s.description, 
                s.p_code
            FROM Facility f
            LEFT JOIN Office o ON f.facility_id = o.facility_id
            LEFT JOIN OutpatientSurgery s ON f.facility_id = s.facility_id;
        """)
        facilities_data = session.execute(facilities_query)

        result_list = []

        # Construct facility objects based on type and available data
        for facility in facilities_data:
            if facility[3] == 'Office' and facility[4] is not None:
                result_list.append({
                    'facility_id': facility[0],
                    'address': facility[1],
                    'size': facility[2],
                    'ftype': 'Office',
                    'office_count': facility[4]
                })
            elif facility[3] == 'OutpatientSurgery' and facility[5] is not None:
                result_list.append({
                    'facility_id': facility[0],
                    'address': facility[1],
                    'size': facility[2],
                    'ftype': 'Outpatient Surgery',
                    'room_count': facility[5],
                    'description': facility[6],
                    'p_code': facility[7]
                })
            else:
                # General facility data that doesn't match subtype criteria
                result_list.append({
                    'facility_id': facility[0],
                    'address': facility[1],
                    'size': facility[2],
                    'ftype': facility[3]
                })

        return result_list

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")


def search_appointments_db(session, patient_id=None, doctor_id=None, facility_id=None, start_date=None, end_date=None):
    query = """
        SELECT a.patient_id, a.doctor_id, a.facility_id, a.date_time, id.cost
        FROM Appointments a
        JOIN InvoiceDetails id ON a.patient_id = id.patient_id
                               AND a.facility_id = id.facility_id
                               AND a.doctor_id = id.doctor_id
                               AND a.date_time = id.date_time
        WHERE 1=1
    """
    params = {}
    if patient_id:
        query += " AND a.patient_id = :patient_id"
        params['patient_id'] = patient_id
    if doctor_id:
        query += " AND a.doctor_id = :doctor_id"
        params['doctor_id'] = doctor_id
    if facility_id:
        query += " AND a.facility_id = :facility_id"
        params['facility_id'] = facility_id
    if start_date:
        query += " AND a.date_time >= :start_date"
        params['start_date'] = start_date.strftime('%Y-%m-%d')
    if end_date:
        query += " AND a.date_time <= :end_date"
        params['end_date'] = end_date.strftime('%Y-%m-%d')

    result = session.execute(text(query), params)
    # Convert result to dictionary for easier handling in templates
    appointments = [
        {'patient_id': row[0], 'doctor_id': row[1], 'facility_id': row[2], 'date_time': row[3], 'cost': row[4]} for row
        in result]

    return appointments
def update_appointment_cost_db(session, patient_id, facility_id, doctor_id, date_time, new_cost):
    try:
        update_invoice_details = text("""
            UPDATE InvoiceDetails
            SET cost = :new_cost
            WHERE patient_id = :patient_id AND facility_id = :facility_id
              AND doctor_id = :doctor_id AND date_time = :date_time
        """)
        result = session.execute(update_invoice_details, {
            'new_cost': new_cost,
            'patient_id': patient_id,
            'facility_id': facility_id,
            'doctor_id': doctor_id,
            'date_time': date_time
        })
        print(f"Rows affected in InvoiceDetails: {result.rowcount}")  # Debugging line

        calculate_new_total = text("""
            UPDATE Invoice
            SET total_cost = (
                SELECT SUM(cost)
                FROM InvoiceDetails
                WHERE invoice_id IN (
                    SELECT invoice_id
                    FROM InvoiceDetails
                    WHERE patient_id = :patient_id AND facility_id = :facility_id
                      AND doctor_id = :doctor_id AND DATE(date_time) = DATE(:date_time)
                )
            )
            WHERE invoice_id IN (
                SELECT invoice_id
                FROM InvoiceDetails
                WHERE patient_id = :patient_id AND facility_id = :facility_id
                  AND doctor_id = :doctor_id AND DATE(date_time) = DATE(:date_time)
            )
        """)
        result = session.execute(calculate_new_total, {
            'patient_id': patient_id,
            'facility_id': facility_id,
            'doctor_id': doctor_id,
            'date_time': date_time
        })
        print(f"Rows affected in Invoice: {result.rowcount}")  # Debugging line

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during database operation: {str(e)}")
        raise
