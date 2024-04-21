from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField, DateField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired
from app.crud import get_all_facility
from app.Database import db

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
        facility_data = get_all_facility(db.get_db())
        self.facility_id.choices = [(data[0], f"{data[0]} - {data[1]}") for data in facility_data]


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