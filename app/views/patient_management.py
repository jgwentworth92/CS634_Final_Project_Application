import logging

from flask import render_template, flash, url_for, redirect, request
from icecream import ic

from app.Database import db

from app.forms import PatientForm, AppointmentForm
from crud_helpers.patient_crud import delete_patient, update_patient, get_patient, get_all_patients, create_patient


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
            create_patient(db.get_db(), patient_data)
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


