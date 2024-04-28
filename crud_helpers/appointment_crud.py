import logging

from icecream import ic
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from crud_helpers.insurance_crud import get_insurance_id

# Setting the logging level for SQLAlchemy engine to display queries


# =========================
# CRUD operations for Create
# =========================

def create_appointment(session, patient_id, facility_id, doctor_id, date_time, description):
    try:
        insurance_id = get_insurance_id(session, patient_id)
        if not insurance_id:
            raise ValueError("No insurance found for patient")
        invoice_date = date_time.date()
        invoice_id = handle_invoice(session, insurance_id, invoice_date)
        insert_appointment(session, patient_id, facility_id, doctor_id, date_time, description)
        insert_invoice_details(session, invoice_id, patient_id, facility_id, doctor_id, date_time)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Failed to create appointment: {str(e)}")


def insert_appointment(session, patient_id, facility_id, doctor_id, date_time, description):
    query = text("""
        INSERT INTO Appointments (patient_id, facility_id, doctor_id, date_time, description)
        VALUES (:patient_id, :facility_id, :doctor_id, :date_time, :description)
    """)
    session.execute(query, {'patient_id': patient_id, 'facility_id': facility_id, 'doctor_id': doctor_id,
                            'date_time': date_time, 'description': description})


def insert_invoice_details(session, invoice_id, patient_id, facility_id, doctor_id, date_time):
    query = text("""
        INSERT INTO InvoiceDetails (invoice_id, cost, patient_id, facility_id, doctor_id, date_time)
        VALUES (:invoice_id, 0, :patient_id, :facility_id, :doctor_id, :date_time)
    """)
    session.execute(query, {'invoice_id': invoice_id, 'patient_id': patient_id, 'facility_id': facility_id,
                            'doctor_id': doctor_id, 'date_time': date_time})


def handle_invoice(session, insurance_id, invoice_date):
    # First, attempt to find an existing invoice
    result = session.execute(text("""
        SELECT invoice_id FROM Invoice
        WHERE insurance_id = :insurance_id AND date = :invoice_date
    """), {'insurance_id': insurance_id, 'invoice_date': invoice_date})

    for row in result:
        return row[0]  # Return existing invoice_id if found

    # If no existing invoice, create a new one
    session.execute(text("""
        INSERT INTO Invoice (date, total_cost, insurance_id)
        VALUES (:invoice_date, 0, :insurance_id)
    """), {'invoice_date': invoice_date, 'insurance_id': insurance_id})
    session.commit()

    # Retrieve the newly created invoice_id using LAST_INSERT_ID()
    result = session.execute(text("SELECT LAST_INSERT_ID()"))
    for row in result:
        return row[0]  # Return the new invoice_id


# Return the newly created invoice ID

def ensure_treats_exist(session, patient_id, doctor_id):
    result = session.execute(text("""
        SELECT 1 FROM Treats WHERE patient_id = :patient_id AND doctor_id = :doctor_id
    """), {'patient_id': patient_id, 'doctor_id': doctor_id})
    for _ in result:
        return  # Treats relationship exists, do nothing
    # If not exists, insert new relationship
    session.execute(text("""
        INSERT INTO Treats (patient_id, doctor_id)
        VALUES (:patient_id, :doctor_id)
    """), {'patient_id': patient_id, 'doctor_id': doctor_id})
    session.commit()


# =========================
# CRUD operations for Retrieve
# =========================
def find_invoice_id(session, insurance_id, new_date):
    query = text("""
        SELECT invoice_id FROM Invoice
        WHERE insurance_id = :insurance_id AND date = :new_date
    """)
    result = session.execute(query, {'insurance_id': insurance_id, 'new_date': new_date})
    for row in result:
        return row[0]  # Return the first invoice_id found
    return None  # Return None if no invoice is found


def get_appointment_by_id(session, patient_id, facility_id, doctor_id, date_time):
    result = session.execute(text("""
        SELECT * FROM Appointments
        WHERE patient_id = :patient_id AND facility_id = :facility_id
        AND doctor_id = :doctor_id AND date_time = :date_time
    """), {'patient_id': patient_id, 'facility_id': facility_id, 'doctor_id': doctor_id, 'date_time': date_time})
    appointment = None
    for row in result:
        appointment = {'patient_id': row[0], 'doctor_id': row[1], 'facility_id': row[2], 'date_time': row[3],
                       'description': row[4]}
        break  # Since there should only be one record, break after the first iteration
    return appointment


