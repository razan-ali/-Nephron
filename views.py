from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import  User, ACCESS, Patient, Donor, Transplantation , MatchingHistories
from flask import  render_template, flash, redirect, url_for, request
from flask_login import current_user,  login_required
from . import db  #means from __init__.py import db
from functools import wraps
from sqlalchemy import or_, func, desc
from .model import matching_result
import datetime

views = Blueprint('views', __name__)

### custom wrap to determine access level ###
def requires_access_level(access_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated: #the user is not logged in
                return redirect(url_for('login'))
            #user = User.query.filter_by(id=current_user.id).first()
            if not current_user.allowed(access_level):
                flash('You do not have access to this resource.', 'Error')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@views.route('/home', methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def home():
    user_id = current_user.id
    unique_combinations = MatchingHistories.query.with_entities(
        MatchingHistories.id, MatchingHistories.DonorID, MatchingHistories.DateOfTransplantation
    ).filter_by(UserID=user_id).distinct().order_by(desc(MatchingHistories.id))
    if request.method == 'POST':
        donorID = request.form.get('donorID')
        return redirect(url_for('views.mathcing', donorID=donorID))
    return render_template("index.html", unique_combinations= unique_combinations)



@views.route('/admin')
@requires_access_level(ACCESS['admin'])
def admin():
    users = User.query.filter(or_(User.access == 0, User.access == 1)).all()
    return render_template("users.html", users=users)

@views.route("/update_activation/<int:user_id>/<int:activated>", methods=["GET"])
def update_activation(user_id, activated):
    user = User.query.get(user_id)
    if user.access == 0:
        user.access = 1
    else:
        user.access = 0
    db.session.commit()
    return "OK"

@views.route("/delete_user/<int:user_id>", methods=["POST"])
@requires_access_level(ACCESS['admin'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("views.admin"))


'''--------------------------------------------------------------------------------------------------------'''
'''------------------------------------------------DONOR---------------------------------------------------'''
'''--------------------------------------------------------------------------------------------------------'''




@views.route('/donor')
@requires_access_level(ACCESS['user'])
@login_required
def donor():
    donors = Donor.query.all()
    return render_template("Donor.html",donors = donors )


@views.route('/donor_search', methods=['POST'])
@requires_access_level(ACCESS['user'])
@login_required
def donor_search():
    search_query = request.form['searchQuery']
    donors = Donor.query.filter(Donor.DonorID.like(f"{search_query}%")).all()
    return render_template("Donor.html", donors=donors)


@views.route('/donor/<int:donorID>', methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def view_donor(donorID):
    donor = Donor.query.filter_by(DonorID=donorID).first_or_404()
    return render_template("View-Donor.html", donor=donor)




@views.route('/donor/add_donor', methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def add_donor():
    if request.method == 'POST':
        DonorID = request.form.get('donorID')
        donorA1 = request.form.get('donorA1')
        donorA2 = request.form.get('donorA2')
        donorB1 = request.form.get('donorB1')
        donorB2 = request.form.get('donorB2')
        donorC1 = request.form.get('donorC1')
        donorC2 = request.form.get('donorC2')
        donorDRB1 = request.form.get('donorDRB1')
        donorDRB2 = request.form.get('donorDRB2')
        donorDQA1 = request.form.get('donorDQA1')
        donorDQA2 = request.form.get('donorDQA2')
        donorDQB1 = request.form.get('donorDQB1')
        donorDQB2 = request.form.get('donorDQB2')
        input_status = request.form.get('inputStatus')
        BloodGroup = request.form.get('bloodGroup')
        date_of_birth = request.form.get('inputDate')
        isAvailable = True if input_status == "option1" else False
        donor = Donor.query.filter_by(DonorID=DonorID).first()
        if donor is None :
            new_donor = Donor(DonorID=DonorID,A1= donorA1, A2= donorA2, B1 = donorB1,B2= donorB2, C1 = donorC1, C2  = donorC2,
                            DQA1 = donorDQA1, DQA2= donorDQA2, DQB1= donorDQB1, DQB2= donorDQB2, DRB1= donorDRB1, DRB2= donorDRB2 ,
                            isAvailable = isAvailable, BloodGroup= BloodGroup, DateOfBirth= date_of_birth )
            db.session.add(new_donor)
            db.session.commit()
            flash('The donor has been added successfull!', 'success')
            return redirect(url_for('views.donor'))
        else :
            flash('The donor ID already exists!', 'error')

        
    return render_template("Add-Donor.html")


@views.route("/delete_donor/<int:donorID>", methods=["POST"])
@requires_access_level(ACCESS['user'])
def delete_donor(donorID):
    donor = Donor.query.filter_by(DonorID=donorID).first_or_404()
    if donor is not None:
        db.session.delete(donor)
        db.session.commit()
    return redirect(url_for("views.donor"))




@views.route('/Match/<int:donorID>')
@requires_access_level(ACCESS['user'])
@login_required
def mathcing(donorID):
    #get donor 
    donor = Donor.query.filter_by(DonorID=donorID).first()
    if donor is None:
        flash('no donor with this id number!', 'error')
        return redirect(url_for('views.home'))
    else :
        #retive patient 
        patients = Patient.query.filter_by(isPatientOnWaitingList=True)
        #call the intelligent model and return result 
        results ,ranking = matching_result(patients, donor) # the AI model 
        ranking = dict(sorted(ranking.items(), key=lambda x: x[1], reverse=True)) #sort decedning
        #store the result 
        store_histoy(donorID, results, ranking)
    return render_template("MatchResult.html", results = results, ranking=ranking , donor= donor)


@views.route('/Matching/<int:donorid>/<int:id>')
@requires_access_level(ACCESS['user'])
@login_required
def old_mathcing(donorid, id):
    donor = Donor.query.filter_by(DonorID=donorid).first_or_404()
    matching_histories = MatchingHistories.query.filter_by(DonorID=donorid, id=id).all()
    return render_template("old_matching_result.html", matching_histories=matching_histories, donor=donor)


@views.route('/delete_Matching_History/<int:donorid>/<int:id>')
@requires_access_level(ACCESS['user'])
@login_required
def delete_History(donorid, id):
    matching_histories = MatchingHistories.query.filter_by(DonorID=donorid, id=id).all()
    for matching_history in matching_histories:
        db.session.delete(matching_history)
    db.session.commit()
    return redirect(url_for('views.home'))




@views.route("/modify_Donor/<int:donorID>", methods=['GET', 'POST'])
@requires_access_level(ACCESS['user'])
def modify_Donor(donorID):
    donor = Donor.query.filter_by(DonorID=donorID).first_or_404()
    if request.method == 'POST':
        if request.form.get('patinetA1') != "" :
            donor.A1 = request.form.get('patinetA1')
        if request.form.get('patinetA2') != "" :
            donor.A2 = request.form.get('patinetA2')
            
        if request.form.get('patinetB1') != "" :
            donor.B1 = request.form.get('patinetB1')
        if request.form.get('patinetB2') !=  "" :
            donor.B2 = request.form.get('patinetB2')

        if request.form.get('patinetC1') !=  "" :
            donor.C1 = request.form.get('patinetC1')
        if request.form.get('patinetC2') !=  "" :
            donor.C2 = request.form.get('patinetC2')

        if request.form.get('patinetDRB1') !=  "" :
            donor.DRB1 = request.form.get('patinetDRB1')
        if request.form.get('patinetDRB2') !=  "" :
            donor.DRB2 = request.form.get('patinetDRB2')

        if request.form.get('patinetDQA1') != "" :
            donor.DQA1 = request.form.get('patinetDQA1')
        if request.form.get('patinetDQA2') != "" :
            donor.DQA2 = request.form.get('patinetDQA2')

        if request.form.get('patinetDQB1') != "" :
            donor.DQB1 = request.form.get('patinetDQB1')
        if request.form.get('patinetDQB2') != "" :
            donor.DQB2 = request.form.get('patinetDQB2')
       
        input_status = request.form.get('inputStatus')
        print(input_status)
        donor.isAvailable = True if input_status == "option1" or input_status == "Active"  else False
        donor.BloodGroup = request.form.get('bloodGroup')
        donor.DateOfBirth = request.form.get('inputDate')
       
        db.session.commit()
        flash('Donor updated successfully!', 'success')
        return redirect(url_for('views.view_donor', donorID=donor.DonorID))
    return render_template("Modify-Donor.html", donor=donor)


'''--------------------------------------------------------------------------------------------------------'''
'''-------------------------------------------TRANSPLANTATION----------------------------------------------'''
'''--------------------------------------------------------------------------------------------------------'''

@views.route('/transplantation')
@requires_access_level(ACCESS['user'])
@login_required
def transplantation():
    Transplantations = Transplantation.query.all() 
    return render_template("Transplantation.html", Transplantations= Transplantations)

@views.route('/search_transplantation', methods=["POST"])
@requires_access_level(ACCESS['user'])
@login_required
def search_transplantation():
    search_query = request.form['searchQuery']
    Transplantations = Transplantation.query.filter(Transplantation.id.like(f"{search_query}%")).all()
    return render_template("Transplantation.html", Transplantations= Transplantations)



@views.route('/transplantation/<int:transplantationId>')
@requires_access_level(ACCESS['user'])
@login_required
def view_transplantation(transplantationId):
    transplantation = Transplantation.query.filter_by(id=transplantationId).first_or_404()
    return render_template("View-Transplantation.html", transplantation= transplantation)


@views.route('/transplantation/schedule/<int:donorID>-<int:patientID>',  methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def schedule_transplantation(donorID,patientID ):
    
    donor = Donor.query.filter_by(DonorID=donorID).first_or_404()
    patient = Patient.query.filter_by(PatientID=patientID).first_or_404()
    if not donor.isAvailable :
        flash('donor is notAvailable', category='error')
    if request.method == 'POST':
        date = request.form.get('inputDate')
        complications = request.form.get('text')
        new_transplantation= Transplantation(DonorID= donor.DonorID, PatientID=patient.PatientID , DateOfTransplantation= date)
        if complications != None :
            new_transplantation.complications= complications
        db.session.add(new_transplantation)
        donor.isAvailable = False 
        patient.isPatientOnWaitingList= False 
        db.session.add(donor)
        db.session.add(patient)
        db.session.commit()
        flash('Transplantation scheduled successfully!', 'success')
        return redirect(url_for('views.transplantation'))

    return render_template("schedule-transplantation.html",donor=donor, patient=patient)

@views.route("/delete_Transplantation/<int:TransplantationID>", methods=["POST"])
@requires_access_level(ACCESS['user'])
def delete_Transplantation(TransplantationID):
    transplantation = Transplantation.query.filter_by(id=TransplantationID).first_or_404()
    db.session.delete(transplantation)
    db.session.commit()
    flash('Transplantation deleted successfully!', 'success')
    return redirect(url_for("views.transplantation"))

@views.route("/modify_Transplantation/<int:TransplantationID>", methods=['GET', 'POST'])
@requires_access_level(ACCESS['user'])
def modify_Transplantation(TransplantationID):
    transplantation = Transplantation.query.filter_by(id=TransplantationID).first_or_404()
    if request.method == 'POST':
        transplantation.DateOfTransplantation = request.form.get('DateOfTransplantation')
        transplantation.complications = request.form.get('complications')
        db.session.commit()
        flash('Transplantation updated successfully!', 'success')
        return redirect(url_for('views.view_transplantation', transplantationId = transplantation.id))
    return render_template('Modify-transplantation.html', transplantation=transplantation)

'''--------------------------------------------------------------------------------------------------------'''
'''-------------------------------------------PATIENTS-----------------------------------------------------'''
'''--------------------------------------------------------------------------------------------------------'''

@views.route('/patient')
@requires_access_level(ACCESS['user'])
@login_required
def patient():
    patients = Patient.query.all()
    return render_template("Patient.html", patients=patients)



@views.route('/patient_search', methods=['POST'])
@requires_access_level(ACCESS['user'])
@login_required
def patient_search():
    search_query = request.form['searchQuery']
    patients = Patient.query.filter(Patient.PatientID.like(f"{search_query}%")).all()
    return render_template("Patient.html", patients=patients)

@views.route('/patient/add_patient', methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def add_patient():
    if request.method == 'POST':
        patientID = request.form.get('patientID')
        patinetA1 = request.form.get('patinetA1')
        patinetA2 = request.form.get('patinetA2')
        patinetB1 = request.form.get('patinetB1')
        patinetB2 = request.form.get('patinetB2')
        patinetC1 = request.form.get('patinetC1')
        patinetC2 = request.form.get('patinetC2')
        patinetDRB1 = request.form.get('patinetDRB1')
        patinetDRB2 = request.form.get('patinetDRB2')
        patinetDQA1 = request.form.get('patinetDQA1')
        patinetDQA2 = request.form.get('patinetDQA2')
        patinetDQB1 = request.form.get('patinetDQB1')
        patinetDQB2 = request.form.get('patinetDQB2')
        input_status = request.form.get('inputStatus')
        bloodGroup = request.form.get('bloodGroup')
        date_of_birth = request.form.get('inputDate')
        antiA = request.form.get('antiA')
        if antiA=="":
            antiA= None
        antiB = request.form.get('antiB')
        if antiB=="":
            antiB= None
        antiC = request.form.get('antiC')
        if antiC=="":
            antiC= None
        antiDQA = request.form.get('antiDQA')
        if antiDQA=="":
            antiDQA= None
        antiDQB = request.form.get('antiDQB')
        if antiDQB=="":
            antiDQB= None
        antiDR = request.form.get('antiDR')
        if antiDR=="":
            antiDR= None
        is_patient_on_waiting_list = True if input_status == "option1" else False
        patient = Patient.query.filter_by(PatientID=patientID).first()
        if patient is None :
            new_patient = Patient(PatientID=patientID,A1= patinetA1, A2= patinetA2, B1 = patinetB1,B2= patinetB2, C1 = patinetC1, C2  = patinetC2,
                           DQA1 = patinetDQA1, DQA2= patinetDQA2, DQB1= patinetDQB1, DQB2= patinetDQB2, DRB1= patinetDRB1, DRB2= patinetDRB2 ,
                           isPatientOnWaitingList = is_patient_on_waiting_list, BloodGroup= bloodGroup, DateOfBirth= date_of_birth,
                           antiA=antiA , antiB= antiB,antiC= antiC, antiDQA= antiDQA,antiDQB= antiDQB,  antIDR= antiDR )
            db.session.add(new_patient)
            db.session.commit()
            flash('The donor has been added successfull!', 'success')
            return redirect(url_for('views.patient'))
        else :
            flash('The patient ID already exists!', 'error')
    return render_template("Add-Patient.html")



@views.route("/delete_patient/<int:PatientID>", methods=["POST"])
@requires_access_level(ACCESS['user'])
def delete_patient(PatientID):
    patient = Patient.query.filter_by(PatientID=PatientID).first_or_404()
    if patient is not None:
        db.session.delete(patient)
        db.session.commit()
    return redirect(url_for("views.patient"))

@views.route('/patient/<int:PatientID>', methods=['GET','POST'])
@requires_access_level(ACCESS['user'])
@login_required
def view_patient(PatientID):
    patient = Patient.query.filter_by(PatientID=PatientID).first_or_404()
    return render_template("View-Patient.html", patient=patient)

@views.route("/modify_Patient/<int:PatientID>", methods=['GET', 'POST'])
@requires_access_level(ACCESS['user'])
def modify_Patient(PatientID):
    
    patient = Patient.query.filter_by(PatientID=PatientID).first_or_404()
    if request.method == 'POST':

        if request.form.get('patinetA1') != "" :
            patient.A1 = request.form.get('patinetA1')
        if request.form.get('patinetA2') != "" :
            patient.A2 = request.form.get('patinetA2')
            
        if request.form.get('patinetB1') != "" :
            patient.B1 = request.form.get('patinetB1')
        if request.form.get('patinetB2') !=  "" :
            patient.B2 = request.form.get('patinetB2')

        if request.form.get('patinetC1') !=  "" :
            patient.C1 = request.form.get('patinetC1')
        if request.form.get('patinetC2') !=  "" :
            patient.C2 = request.form.get('patinetC2')

        if request.form.get('patinetDRB1') !=  "" :
            patient.DRB1 = request.form.get('patinetDRB1')
        if request.form.get('patinetDRB2') !=  "" :
            patient.DRB2 = request.form.get('patinetDRB2')

        if request.form.get('patinetDQA1') != "" :
            patient.DQA1 = request.form.get('patinetDQA1')
        if request.form.get('patinetDQA2') != "" :
            patient.DQA2 = request.form.get('patinetDQA2')

        if request.form.get('patinetDQB1') != "" :
            patient.DQB1 = request.form.get('patinetDQB1')
        if request.form.get('patinetDQB2') != "" :
            patient.DQB2 = request.form.get('patinetDQB2')
       
        input_status = request.form.get('inputStatus')
       
        patient.isPatientOnWaitingList = True if input_status == "option1" or input_status == "Waiting list"  else False
        patient.BloodGroup = request.form.get('bloodGroup')
        patient.DateOfBirth = request.form.get('inputDate')
        if request.form.get('antiA') is not "" :
            patient.antiA = request.form.get('antiA')
        
        if request.form.get('antiB') != "" :
            patient.antiB = request.form.get('antiB')
        if request.form.get('antiC') != "" :
            patient.antiC = request.form.get('antiC')

        if request.form.get('antiDQA') !="" :
            patient.antiDQA = request.form.get('antiDQA')
        if request.form.get('antiDQB') != "" :
            patient.antiDQB = request.form.get('antiDQB')
        if request.form.get('antiDR') != "" :
            patient.antIDR = request.form.get('antiDR')
       
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('views.view_patient', PatientID=patient.PatientID))
    return render_template("Modify-Patient.html", patient=patient)



'''--------------------------------------------------------------------------------------------------------'''
'''-------------------------------------------other method-----------------------------------------------------'''
'''--------------------------------------------------------------------------------------------------------'''

def store_histoy (donor, results , ranking):
    last_matching_history = db.session.query(func.max(MatchingHistories.id)).scalar()
    new_id = last_matching_history + 1 if last_matching_history else 1
    current_time = datetime.datetime.now()
    user_id = current_user.id
    for key, value in ranking.items():
        new_history_item = MatchingHistories( UserID = user_id ,id= new_id,PatientID = key, DonorID= donor, DateOfTransplantation= current_time, matchingResult=value )
        db.session.add(new_history_item)
        db.session.commit()
    for key, value in results.items():
        new_history_item = MatchingHistories( UserID = user_id ,id = new_id ,PatientID = key, DonorID= donor, DateOfTransplantation= current_time, matchingResult=value )
        db.session.add(new_history_item)
        db.session.commit()
    

@views.route("/view_matching/<int:PatientID>,<int:donorid>,<matchingResult>")
@requires_access_level(ACCESS['user'])
def view_matching(donorid, PatientID, matchingResult):
    patient = Patient.query.filter_by(PatientID=PatientID).first_or_404()
    donor = Donor.query.filter_by(DonorID=donorid).first_or_404()
    return render_template("view_matching.html", patient=patient, donor= donor, matchingResult= matchingResult)
   

