from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField, DateField
from wtforms.fields.datetime import DateTimeField, DateTimeLocalField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.Database import db
from crud_helpers.employee_crud import get_all_doctors
from crud_helpers.facility_crud import retrieve_facilities
from crud_helpers.insurance_crud import retrieve_insurance_companies
from crud_helpers.patient_crud import get_all_patients


class BaseEmployeeForm(FlaskForm):
    ssn = StringField('Social Security Number', validators=[DataRequired()])
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    salary = DecimalField('Salary', validators=[DataRequired()])
    hire_date = DateField('Hire Date', format='%Y-%m-%d', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    facility_id = SelectField('Facility', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(BaseEmployeeForm, self).__init__(*args, **kwargs)

        facility_data = retrieve_facilities(db.get_db())
        self.facility_id.choices = [(data['facility_id'], f"{data['facility_id']} - {data['ftype']}") for data in
                                    facility_data]


class DoctorForm(BaseEmployeeForm):
    speciality = StringField('Speciality', validators=[DataRequired()])
    bc_date = DateField('Board Certification Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Submit')


class NurseForm(BaseEmployeeForm):
    certification = StringField('Certification', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AdminForm(BaseEmployeeForm):
    job_title = StringField('Job Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


class OtherHCPForm(BaseEmployeeForm):
    job_title = StringField('Job Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


class BaseFacilityForm(FlaskForm):
    address = StringField('Address', validators=[DataRequired()])
    size = IntegerField('Size', validators=[DataRequired()])


class OfficeForm(BaseFacilityForm):
    office_count = IntegerField('Number of Offices', validators=[DataRequired()])
    submit = SubmitField('Submit')


class OutpatientSurgeryForm(BaseFacilityForm):
    room_count = IntegerField('Number of Rooms', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    p_code = StringField('Procedure Code', validators=[DataRequired()])
    submit = SubmitField('Submit')


class InsuranceCompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Update Company')

    def __init__(self, *args, **kwargs):
        super(InsuranceCompanyForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs and kwargs['obj'] is not None:
            obj = kwargs['obj']
            self.name.data = getattr(obj, 'name', '')
            self.address.data = getattr(obj, 'address', '')


class PatientForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    primary_doc_id = SelectField('Primary Doctor', coerce=int, validators=[DataRequired()])
    insurance_id = SelectField('Insurance', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, patient=None, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)

        # Fetch all doctors and populate the choices for primary_doc_id
        doctor_data = get_all_doctors(db.get_db())
        self.primary_doc_id.choices = [(doc['EMPID'], f"{doc['fname']} {doc['lname']}") for doc in doctor_data]

        # Fetch all insurance companies and populate the choices for insurance_id
        insurance_data = retrieve_insurance_companies(db.get_db())

        self.insurance_id.choices = [(ins['insurance_id'], ins['name']) for ins in insurance_data]

        # Set default values if a patient object is provided
        if patient is not None:
            self.fname.data = patient['fname']
            self.lname.data = patient['lname']
            self.primary_doc_id.data = patient['primary_doc_id']
            self.insurance_id.data = patient['insurance_id']


class DailyInvoiceForm(FlaskForm):
    invoice_date = DateField('Invoice Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AppointmentForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    facility_id = SelectField('Facility', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    date_time = DateTimeLocalField('Date and Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Create/Update Appointment')

    def __init__(self, appointment=None, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)

        db_session = db.get_db()  # Assumed function to get the database session

        # Populate patient choices
        patient_data = get_all_patients(db_session)
        self.patient_id.choices = [(pat['patient_id'], f"{pat['fname']} {pat['lname']}") for pat in patient_data]

        # Populate facility choices

        facility_data = retrieve_facilities(db.get_db())
        self.facility_id.choices = [(data['facility_id'], f"{data['facility_id']} - {data['ftype']}") for data in
                                    facility_data]

        # Populate doctor choices
        doctor_data = get_all_doctors(db_session)
        self.doctor_id.choices = [(doc['EMPID'], f"{doc['fname']} {doc['lname']}") for doc in doctor_data]

        # Set default values if an appointment object is provided
        if appointment is not None:
            self.patient_id.data = appointment['patient_id']
            self.facility_id.data = appointment['facility_id']
            self.doctor_id.data = appointment['doctor_id']
            self.date_time.data = appointment['date_time']
            self.description.data = appointment['description']


class SearchAppointmentsForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[Optional()], choices=[])
    doctor_id = SelectField('Doctor', coerce=int, validators=[Optional()], choices=[])
    facility_id = SelectField('Facility', coerce=int, validators=[Optional()], choices=[])
    start_date = DateTimeLocalField('Start Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_date = DateTimeLocalField('End Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super(SearchAppointmentsForm, self).__init__(*args, **kwargs)

        # Populate the choices for patient_id, doctor_id, and facility_id dynamically from the database
        db_session = db.get_db()  # Assumed function to get the database session

        patient_data = get_all_patients(db_session)
        self.patient_id.choices = [(0, 'Any')] + [(pat['patient_id'], f"{pat['fname']} {pat['lname']}") for pat in
                                                  patient_data]

        doctor_data = get_all_doctors(db_session)
        self.doctor_id.choices = [(0, 'Any')] + [(doc['EMPID'], f"{doc['fname']} {doc['lname']}") for doc in
                                                 doctor_data]

        facility_data = retrieve_facilities(db.get_db())
        self.facility_id.choices = [(0, 'Any')] + [(data['facility_id'], f"{data['facility_id']} - {data['ftype']}") for
                                                   data in
                                                   facility_data]


class UpdateCostForm(FlaskForm):
    cost = DecimalField('New Cost', validators=[DataRequired(), NumberRange(min=0)], places=2, default=0.00)
    submit = SubmitField('Update Cost')