def search_appointments_db(session, patient_id=None, doctor_id=None, facility_id=None, start_date=None, end_date=None):
    query = """
        SELECT a.patient_id, a.doctor_id, a.facility_id, a.date_time, id.cost, a.description
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
    return [{'patient_id': row[0], 'doctor_id': row[1], 'facility_id': row[2], 'date_time': row[3], 'cost': row[4],
             'description': row[5]} for row in result]


# =========================
# CRUD operations for Update
# =========================
def update_appointment_and_related_details(session, original_data, updated_data):
    try:
        # Start transaction
        invoice_detail_tuple = None
        # Check if date_time has changed
        date_changed = original_data['date_time'] != updated_data['date_time']
        invoice_id = None

        if date_changed:
            # Fetch and delete existing InvoiceDetails temporarily to avoid foreign key constraint
            invoice_detail_result = session.execute(text("""
                        SELECT invoice_id, cost FROM InvoiceDetails
                        WHERE patient_id = :patient_id AND facility_id = :facility_id AND doctor_id = :doctor_id AND date_time = :date_time
                    """), {
                'patient_id': original_data['patient_id'],
                'facility_id': original_data['facility_id'],
                'doctor_id': original_data['doctor_id'],
                'date_time': original_data['date_time']
            })
            if invoice_detail_result:
                # Convert tuple to dictionary using the column names directly as keys
                for val in invoice_detail_result:
                    invoice_detail_tuple = {
                    'invoice_id': val[0],
                    'cost': val[1]
                    }
            session.execute(text("""
                DELETE FROM InvoiceDetails
                WHERE patient_id = :patient_id AND facility_id = :facility_id AND doctor_id = :doctor_id AND date_time = :date_time
            """), {
                'patient_id': original_data['patient_id'],
                'facility_id': original_data['facility_id'],
                'doctor_id': original_data['doctor_id'],
                'date_time': original_data['date_time']
            })

            # Check for or create a new invoice for the updated date_time
            insurance_id=get_insurance_id(session,updated_data['patient_id'])
            invoice_id = find_or_create_invoice(session,  insurance_id, updated_data['date_time'].date())

        # Update the Appointments
        session.execute(text("""
            UPDATE Appointments
            SET patient_id = :patient_id, facility_id = :facility_id, doctor_id = :doctor_id,
                date_time = :date_time, description = :description
            WHERE patient_id = :original_patient_id AND facility_id = :original_facility_id
            AND doctor_id = :original_doctor_id AND date_time = :original_date_time
        """), {
            'patient_id': updated_data['patient_id'],
            'facility_id': updated_data['facility_id'],
            'doctor_id': updated_data['doctor_id'],
            'date_time': updated_data['date_time'],
            'description': updated_data['description'],
            'original_patient_id': original_data['patient_id'],
            'original_facility_id': original_data['facility_id'],
            'original_doctor_id': original_data['doctor_id'],
            'original_date_time': original_data['date_time']
        })

        if date_changed and invoice_detail_tuple:
            # Reinsert updated InvoiceDetails with new invoice_id and date_time
            session.execute(text("""
                INSERT INTO InvoiceDetails (invoice_id, cost, patient_id, facility_id, doctor_id, date_time)
                VALUES (:invoice_id, :cost, :patient_id, :facility_id, :doctor_id, :date_time)
            """), {
                'invoice_id': invoice_id,
                'cost': invoice_detail_tuple['cost'],
                'patient_id': updated_data['patient_id'],
                'facility_id': updated_data['facility_id'],
                'doctor_id': updated_data['doctor_id'],
                'date_time': updated_data['date_time']
            })

        # Commit the transaction
        session.commit()

    except Exception as e:
        # Rollback in case of an error
        session.rollback()
        raise Exception(f"Failed to update appointment and related entities: {str(e)}")




def search_daily_insurance_invoices(session, invoice_date):
    """
    Search for daily insurance invoices by a specific date, including details for each invoice detail
    entry, patient information, and associated insurance company name using tuple indices.

    Parameters:
    - session: SQLAlchemy session for executing the query.
    - invoice_date: datetime.date object representing the date to search invoices.

    Returns:
    A structured list of dictionaries each containing detailed invoice and patient information,
    along with total cost per invoice and details for individual charges, grouped by insurance company and invoice.
    """
    # Define the SQL query with proper grouping and ordering
    sql_query = text("""
        SELECT 
            ic.name,          -- 0: Insurance company name
            i.invoice_id,     -- 1: Invoice ID
            i.total_cost,     -- 2: Invoice total cost
            id.cost,          -- 3: Detail cost
            p.fname,          -- 4: Patient first name
            p.lname,          -- 5: Patient last name
            p.patient_id,     -- 6: Patient ID
            i.insurance_id    -- 7: Insurance ID
        FROM Invoice i
        JOIN InvoiceDetails id ON i.invoice_id = id.invoice_id
        JOIN Patient p ON id.patient_id = p.patient_id
        JOIN InsuranceCompany ic ON i.insurance_id = ic.insurance_id
        WHERE DATE(i.date) = :invoice_date
        ORDER BY ic.insurance_id, i.invoice_id, p.patient_id
    """)

    # Execute the query with the provided date parameter
    result = session.execute(sql_query, {'invoice_date': invoice_date})

    # Organize results into a nested structure: insurance -> invoices -> patient details
    invoices_by_insurance = {}
    for row in result:
        insurance_key = (row[7], row[0])  # Insurance ID and name
        invoice_key = row[1]  # Invoice ID

        if insurance_key not in invoices_by_insurance:
            invoices_by_insurance[insurance_key] = {
                'insurance_name': row[0],
                'invoices': {}
            }

        if invoice_key not in invoices_by_insurance[insurance_key]['invoices']:
            invoices_by_insurance[insurance_key]['invoices'][invoice_key] = {
                'invoice_id': invoice_key,
                'invoice_total_cost': float(row[2]),
                'patient_details': []
            }

        # Append patient details to this invoice
        invoices_by_insurance[insurance_key]['invoices'][invoice_key]['patient_details'].append({
            'patient_id': row[6],
            'patient_fname': row[4],
            'patient_lname': row[5],
            'detail_cost': float(row[3])
        })

    return invoices_by_insurance


def find_or_create_invoice(session, insurance_id, new_date):
    try:
        invoice_id = find_invoice_id(session, insurance_id, new_date)
        if not invoice_id:
            # Create a new invoice if it doesn't exist
            session.execute(text("""
                INSERT INTO Invoice (date, total_cost, insurance_id)
                VALUES (:date, 0, :insurance_id)
            """), {'date': new_date, 'insurance_id': insurance_id})
            session.commit()
            invoice_id = find_invoice_id(session, insurance_id, new_date)
        return invoice_id
    except Exception as e:

        session.rollback()
        raise Exception(f"Failed to update appointment and related entities: {str(e)}")



def update_invoice_details_date(session, updated_data):
    try:
        # Assuming you have an invoice table that links through the patient, facility, and doctor ID
        update_invoice = text("""
            UPDATE Invoice
            SET date = :new_date
            WHERE patient_id = :patient_id AND facility_id = :facility_id AND doctor_id = :doctor_id;
        """)
        session.execute(update_invoice, {
            'new_date': updated_data['date_time'].date(),
            'patient_id': updated_data['patient_id'],
            'facility_id': updated_data['facility_id'],
            'doctor_id': updated_data['doctor_id']
        })
        session.commit()
    except Exception as e:
        session.rollback()
        raise Exception(f"Failed to update invoice details: {str(e)}")




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


        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during database operation: {str(e)}")
        raise


def update_invoice_details(session, new_invoice_id, patient_id, facility_id, doctor_id, new_date_time,
                           original_date_time):
    try:
        update_invoice_details_query = text("""
            UPDATE InvoiceDetails
            SET invoice_id = :new_invoice_id, date_time = :new_date_time
            WHERE patient_id = :patient_id AND facility_id = :facility_id
            AND doctor_id = :doctor_id AND date_time = :original_date_time
        """)
        session.execute(update_invoice_details_query, {
            'new_invoice_id': new_invoice_id,
            'new_date_time': new_date_time,
            'patient_id': patient_id,
            'facility_id': facility_id,
            'doctor_id': doctor_id,
            'original_date_time': original_date_time
        })
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error during database operation: {str(e)}")
        raise

def update_total_cost(session):
    try:
        update_total_cost = text("""
            UPDATE Invoice AS i
            SET i.total_cost = (SELECT SUM(id.cost) FROM InvoiceDetails AS id
                WHERE id.invoice_id = i.invoice_id
            )
            WHERE EXISTS (
                SELECT * FROM InvoiceDetails AS id
                WHERE id.invoice_id = i.invoice_id
            );""")
    except Exception as e:
        session.rollback()
        print(f"Error during total cost update: {str(e)}")
        raise

def generate_top_revenue_days(session, year, month):
    revenue_query = text("""
            SELECT DATE(Invoice.date) AS revenue_date, SUM(Invoice.total_cost) AS total_revenue
            FROM Invoice
            WHERE YEAR(Invoice.date) = :year AND MONTH(Invoice.date) = :month
            GROUP BY DATE(Invoice.date)
            ORDER BY total_revenue DESC
            LIMIT 5;
        """)
    revenue_data = session.execute(revenue_query, {'year': year, 'month': month})
    result_list = []
    for revenue_entry in revenue_data:
        result_list.append({
                    'revenue_date': revenue_entry[0],
                    'total_revenue': revenue_entry[1],
                })
    return result_list

def generate_average_revenue_list(session, begin_date, end_date):
    revenue_query = text("""
            SELECT InsuranceCompany.name, AVG(Invoice.total_cost) AS avg_daily_revenue
            FROM Invoice
            JOIN InsuranceCompany ON Invoice.insurance_id = InsuranceCompany.insurance_id
            WHERE Invoice.date BETWEEN :begin_date AND :end_date
            GROUP BY InsuranceCompany.name;
        """)
    revenue_data = session.execute(revenue_query, {'begin_date': begin_date, 'end_date': end_date})
    result_list = []
    for revenue_entry in revenue_data:
        result_list.append({
                    'insurance_company': revenue_entry[0],
                    'average_revenue': int(revenue_entry[1]),
                })
    print("\n\n", result_list, "\n\n")
    return result_list