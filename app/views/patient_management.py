import logging

from flask import render_template, flash, url_for, redirect, request
from icecream import ic

from app.Database import db

from app.crud import add_patient, get_all_patients, update_patient, get_patient, delete_patient, create_appointment, \
    search_appointments_db
from app.forms import PatientForm, AppointmentForm


def add_patient_record():
    form = PatientForm()
    if form.validate_on_submit():
        # Extract form data
        patient_data = {
            'fname': form.fname.data,
            'lname': form.lname.data,
            'primary_doc_id': form.primary_doc_id.data,
            'insurance_id': form.insurance_id.data
        }

        try:
            # Create SQL insert statement
            add_patient(db.get_db(), patient_data)
            flash('Patient added successfully!')
            return redirect(url_for('routes.view_patient_list'))  # Redirect to a route that shows all patients
        except Exception as e:

            flash(f'Error adding patient: {e}')

    return render_template('add.html', form=form)


def view_patient_list():
    patient_list = get_all_patients(db.get_db())
    return render_template('patient_view.html', patient_list=patient_list)


def edit_patient(patient_id):
    patient = get_patient(db.get_db(), patient_id)  # Assume this function returns a dict of patient info

    if request.method == 'GET':
        form = PatientForm(patient=patient)
    else:
        form = PatientForm()

    if form.validate_on_submit():
        # Process form data and update the database
        updated_data = {
            'fname': form.fname.data,
            'lname': form.lname.data,
            'primary_doc_id': form.primary_doc_id.data,
            'insurance_id': form.insurance_id.data
        }
        logging.info(f"first name is {form.fname.data}")
        update_patient(db.get_db(), patient_id, updated_data)  # Assume this function handles DB update
        flash('Patient updated successfully!')
        return redirect(url_for('routes.view_patient_list'))

    return render_template('update.html', form=form)


def delete_patient_record(patient_id):
    try:
        # Function to execute the SQL delete command
        delete_patient(db.get_db(), patient_id)
        flash('Patient successfully deleted.')
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('routes.view_patient_list'))


def make_appointment():
    form = AppointmentForm()
    appointment = search_appointments_db(db.get_db(), 2, facility_id=5)
    for val in appointment:
        ic(val)
    if form.validate_on_submit():
        # Adjust import as necessary
        session = db.get_db()
        try:
            create_appointment(session, form.patient_id.data, form.facility_id.data, form.doctor_id.data,
                               form.date_time.data)
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('routes.view_patient_list'))  # Adjust redirect as necessary
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add.html', form=form)
