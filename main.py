from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
from flask_mail import Mail
import json
from sqlalchemy.orm import sessionmaker


with open('config.json','r') as c:
    params = json.load(c)["params"]
    
# Database connection
local_server = True
app = Flask(__name__)
app.secret_key = '123456789'


# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

# SMTP MAIL SERVER SETTINGS

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure the database URI
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/hms'
else:
    # Add configuration for your production server
    pass

db = SQLAlchemy(app)

# Define database models
# here we will create db models that is tables
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))
 
class Patients(db.Model):
    pid=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    name=db.Column(db.String(50))
    gender=db.Column(db.String(50))
    slot=db.Column(db.String(50))
    disease=db.Column(db.String(50))
    time=db.Column(db.String(50),nullable=False)
    date=db.Column(db.String(50),nullable=False)
    dept=db.Column(db.String(50))
    number=db.Column(db.String(50))
    
    
class Doctors(db.Model):
    did=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    doctorname=db.Column(db.String(50))
    dept=db.Column(db.String(50))  
    
class Trigr(db.Model):
    tid=db.Column(db.Integer,primary_key=True)
    pid=db.Column(db.Integer)
    email=db.Column(db.String(50))
    name=db.Column(db.String(50))
    action=db.Column(db.String(50))
    time=db.Column(db.String(50))
   

# Define routes
@app.route('/')   # End point
def index():
    return render_template('index.html')

@app.route('/doctors',methods=['POST','GET'])
def doctors():

    if request.method=="POST":

        email=request.form.get('email')
        doctorname=request.form.get('doctorname')
        dept=request.form.get('dept')

        query=text(f"INSERT INTO `doctors` (`email`,`doctorname`,`dept`) VALUES ('{email}','{doctorname}','{dept}')")
        try:
            # Execute the query
            db.session.execute(query)

            # Commit the transaction to persist the changes
            db.session.commit()
            flash("Information is Stored","primary")
        except Exception as e:
            # If an error occurs, roll back the transaction and display an error message
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('doctors.html')


@app.route('/patients', methods=['POST', 'GET'])
@login_required
def patient():
    doct_query = text("SELECT * FROM `doctors`")
    doct = db.session.execute(doct_query)

    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        gender = request.form.get('gender')
        slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        number = request.form.get('number')
        subject = "HOSPITAL MANAGEMENT SYSTEM"

        query = text(
            f"INSERT INTO `patients` (`email`, `name`, `gender`, `slot`, `disease`, `time`, `date`, `dept`, `number`) VALUES (:email, :name, :gender, :slot, :disease, :time, :date, :dept, :number)"
        )
        try:
            db.session.execute(query, {
                'email': email,
                'name': name,
                'gender': gender,
                'slot': slot,
                'disease': disease,
                'time': time,
                'date': date,
                'dept': dept,
                'number': number
            })
            db.session.commit()
            # mail.send_message(subject, sender=params['gmail-user'], recipients=[email],
            #                    body=f"YOUR BOOKING IS CONFIRMED. THANKS FOR CHOOSING US.\nYour Entered Details are:\nName: {name}\nSlot: {slot}")
            flash("Booking Confirmed", "info")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('patients.html', doct=doct)

@app.route('/bookings')
@login_required
def bookings():
    em = current_user.email
    conn = db.engine.connect()
    query = conn.execute(text(f"SELECT * FROM `patients` WHERE email='{em}'"))
    conn.close()
    return render_template('bookings.html', query=query)


@app.route("/edit/<string:pid>",methods=['POST','GET'])
@login_required
def edit(pid):
    posts=Patients.query.filter_by(pid=pid).first()
    if request.method=="POST":
        email=request.form.get('email')
        name=request.form.get('name')
        gender=request.form.get('gender')
        slot=request.form.get('slot')
        disease=request.form.get('disease')
        time=request.form.get('time')
        date=request.form.get('date')
        dept=request.form.get('dept')
        number=request.form.get('number')
        query=text(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid}")
        try:
            db.session.execute(query)
            db.session.commit()
            flash("Slot is Updated","success")
            return redirect('/bookings')
        except Exception as e:
            # If an error occurs, roll back the transaction and display an error message
            db.session.rollback()
            
    
    return render_template('edit.html',posts=posts)


@app.route("/delete/<string:pid>",methods=['POST','GET'])
@login_required
def delete(pid):
    query=text(f"DELETE FROM `patients` WHERE `patients`.`pid`={pid}")
    try:
            db.session.execute(query)
            db.session.commit()
    except Exception as e:
            # If an error occurs, roll back the transaction and display an error message
            db.session.rollback()
    return redirect('/bookings')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        # Hash the password before saving it
        encpassword = generate_password_hash(password)

        # Create a new User object
        new_user = User(username=username, email=email, password=encpassword)

        # Add the new user to the database session
        db.session.add(new_user)

        # Commit the changes to the database
        db.session.commit()

        flash("Signup Successful! Please Login", "success")
        return redirect('/login')  # Redirect to the login page after signup

    return render_template('signup.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Success","primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","danger")
            return render_template('login.html')    





    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))

@app.route('/test')  # End point
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'
    

@app.route('/details')
@login_required
def details():
    posts=Trigr.query.all()
    #query=text("SELECT * FROM `trigr`")
    # try:
    #         db.session.execute(query)
    #         db.session.commit()
    # except Exception as e:
    #         # If an error occurs, roll back the transaction and display an error message
    #         db.session.rollback()
    return render_template('trigers.html',posts=posts)
  
@app.route('/search',methods=['POST','GET'])
@login_required
def search():
    if request.method=="POST":
        query=request.form.get('search')
        dept=Doctors.query.filter_by(dept=query).first()
        name=Doctors.query.filter_by(doctorname=query).first()
        if name:

            flash("Doctor is Available","info")
        else:

            flash("Doctor is Not Available","danger")
    return render_template('index.html')
    

# Run the application
if __name__ == '__main__':
    app.run(debug=True)

