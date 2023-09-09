from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User 
from passlib.hash import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

ACCESS = {
    'guest': 0,
    'user': 1,
    'admin': 2
}
@auth.route('/login', methods=['GET', 'POST'])
def login():
    print("ssss")
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password) and user.access == 1 :
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            elif check_password_hash(user.password, password) and user.access == 0:
                flash('your account is not activatied, try again.', category='error')
            elif check_password_hash(user.password, password) and user.access==2  :
                login_user(user, remember=True)
                return redirect(url_for('views.admin'))
            else :
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, last_name=last_name ,  password=generate_password_hash(
                password1, method='sha256')  )
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! wait for authorization', category='success')

    return render_template("sign_up.html", user=current_user)
