import logging
from typing import Union, List

from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError


from app.schemas import EmployeeModel, JobClass, Doctor, Nurse, Admin, OtherHCP, OutpatientSurgery, Facility, Office, \
    InsuranceCompany


def select_employee_by_id(session, employee_id):
    try:
        # Prepare the SQL query using text() for safe parameter binding
        query = text("SELECT SSN, fname, lname, salary, hire_date, job_class, address, facility_id \
                     FROM Employee WHERE EMPID = :employee_id")
        result = session.execute(query, {'employee_id': employee_id})
        results_as_dict = result.mappings().all()
        results_as_dict = dict(results_as_dict[0])
        print("\n\n", results_as_dict, "\n\n")

        if result is None:
            return None 

        employee = EmployeeModel(
            SSN=results_as_dict['SSN'],
            fname=results_as_dict['fname'],
            lname=results_as_dict['lname'],
            salary=results_as_dict['salary'],
            hire_date=results_as_dict['hire_date'],
            job_class=results_as_dict['job_class'],
            address=results_as_dict['address'],
            facility_id=results_as_dict['facility_id']
        )
        return employee

    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to fetch insurance company: {str(e)}")

# =========================
# CRUD operations for Create
# =========================
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


# =========================
# CRUD operations for Retrieve
# =========================

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


# ==========================
# CRUD operations for Update
# ==========================

def update_employee_entry(session, employee_id, job_class, employee_data, subclass_data):
    print("\n\n", employee_data, "\n\n")
    print("\n\n", subclass_data, "\n\n")
    employee_data['employee_id'] = employee_id
    subclass_data['employee_id'] = employee_id
    update_query = text("""UPDATE Employee SET SSN=:ssn,fname=:fname,lname=:lname,salary=:salary,\
                        hire_date=:hire_date,job_class=:job_class,address=:address,facility_id=:facility_id \
                        WHERE EMPID=:employee_id;
    """)
    session.execute(update_query, employee_data)
    if job_class=='Nurse':
        update_query = text("""UPDATE Nurse SET certification=:certification \
                        WHERE EMPID=:employee_id;
    """)
        session.execute(update_query, subclass_data)
    elif job_class=='Doctor':
        update_query = text("""UPDATE Doctor SET speciality=:speciality, bc_date=:bc_date \
                        WHERE EMPID=:employee_id;
    """)
        session.execute(update_query, subclass_data)
    elif job_class=='OtherHCP':
        update_query = text("""UPDATE OtherHCP SET job_title=:job_title \
                        WHERE EMPID=:employee_id;
    """)
        session.execute(update_query, subclass_data)
    elif job_class=='Admin':
        update_query = text("""UPDATE Admin SET job_title=:job_title \
                        WHERE EMPID=:employee_id;
    """)
        session.execute(update_query, subclass_data)
    session.commit()
    return
# =========================
# CRUD operations for Delete
# =========================
def delete_employee_entry(session, employee_id, job_class):
    try:
        

        if job_class=='Nurse':
            subclass_delete_query = text("""DELETE FROM Nurse \
                            WHERE EMPID=:employee_id;
        """)
            session.execute(subclass_delete_query, {'employee_id': employee_id})
        elif job_class=='Doctor':
            subclass_delete_query = text("""DELETE FROM Doctor \
                            WHERE EMPID=:employee_id;
        """)
            session.execute(subclass_delete_query, {'employee_id': employee_id})
        elif job_class=='OtherHCP':
            subclass_delete_query = text("""DELETE FROM OtherHCP \
                            WHERE EMPID=:employee_id;
        """)
            session.execute(subclass_delete_query, {'employee_id': employee_id})
        elif job_class=='Admin':
            subclass_delete_query = text("""DELETE FROM Admin  \
                            WHERE EMPID=:employee_id;
        """)
            session.execute(subclass_delete_query, {'employee_id': employee_id})

        employee_delete_query = text("""
            DELETE FROM Employee WHERE EMPID = :employee_id;
        """)
        session.execute(employee_delete_query, {'employee_id': employee_id})


        session.commit()
        print("\n\nDeletion Progress is here\n\n", employee_delete_query)
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database operation failed: {str(e)}")
