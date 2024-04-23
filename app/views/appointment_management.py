from datetime import datetime

from flask import render_template, request, redirect, url_for, session, flash

from app.crud import search_appointments_db, update_appointment_cost_db
from app.forms import SearchAppointmentsForm, UpdateCostForm
from app.Database import db


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
                flash('Cost updated successfully', 'success')
                return redirect(url_for('routes.search_appointments'))  # Correctly namespaced

    return render_template('search_appointment.html', form=form, appointments=appointments, update_forms=update_forms)


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
