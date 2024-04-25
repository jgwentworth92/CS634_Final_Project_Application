import logging
from typing import Union, List

from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError


from app.schemas import EmployeeModel, JobClass, Doctor, Nurse, Admin, OtherHCP, OutpatientSurgery, Facility, Office, \
    InsuranceCompany


# =========================
# CRUD operations for Create
# =========================
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


# =========================
# CRUD operations for Retrieve
# =========================
def get_insurance_id(session, patient_id):
    query = text("SELECT insurance_id FROM Patient WHERE patient_id = :patient_id")
    result = session.execute(query, {'patient_id': patient_id})
    insurance_companies = [{'insurance_id': company[0]} for company in
                           result]
    # Fetch all results
    return insurance_companies[0]['insurance_id'] if result else None  # Return the first insurance_id if exists


def retrieve_insurance_companies(session):
    try:
        # SQL query to fetch all insurance companies
        query = text("""
            SELECT insurance_id, name, address FROM InsuranceCompany;
        """)
        result = session.execute(query)  # This returns a list of tuples

        # Convert tuples into list of InsuranceCompany models
        insurance_companies = [{'insurance_id': company[0], 'name': company[1], 'address': company[2]} for company in
                               result]

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


# =========================
# CRUD operations for Update
# =========================
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
# =========================
# CRUD operations for Delete
# =========================
