import logging
from datetime import datetime

from flask import render_template, request, redirect, url_for, session, flash
from icecream import ic

from app.forms import SearchAppointmentsForm, UpdateCostForm, AppointmentForm, DailyInvoiceForm, RevenueDaysForm, \
    DateRangeForm
from app.Database import db, total_cost_trigger
from crud_helpers.appointment_crud import search_appointments_db, update_appointment_cost_db, get_appointment_by_id, \
    create_appointment, update_appointment_and_related_details, search_daily_insurance_invoices, \
    generate_top_revenue_days, \
    generate_average_revenue_list


def daily_invoices():
    form = DailyInvoiceForm(request.form)
    invoices_by_insurance = {}
    if request.method == 'POST' and form.validate():
        # Store the selected date in session after validating form submission
        session['invoice_date'] = form.invoice_date.data.strftime('%Y-%m-%d')
        return redirect(url_for('routes.daily_invoices'))  # Redirect to clear POST data and avoid re-submission issues

    if 'invoice_date' in session:
        # Fetch invoices using the date stored in session if available
        invoice_date = session['invoice_date']
        invoices_by_insurance = search_daily_insurance_invoices(db.get_db(), invoice_date)
    else:
        # Set a default date or handle the case where no date is selected
        invoice_date = datetime.now().strftime('%Y-%m-%d')
        invoices_by_insurance = search_daily_insurance_invoices(db.get_db(), invoice_date)

    return render_template('daily_invoice_view.html', form=form, invoices_by_insurance=invoices_by_insurance,
                           invoice_date=invoice_date)


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
            form_key = (
            appointment['patient_id'], appointment['facility_id'], appointment['doctor_id'], appointment['date_time'])
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

                flash(f'Cost updated successfully', 'success')
                return redirect(url_for('routes.search_appointments'))  # Correctly namespaced

    return render_template('search_appointment.html', form=form, appointments=appointments, update_forms=update_forms)


def edit_appointment(patient_id, facility_id, doctor_id, date_time):
    db_session = db.get_db()  # Get the database session
    appointment = get_appointment_by_id(db_session, patient_id, facility_id, doctor_id,
                                        date_time)  # Fetch appointment details
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
        update_appointment_and_related_details(db_session, appointment,
                                               updated_data)  # This function should handle the update logic
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
                               form.date_time.data, form.description.data)
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('routes.view_patient_list'))  # Adjust redirect as necessary
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add.html', form=form)


def top_revenue_days():
    today = datetime.now()
    default_monthyear = today.strftime('%Y-%m')

    if request.method == 'POST':
        # Directly read the month/year from the form input
        session['selected_monthyear'] = request.form['monthInput']
        return redirect(url_for('routes.top_revenue_days'))

    revenues = []
    # Fetch monthyear either from session or use the default
    monthyear = session.get('selected_monthyear', default_monthyear)
    year, month = monthyear.split('-')
    revenues = generate_top_revenue_days(db.get_db(), year, month)

    return render_template('top_revenues.html', revenues=revenues,
                           selected_monthyear=monthyear)



def average_revenue():
    form = DateRangeForm()
    if form.validate_on_submit():
        session['begin_date'] = form.begin_date.data.strftime('%Y-%m-%d')
        session['end_date'] = form.end_date.data.strftime('%Y-%m-%d')
        return redirect(url_for('routes.average_revenue'))

    revenues = []
    if 'begin_date' in session and 'end_date' in session:
        begin_date = session['begin_date']
        end_date = session['end_date']
        revenues = generate_average_revenue_list(db.get_db(), begin_date, end_date)

    return render_template('average_revenues.html', form=form, revenues=revenues)