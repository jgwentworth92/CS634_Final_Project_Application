
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
from pydantic import BaseModel
from typing import Optional

class Facility(BaseModel):
    address: str
    size: int
    ftype: str
    facility_id: Optional[int] = None

class Office(Facility):
    office_count: int

class OutpatientSurgery(Facility):
    room_count: int
    description: str
    p_code: str
class InsuranceCompany(BaseModel):
    insurance_id: Optional[int] = None  # Auto-incremented by the database, optional in the model
    name: str
    address: str