from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import logging


class Database:
    """
    Synchronous Database class to manage database connections and sessions.
    """

    def __init__(self):
        """
        Initialize the database class.
        """
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        """
        Get the attribute from the session.
        """
        return getattr(self._session, name)

    def connect(self):
        """
        Connect to the database.
        """
        logging.info("Connecting to the database...")
        self._engine = create_engine(
            "mysql+pymysql://user:password@mysqldb:3306/mydatabase",
            echo=True
        )

        self._session = sessionmaker(
            bind=self._engine, autocommit=False
        )

    def disconnect(self):
        """
        Dispose the database connection.
        """
        self._engine.dispose()

    def get_db(self):
        """
        Get the database session.
        """
        session = self._session()
        return session


db = Database()


# Other imports and Database class definition remain the same

def create_facility_tables(session):
    queries = [
        """
        CREATE TABLE IF NOT EXISTS Facility (
            facility_id INT AUTO_INCREMENT,
            address VARCHAR(255),
            size INT,
            ftype ENUM('Office', 'OutpatientSurgery'),
            PRIMARY KEY (facility_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Office (
            facility_id INT NOT NULL,
            office_count INT,
            PRIMARY KEY (facility_id),
            FOREIGN KEY (facility_id) REFERENCES Facility(facility_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS OutpatientSurgery (
            facility_id INT NOT NULL,
            room_count INT,
            description VARCHAR(255),
            p_code VARCHAR(100),
            PRIMARY KEY (facility_id),
            FOREIGN KEY (facility_id) REFERENCES Facility(facility_id)
        );
        """
    ]
    for query in queries:
        session.execute(text(query))
        session.commit()


def create_employee_sublcass_tables(session):
    queries = [
        """
        CREATE TABLE IF NOT EXISTS OtherHCP (
            EMPID INT NOT NULL,
            job_title VARCHAR(255),
            PRIMARY KEY (EMPID),
            FOREIGN KEY (EMPID) REFERENCES Employee(EMPID)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Nurse (
            EMPID INT NOT NULL,
            certification VARCHAR(255),
            PRIMARY KEY (EMPID),
            FOREIGN KEY (EMPID) REFERENCES Employee(EMPID)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Admin (
            EMPID INT NOT NULL,
            job_title VARCHAR(255),
            PRIMARY KEY (EMPID),
            FOREIGN KEY (EMPID) REFERENCES Employee(EMPID)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Doctor (
            EMPID INT NOT NULL,
            speciality VARCHAR(255),
            bc_date DATE,
            PRIMARY KEY (EMPID),
            FOREIGN KEY (EMPID) REFERENCES Employee(EMPID)
        );
        """
    ]

    for query in queries:
        session.execute(text(query))
        session.commit()


# Establishing the connection string

def create_employee_tables(session):
    sql_query = text("""
  CREATE TABLE IF NOT EXISTS Employee (
    EMPID INT AUTO_INCREMENT,
    SSN INT NOT NULL,
    fname VARCHAR(255),
    lname VARCHAR(255),
    salary DECIMAL(10, 2),
    hire_date DATE,
    job_class ENUM('OtherHCP', 'Nurse', 'Admin', 'Doctor'),
    address VARCHAR(255),
    facility_id INT,
    PRIMARY KEY (EMPID, SSN),
    UNIQUE (SSN),
    FOREIGN KEY (facility_id) REFERENCES Facility(facility_id)
);

    """)

    session.execute(sql_query)
    session.commit()


def create_insurance_tables(session):
    sql_query = text("""
       CREATE TABLE IF NOT EXISTS InsuranceCompany (
           insurance_id INT AUTO_INCREMENT,
           name VARCHAR(255),
           address VARCHAR(255),
           PRIMARY KEY (insurance_id)
       ) ;
       """)

    session.execute(sql_query)
    session.commit()


def create_treats_tables(session):
    sql_query = text("""
       CREATE TABLE IF NOT EXISTS Treats (
           patient_id INT NOT NULL,
           doctor_id INT NOT NULL,
           PRIMARY KEY (patient_id, doctor_id),
           FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
           FOREIGN KEY (doctor_id) REFERENCES Doctor(EMPID)
       );
       """)

    session.execute(sql_query)
    session.commit()


def create_appointments_tables(session):
    sql_query = text("""
      CREATE TABLE IF NOT EXISTS Appointments (
          patient_id INT NOT NULL,
          facility_id INT NOT NULL,
          doctor_id INT NOT NULL,
          date_time DATETIME NOT NULL,
          description VARCHAR(255),
          PRIMARY KEY (patient_id, facility_id, doctor_id, date_time),
          FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
          FOREIGN KEY (facility_id) REFERENCES Facility(facility_id),
          FOREIGN KEY (doctor_id) REFERENCES Doctor(EMPID)
      );
      """)

    session.execute(sql_query)
    session.commit()


def create_invoice_tables(session):
    queries = [
        """
        CREATE TABLE IF NOT EXISTS Invoice (
            invoice_id INT AUTO_INCREMENT,
            date DATE NOT NULL,
            total_cost DECIMAL(10, 2),
            insurance_id INT,
            PRIMARY KEY (invoice_id),
            FOREIGN KEY (insurance_id) REFERENCES InsuranceCompany(insurance_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS InvoiceDetails (
    invoice_id INT NOT NULL,
    cost DECIMAL(10, 2),
    patient_id INT NOT NULL,
    facility_id INT NOT NULL,
    doctor_id INT NOT NULL,
    date_time DATETIME NOT NULL,
    PRIMARY KEY (invoice_id, patient_id, facility_id, doctor_id, date_time),
    FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id),
    FOREIGN KEY (patient_id, facility_id, doctor_id, date_time) REFERENCES Appointments(patient_id, facility_id, doctor_id, date_time)
);
        """]

    for query in queries:
        session.execute(text(query))
        session.commit()


def create_patient_table(session):
    # SQL query for creating the Patient table
    sql_query = text("""
   CREATE TABLE IF NOT EXISTS Patient (
    patient_id INT AUTO_INCREMENT,
    fname VARCHAR(255),
    lname VARCHAR(255),
    primary_doc_id INT,  
    insurance_id INT,
    PRIMARY KEY (patient_id),
    FOREIGN KEY (primary_doc_id) REFERENCES Doctor(EMPID), 
    FOREIGN KEY (insurance_id) REFERENCES InsuranceCompany(insurance_id) 
);
    """)

    session.execute(sql_query)
    session.commit()
    logging.info("Patient table created successfully.")


def main():
    db = Database()
    db.connect()
    session = db.get_db()
    try:
        create_facility_tables(session)
        create_employee_tables(session)
        create_employee_sublcass_tables(session)
        create_insurance_tables(session)
        create_patient_table(session)
        create_treats_tables(session)
        create_appointments_tables(session)
        create_invoice_tables(session)
    finally:
        session.close()
        db.disconnect()


if __name__ == "__main__":
    main()
