
from pydantic import BaseModel
from datetime import date
from enum import Enum

class JobClass(str, Enum):
    otherhcp = 'OtherHCP'
    nurse = 'Nurse'
    admin = 'Admin'
    doctor = 'Doctor'

class EmployeeModel(BaseModel):
    ssn: int
    fname: str
    lname: str
    salary: float
    hire_date: date
    job_class: JobClass
    address: str
    facility_id: int

class Doctor(BaseModel):
    empid: int
    speciality: str
    bc_date: date

class Nurse(BaseModel):
    empid: int
    certification: str

class Admin(BaseModel):
    empid: int
    job_title: str

class OtherHCP(BaseModel):
    empid: int
    job_title: str
