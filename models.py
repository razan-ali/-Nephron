from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import  UserMixin
import datetime
from sqlalchemy.orm import relationship, backref



ACCESS = {
    'guest': 0,
    'user': 1,
    'admin': 2
}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email  = db.Column(db.String(150), unique=True)
    password  = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    access = db.Column(db.Integer, default=0)
    matching_histories = relationship('MatchingHistories', backref='user', cascade="all, delete-orphan")

    def __init__(self, email,first_name,last_name , password ,access=ACCESS['guest']):
       
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.access = access

    def is_admin(self):
        return self.access == ACCESS['admin']

    def is_user(self):
        return self.access == ACCESS['user']

    def allowed(self, access_level):
        return self.access >= access_level

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {0}>'.format(self.first_name+self.last_name)
    
class Transplantation(db.Model):
    __tablename__ = 'Transplantation'
    id = db.Column(db.Integer, primary_key=True)
    DonorID = db.Column(db.Integer, db.ForeignKey('Donor.DonorID'))
    PatientID = db.Column(db.Integer, db.ForeignKey('Patient.PatientID'))
    DateOfTransplantation= db.Column(db.Date)
    complications  = db.Column(db.String(300))
    

    

class Patient(db.Model):
    __tablename__ = 'Patient'
    PatientID = db.Column(db.Integer,primary_key=True , index=True)
    BloodGroup  = db.Column(db.String(30), nullable=False)
    isPatientOnWaitingList = db.Column(db.Boolean, default=True, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    matching_histories = relationship('MatchingHistories', cascade='all, delete-orphan')
    transplantation = relationship('Transplantation', cascade="all, delete-orphan")

    #HLA values
    A1  = db.Column(db.String(30), nullable=False)
    A2  = db.Column(db.String(30), nullable=False)
    B1  = db.Column(db.String(30),nullable=False )
    B2  = db.Column(db.String(30), nullable=False)
    C1  = db.Column(db.String(30),nullable=False)
    C2  = db.Column(db.String(30),nullable=False)
    DQA1  = db.Column(db.String(30),nullable=False)
    DQA2  = db.Column(db.String(30), nullable=False)
    DQB1  = db.Column(db.String(30),nullable=False)
    DQB2  = db.Column(db.String(30),nullable=False)
    DRB1  = db.Column(db.String(30),nullable=False)
    DRB2  = db.Column(db.String(30),nullable=False)
    #anti values
    antiA  = db.Column(db.String(30))
    antiB  = db.Column(db.String(30))
    antiC  = db.Column(db.String(30))
    antiDQA  = db.Column(db.String(30))
    antiDQB  = db.Column(db.String(30))
    antIDR  = db.Column(db.String(30))

    def age(self):
        """
        Returns the age of the patient in years, based on their date of birth.
        """
        today = datetime.date.today()
        dob = self.DateOfBirth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age


class Donor(db.Model):
    __tablename__ = 'Donor'
    DonorID = db.Column(db.Integer, index=True, primary_key=True)
    BloodGroup  = db.Column(db.String(30),nullable=False)
    isAvailable = db.Column(db.Boolean, default=True, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    matching_histories = relationship('MatchingHistories', cascade='all, delete-orphan')
    transplantation = relationship('Transplantation', cascade="all, delete-orphan")
    #HLA values
    A1  = db.Column(db.String(30), nullable=False)
    A2  = db.Column(db.String(30), nullable=False)
    B1  = db.Column(db.String(30),nullable=False )
    B2  = db.Column(db.String(30), nullable=False)
    C1  = db.Column(db.String(30),nullable=False)
    C2  = db.Column(db.String(30),nullable=False)
    DQA1  = db.Column(db.String(30),nullable=False)
    DQA2  = db.Column(db.String(30), nullable=False)
    DQB1  = db.Column(db.String(30),nullable=False)
    DQB2  = db.Column(db.String(30),nullable=False)
    DRB1  = db.Column(db.String(30),nullable=False)
    DRB2  = db.Column(db.String(30),nullable=False)

    def age(self):
        """
        Returns the age of the donor in years, based on their date of birth.
        """
        today = datetime.date.today()
        dob = self.DateOfBirth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age






class MatchingHistories(db.Model):
    __tablename__ = 'MatchingHistories'
    id = db.Column(db.Integer, primary_key=True)
    DonorID = db.Column(db.Integer, db.ForeignKey('Donor.DonorID'), primary_key=True)
    PatientID = db.Column(db.Integer, db.ForeignKey('Patient.PatientID'), primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.id'))
    DateOfTransplantation = db.Column(db.DateTime)
    matchingResult  = db.Column(db.String(40))



   


    

    
  

 