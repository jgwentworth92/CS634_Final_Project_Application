import logging
from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session


from sqlalchemy.exc import SQLAlchemyError

from app.schemas import EmployeeModel, JobClass, Doctor, Nurse, Admin, OtherHCP


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
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def retrieve_all_employees(session):
    try:
        employee_query = text("""
            SELECT EMPID, SSN, fname, lname, salary, hire_date, job_class, address, facility_id
            FROM Employee;
        """)
        employees = session.execute(employee_query).fetchall()

        result_list = []

        for emp in employees:
            emp_data = {
                'ssn': emp.SSN,
                'fname': emp.fname,
                'lname': emp.lname,
                'salary': emp.salary,
                'hire_date': emp.hire_date,
                'job_class': emp.job_class,
                'address': emp.address,
                'facility_id': emp.facility_id
            }
            emp_obj = EmployeeModel(**emp_data)
            subclass_data = {}

            if emp.job_class == JobClass.doctor.value:
                doctor_data = session.execute(text("SELECT speciality, bc_date FROM Doctor WHERE EMPID = :empid"), {'empid': emp.EMPID}).fetchone()
                if doctor_data:
                    subclass_data = {'empid': emp.EMPID, 'speciality': doctor_data.speciality, 'bc_date': doctor_data.bc_date}
                    emp_obj.subclass = Doctor(**subclass_data)
            elif emp.job_class == JobClass.nurse.value:
                nurse_data = session.execute(text("SELECT certification FROM Nurse WHERE EMPID = :empid"), {'empid': emp.EMPID}).fetchone()
                if nurse_data:
                    subclass_data = {'empid': emp.EMPID, 'certification': nurse_data.certification}
                    emp_obj.subclass = Nurse(**subclass_data)
            elif emp.job_class == JobClass.admin.value:
                admin_data = session.execute(text("SELECT job_title FROM Admin WHERE EMPID = :empid"), {'empid': emp.EMPID}).fetchone()
                if admin_data:
                    subclass_data = {'empid': emp.EMPID, 'job_title': admin_data.job_title}
                    emp_obj.subclass = Admin(**subclass_data)
            elif emp.job_class == JobClass.otherhcp.value:
                otherhcp_data = session.execute(text("SELECT job_title FROM OtherHCP WHERE EMPID = :empid"), {'empid': emp.EMPID}).fetchone()
                if otherhcp_data:
                    subclass_data = {'empid': emp.EMPID, 'job_title': otherhcp_data.job_title}
                    emp_obj.subclass = OtherHCP(**subclass_data)

            result_list.append(emp_obj)
        ic(f'return data{result_list}')
        return result_list

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")

def create_insurance_company(session,insurance_data):
    try:

        insurance_insert = text("""
             INSERT INTO InsuranceCompany (name,address)
             VALUES (:name,:address);
                            """)
        session.execute(insurance_insert,insurance_data)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()  # Roll back the transaction on error
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")



def get_employee(session, empid):
    sql_query = text("SELECT * FROM Employee WHERE EMPID = :empid")
    result = session.execute(sql_query, {'empid': empid}).fetchone()
    return result


def update_employee(session, empid, update_data):
    update_statements = []
    for key, value in update_data.items():
        update_statements.append(f"{key} = :{key}")
    update_query = "UPDATE Employee SET " + ", ".join(update_statements) + " WHERE EMPID = :empid"
    session.execute(text(update_query), {**update_data, 'empid': empid})
    session.commit()


def delete_employee(session, empid):
    delete_query = text("DELETE FROM Employee WHERE EMPID = :empid")
    session.execute(delete_query, {'empid': empid})
    session.commit()

def get_all_facility(session):
    query = text("SELECT facility_id, ftype FROM Facility")
    result = session.execute(query)
    rtn_list=[]
    for value in result:
        ic("--- Summary Content Start ---")
        ic(value)
        rtn_list.append(value)
        ic("---Summary Content End ---\n")
    ic( rtn_list)
    return rtn_list


from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def create_facility(session, facility_data, subtype_data):
    try:
        # Insert into Facility table
        facility_insert = text("""
            INSERT INTO Facility (address, size, ftype)
            VALUES (:address, :size, :ftype);
        """)
        session.execute(facility_insert, facility_data)

        # Get the last inserted facility_id
        facility_id = session.execute(text("SELECT LAST_INSERT_ID();")).scalar()

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
