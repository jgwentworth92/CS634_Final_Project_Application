from flask import flash, redirect, url_for, render_template

from app.crud import create_facility
from app.forms import OfficeForm, OutpatientSurgeryForm
from app.Database import db

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
            return redirect(url_for('routes.index'))  # Assuming there is a function to list facilities
        except Exception as e:
          # Roll back in case of error
            flash(f"Error adding facility: {str(e)}", 'error')

    return render_template('add.html', form=form, ftype=ftype)