from flask import render_template, flash, redirect, url_for
from app.Database import db
from app.crud import create_insurance_company
from app.forms import InsuranceCompanyForm


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
            return redirect(url_for('routes.index')) # Redirect to a listing page
        except Exception as e:

            flash(f"Error adding insurance company: {str(e)}", 'error')

    return render_template('add.html', form=form)