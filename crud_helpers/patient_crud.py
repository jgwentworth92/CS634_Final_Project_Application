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
def create_patient(session, patient_data):
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

# =========================
# CRUD operations for Retrieve
# =========================
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


# =========================
# CRUD operations for Update
# =========================
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


# =========================
# CRUD operations for Delete
# =========================
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
