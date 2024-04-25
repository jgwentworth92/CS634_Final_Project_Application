import logging
from datetime import datetime

from flask import render_template, request, redirect, url_for, session, flash
from icecream import ic

from app.forms import SearchAppointmentsForm, UpdateCostForm, AppointmentForm
from app.Database import db, total_cost_trigger
from crud_helpers.appointment_crud import search_appointments_db, update_appointment_cost_db, get_appointment_by_id, \
    create_appointment, update_appointment_and_related_details, search_daily_insurance_invoices


def search_appointments():
    form = SearchAppointmentsForm(request.form)
    update_forms = {}
    appointments = []

    if form.validate_on_submit():
        session['search_filters'] = {
            'patient_id': form.patient_id.data,
            'doctor_id': form.doctor_id.data,
            'facility_id': form.facility_id.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data
        }

        return redirect(url_for('routes.search_appointments'))  # Correctly namespaced

    if 'search_filters' in session:
        filters = session['search_filters']
        appointments = search_appointments_db(db.get_db(), **filters)
        for appointment in appointments:
            form_key = (appointment['patient_id'], appointment['facility_id'], appointment['doctor_id'], appointment['date_time'])
            appointment['form_key'] = form_key  # Store the form key as a tuple
            update_forms[form_key] = UpdateCostForm(prefix='_'.join(map(str, form_key)))

    if request.method == 'POST':
        for form_key, update_form in update_forms.items():
            if update_form.validate_on_submit():
                patient_id, facility_id, doctor_id, date_time = form_key
                update_appointment_cost_db(
                    db.get_db(),
                    patient_id=patient_id,
                    facility_id=facility_id,
                    doctor_id=doctor_id,
                    date_time=date_time,
                    new_cost=update_form.cost.data
                )

                invoices_by_insurance=search_daily_insurance_invoices(db.get_db(), '2024-04-27')


                # Assuming 'invoices_by_insurance' is your nested dictionary containing all the data
                for insurance_key, insurance_info in invoices_by_insurance.items():
                    ic(f"--- Insurance: {insurance_info['insurance_name']} (ID: {insurance_key[0]}) ---")
                    for invoice_id, invoice_info in insurance_info['invoices'].items():
                        ic(f"  - Invoice ID: {invoice_id}, Total Cost: ${invoice_info['invoice_total_cost']:.2f}")
                        for patient in invoice_info['patient_details']:
                            ic(f"    - Patient ID: {patient['patient_id']}, Name: {patient['patient_fname']} {patient['patient_lname']}, Charge: ${patient['detail_cost']:.2f}")

                flash(f'Cost updated successfully', 'success')
                return redirect(url_for('routes.search_appointments'))  # Correctly namespaced

    return render_template('search_appointment.html', form=form, appointments=appointments, update_forms=update_forms)


def edit_appointment(patient_id, facility_id, doctor_id, date_time):
    db_session = db.get_db()  # Get the database session
    appointment = get_appointment_by_id(db_session, patient_id, facility_id, doctor_id, date_time)  # Fetch appointment details
    if request.method == 'GET':
        form = AppointmentForm(appointment=appointment)  # Initialize form with appointment data
    else:
        form = AppointmentForm()  # POST request re-initializes the form for validation

    if form.validate_on_submit():
        # Collect data from the form
        updated_data = {
            'patient_id': form.patient_id.data,
            'facility_id': form.facility_id.data,
            'doctor_id': form.doctor_id.data,
            'date_time': form.date_time.data,
            'description': form.description.data
        }
        # Log update attempt
        logging.info(f"Updating appointment {appointment} with new data: {updated_data}")

        # Update the appointment in the database
        update_appointment_and_related_details(db_session, appointment, updated_data)  # This function should handle the update logic
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('routes.search_appointments'))  # Redirect to appointment search

    return render_template('update.html', form=form)

def update_cost(patient_id, facility_id, doctor_id, date_time):
    form = UpdateCostForm()

    # Convert date_time from string to a datetime object if needed
    # Ensure date_time is passed in URL-friendly format and parsed correctly
    try:
        date_time = datetime.strptime(date_time, '%Y-%m-%d_%H-%M-%S')
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('search_appointments'))

    if form.validate_on_submit():
        try:
            update_appointment_cost_db(
                session=db.get_db(),  # Assuming db.get_db() gets you the database session
                patient_id=patient_id,
                facility_id=facility_id,
                doctor_id=doctor_id,
                date_time=date_time,
                new_cost=form.cost.data
            )
            flash('Cost updated successfully', 'success')
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('search_appointments'))

    return render_template('update_cost.html', form=form, patient_id=patient_id, facility_id=facility_id,
                           doctor_id=doctor_id, date_time=date_time)
def make_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        # Adjust import as necessary
        session = db.get_db()
        try:
            create_appointment(session, form.patient_id.data, form.facility_id.data, form.doctor_id.data,
                               form.date_time.data,form.description.data)
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('routes.view_patient_list'))  # Adjust redirect as necessary
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add.html', form=form)
