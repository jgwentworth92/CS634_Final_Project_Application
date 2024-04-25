from flask import render_template, flash, redirect, url_for, request
from app.Database import db

from app.forms import InsuranceCompanyForm
from crud_helpers.insurance_crud import create_insurance_company, retrieve_insurance_companies, \
    get_insurance_company_by_id, update_insurance_company_data


def add_insurance_company():
    form = InsuranceCompanyForm()
    if form.validate_on_submit():  # Check if the form is valid after submission
        insurance_data = {
            'name': form.name.data,
            'address': form.address.data
        }
        try:
            # Attempt to create an insurance company using the provided data
            create_insurance_company(db.get_db(), insurance_data)

            flash('Insurance company added successfully!', 'success')
            return redirect(url_for('routes.view_insurance_companies'))  # Redirect to a listing page
        except Exception as e:

            flash(f"Error adding insurance company: {str(e)}", 'error')

    return render_template('add.html', form=form)




def view_insurance_companies():
    insurance_data = retrieve_insurance_companies(db.get_db())  # Assuming this function exists to fetch data
    return render_template('view_insurance_companies.html', insurance_companies=insurance_data)









def update_insurance_company(insurance_id):
    insurance_company = get_insurance_company_by_id(db.get_db(), insurance_id)
    if not insurance_company:
        flash('Insurance company not found.')
        return redirect(url_for('routes.view_insurance_companies'))

    if request.method == 'GET':
        form = InsuranceCompanyForm(obj=insurance_company)
    else:
        form = InsuranceCompanyForm()

    if form.validate_on_submit():
        insurance_company.name = form.name.data
        insurance_company.address = form.address.data
        update_insurance_company_data(db.get_db(),insurance_id,    insurance_company.name, insurance_company.address)
        flash('Insurance company updated successfully.')
        return redirect(url_for('routes.view_insurance_companies'))

    return render_template('update.html', form=form, insurance_id=insurance_id)