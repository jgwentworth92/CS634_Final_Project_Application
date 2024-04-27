import logging
from typing import Union, List

from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError


from app.schemas import EmployeeModel, JobClass, Doctor, Nurse, Admin, OtherHCP, OutpatientSurgery, Facility, Office, \
    InsuranceCompany


def get_facility_by_id(session, facility_id):
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
            LEFT JOIN OutpatientSurgery s ON f.facility_id = s.facility_id
            WHERE f.facility_id = :facility_id;
        """)
    result = session.execute(facilities_query, {'insurance_id': facility_id})
    if result is None:
        return None  # Return None if no insurance company is found
    print(result)
    


# =========================
# CRUD operations for Create
# =========================
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
# =========================
# CRUD operations for Retrieve
# =========================
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
# =========================
# CRUD operations for Update
# =========================

def update_facility_entry(session, facility_id, facility_data, subtype_data):
    try:
        facility_data['facility_id'] = facility_id
        subtype_data['facility_id'] = facility_id
        update_query = text("""UPDATE Facility SET address=:address, size=:size, ftype=:ftype WHERE facility_id=:facility_id
        """)
        session.execute(update_query, facility_data)
        
        if(facility_data['ftype']=='OutpatientSurgery'):
            update_query = text("""UPDATE OutpatientSurgery SET room_count=:room_count, description=:description, p_code=:p_code\
                WHERE facility_id=:facility_id
            """)
            session.execute(update_query, subtype_data)
            
        elif(facility_data['ftype']=='Office'):
            update_query = text("""UPDATE Office SET office_count=:office_count\
                WHERE facility_id=:facility_id
            """)
            session.execute(update_query, subtype_data)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to update patient: {str(e)}")


# =========================
# CRUD operations for Delete
# ========================