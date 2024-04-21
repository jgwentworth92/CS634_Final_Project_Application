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

        # Fetch the last inserted EMPID
        empid = session.execute(text("SELECT LAST_INSERT_ID();")).scalar()

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

        # Add subclass-specific data and execute insertion
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
        employees = session.execute(employee_query).fetchall()

        result_list = []

        # Process each tuple representing an employee
        for emp in employees:
            emp_obj = None
            emp_data = {
                'empid': emp[0], 'ssn': emp[1], 'fname': emp[2],
                'lname': emp[3], 'salary': float(emp[4]), 'hire_date': emp[5],
                'job_class': emp[6], 'address': emp[7], 'facility_id': emp[8]
            }

            if emp[6] == JobClass.doctor.value:
                doctor_query = text("""
                    SELECT speciality, bc_date 
                    FROM Doctor WHERE EMPID = :empid
                """)
                doctor_data = session.execute(doctor_query, {'empid': emp[0]}).fetchone()
                if doctor_data:
                    emp_obj = Doctor(
                        speciality=doctor_data[0], bc_date=doctor_data[1], **emp_data
                    )
            elif emp[6] == JobClass.nurse.value:
                nurse_query = text("""
                    SELECT certification 
                    FROM Nurse WHERE EMPID = :empid
                """)
                nurse_data = session.execute(nurse_query, {'empid': emp[0]}).fetchone()
                if nurse_data:
                    emp_obj = Nurse(
                        certification=nurse_data[0], **emp_data
                    )
            elif emp[6] == JobClass.admin.value:
                admin_query = text("""
                    SELECT job_title 
                    FROM Admin WHERE EMPID = :empid
                """)
                admin_data = session.execute(admin_query, {'empid': emp[0]}).fetchone()
                if admin_data:
                    emp_obj = Admin(
                        job_title=admin_data[0], **emp_data
                    )
            elif emp[6] == JobClass.otherhcp.value:
                otherhcp_query = text("""
                    SELECT job_title 
                    FROM OtherHCP WHERE EMPID = :empid
                """)
                otherhcp_data = session.execute(otherhcp_query, {'empid': emp[0]}).fetchone()
                if otherhcp_data:
                    emp_obj = OtherHCP(
                        job_title=otherhcp_data[0], **emp_data
                    )
            else:
                continue  # Skip if the job class is not recognized

            result_list.append(emp_obj)
        for value in result_list:
            ic(f"return values:{value}")
        return result_list

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")


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
        result = session.execute(query, {'id': insurance_id}).fetchone()

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
        ic("is my log showing____________________",{'insurance_id': insurance_id, 'name': name, 'address': address})
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

        # Get the last inserted facility_id
        facility_id = session.execute(text("SELECT LAST_INSERT_ID();"))
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

        # Commit the transaction
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()  # Roll back the transaction on error
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")


from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


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
