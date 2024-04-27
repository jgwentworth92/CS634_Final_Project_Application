

from app.forms import DoctorForm, NurseForm, AdminForm, OtherHCPForm
from app.Database import db
from icecream import ic
from flask import render_template, request, redirect, url_for, flash

from crud_helpers.employee_crud import create_employee, retrieve_all_employees, update_employee_entry


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
            return redirect(url_for('routes.view_employees'))
        except Exception as e:
            flash(f"Database operation failed: {str(e)}", 'error')

    return render_template('add.html', form=form, job_class=job_class)


def view_employees():
    # Retrieve all employees
    all_employees = retrieve_all_employees(db.get_db())
    # Organize employees by job class
    employees_grouped = {}
    for emp in all_employees:
        if emp.job_class.value not in employees_grouped:
            employees_grouped[emp.job_class.value] = []
        employees_grouped[emp.job_class.value].append(emp)
    return render_template('view_employee.html', employees_grouped=employees_grouped)

def find_job_class(job_class):
    job_class = job_class.split(".")[1]
    if job_class=='nurse':
        job_class = 'Nurse'
    elif job_class=='doctor':
        job_class = 'Doctor'
    elif job_class=='otherhcp':
        job_class = 'OtherHCP'
    elif job_class=='admin':
        job_class = 'Admin'
    else:
        job_class = 'Doctor'
    form_class = {
        'Doctor': DoctorForm,
        'Nurse': NurseForm,
        'Admin': AdminForm,
        'OtherHCP': OtherHCPForm
    }.get(job_class, DoctorForm)
    return job_class, form_class

def update_employee(employee_id, job_class):
    job_class, form_class = find_job_class(job_class)
    form = form_class()
    print("\n\n", form, "\n\n")

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
            update_employee_entry(db.get_db(), employee_id, job_class, employee_data, subclass_data)
            return redirect(url_for('routes.view_employees'))
        except Exception as e:
            flash(f"Database operation failed: {str(e)}", 'error')


    return render_template('add.html', form=form, job_class=job_class)

