
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

class Doctor(EmployeeModel):
    empid: int
    speciality: str
    bc_date: date

class Nurse(EmployeeModel):
    empid: int
    certification: str

class Admin(EmployeeModel):
    empid: int
    job_title: str

class OtherHCP(EmployeeModel):
    empid: int
    job_title: str
