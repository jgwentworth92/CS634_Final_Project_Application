from datetime import datetime

from flask import flash, redirect, url_for, render_template, request, session

from app.forms import OfficeForm, OutpatientSurgeryForm, DailyInvoiceForm
from app.Database import db
from crud_helpers.facility_crud import create_facility, retrieve_facilities, get_facility_by_id, \
                                        update_facility_entry, delete_facility_entry, generate_revenue_by_date, \
                                        generate_revenue_by_patient


def add_facility(ftype='Office'):
    # Map form classes to the facility types
    form_class = {
        'Office': OfficeForm,
        'OutpatientSurgery': OutpatientSurgeryForm,
    }.get(ftype)
    
    if not form_class:
        flash('Invalid facility type specified.', 'error')
        return redirect(url_for('index'))  # Redirect to a default page if invalid type

    form = form_class()  # Instantiate the form based on the facility type
    print("\n\n",form, "\n\n")
    if form.validate_on_submit():  # Check if the form has been submitted and is valid
        try:
            # Common facility data collected from the form
            facility_data = {
                'address': form.address.data,
                'size': form.size.data,
                'ftype': ftype  # Set ftype directly from the URL parameter
            }

            # Specific data based on facility type
            subtype_data = {}
            if ftype == 'Office':
                subtype_data = {'office_count': form.office_count.data}
            elif ftype == 'OutpatientSurgery':
                subtype_data = {
                    'room_count': form.room_count.data,
                    'description': form.description.data,
                    'p_code': form.p_code.data
                }

            # Call the CRUD function to create a new facility
            create_facility(db.get_db(), facility_data, subtype_data)
         # Commit the transaction after successful CRUD operation
            flash('Facility added successfully!', 'success')
            return redirect(url_for('routes.view_facilities'))  # Assuming there is a function to list facilities
        except Exception as e:
          # Roll back in case of error
            flash(f"Error adding facility: {str(e)}", 'error')

    return render_template('add.html', form=form, ftype=ftype)

def view_facilities():
    # Retrieve all facilities, organized by type with associated data
    facilities = retrieve_facilities(db.get_db())
    offices = [f for f in facilities if f['ftype'] == 'Office']
    surgeries = [f for f in facilities if f['ftype'] == 'Outpatient Surgery']

    return render_template('view_facility.html', offices=offices, surgeries=surgeries)

def update_facility(surgery, office):
    if surgery != 0:
        ftype = 'OutpatientSurgery'
        form_class = {
        'Office': OfficeForm,
        'OutpatientSurgery': OutpatientSurgeryForm,}.get(ftype)
        form = form_class()
        if form.validate_on_submit():
            facility_data = {
                'address': form.address.data,
                'size': form.size.data,
                'ftype': ftype 
            }
            subtype_data = {
                'room_count': form.room_count.data,
                'description': form.description.data,
                'p_code': form.p_code.data
            }
            update_facility_entry(db.get_db(), facility_id=surgery, 
                            facility_data=facility_data, subtype_data=subtype_data)
            flash('OutpatientSurgery updated successfully.')
            return redirect(url_for('routes.view_facilities'))
    else:
        ftype = 'Office'
        form_class = {'Office': OfficeForm,
                    'OutpatientSurgery': OutpatientSurgeryForm,}.get(ftype)
        form = form_class()
        if form.validate_on_submit():
            facility_data = {
                'address': form.address.data,
                'size': form.size.data,
                'ftype': ftype  # Set ftype directly from the URL parameter
            }

            # Specific data based on facility type
            subtype_data = {
                'office_count':form.office_count.data
            }
            update_facility_entry(db.get_db(), facility_id=office, 
                            facility_data=facility_data, subtype_data=subtype_data)
            flash('Office updated successfully.')
            return redirect(url_for('routes.view_facilities'))
        
    return render_template('add.html', form=form, ftype=ftype)

def delete_facility(surgery, office):
    if surgery != 0:
        facility_id = surgery
        ftype = 'OutpatientSurgery'
    else:
        facility_id = office
        ftype = 'Office'
    delete_facility_entry(db.get_db(), facility_id=facility_id, 
                            subclass=ftype)
    flash('{} deleted successfully.'.format(ftype))
    return redirect(url_for('routes.view_facilities'))

def revenue_by_facility():
    form = DailyInvoiceForm(request.form)
    # Check if there is already a date in session or set today's date as default
    today = datetime.now().strftime('%Y-%m-%d')
    if 'revenue_date' not in session:
        session['revenue_date'] = today

    if request.method == 'POST' and form.validate_on_submit():
        # Store the selected date in session after validating form submission
        session['revenue_date'] = form.invoice_date.data.strftime('%Y-%m-%d')
        return redirect(url_for('routes.revenue_by_facility'))  # Redirect to clear POST data

    # Get the revenue date from session or use today's date as default
    revenue_date = session.get('revenue_date', today)
    revenues, total_revenue = generate_revenue_by_patient(db.get_db(), revenue_date)

    return render_template('revenue_by_patient.html', form=form, revenues=revenues,
                           total_revenue=total_revenue, revenue_date=revenue_date)


def revenue_by_patient(date):
    revenues, total_revenue = generate_revenue_by_patient(db.get_db(), date)
    return render_template('revenue_by_patient.html', invoice_date=date, revenues=revenues, total_revenue=total_revenue)