

from app.crud import create_employee, get_all_facility, retrieve_all_employees
from app.forms import DoctorForm, NurseForm, AdminForm, OtherHCPForm
from app.Database import db
from icecream import ic
from flask import render_template, request, redirect, url_for, flash

def add_employee(job_class='Doctor'):
    form_class = {
        'Doctor': DoctorForm,
        'Nurse': NurseForm,
        'Admin': AdminForm,
        'OtherHCP': OtherHCPForm
    }.get(job_class, DoctorForm)  # Fallback to DoctorForm if job_class is not valid



    if not form_class:
        flash('Invalid job class specified.', 'error')
        return redirect(url_for('routes.index'))

    form = form_class()
    retrieve_all_employees(db.get_db())
    if form.validate_on_submit():
        try:
            # Common data extraction
            employee_data = {
                'ssn': form.ssn.data,
                'fname': form.fname.data,
                'lname': form.lname.data,
                'salary': form.salary.data,
                'hire_date': form.hire_date.data.strftime('%Y-%m-%d'),
                'job_class': job_class,
                'address': form.address.data,
                'facility_id': form.facility_id.data
            }
            # Subclass-specific data
            subclass_data = {}
            if job_class == 'Doctor':
                subclass_data['speciality'] = form.speciality.data
                subclass_data['bc_date'] = form.bc_date.data.strftime('%Y-%m-%d')
            elif job_class == 'Nurse':
                subclass_data['certification'] = form.certification.data
            elif job_class in ['Admin', 'OtherHCP']:
                subclass_data['job_title'] = form.job_title.data

            # Create employee in the database
            create_employee(db.get_db(), employee_data, subclass_data)
            flash(f'{job_class} has been successfully added.', 'success')
            return redirect(url_for('routes.index'))
        except Exception as e:
            flash("AYYYYE SOMETHING BROKE MY DUDE!!!!!!!!", 'error')

    return render_template('add.html', form=form, job_class=job_class)
