from flask import Flask,render_template,request, flash,redirect, url_for, jsonify
from config import client
from models import *
from flask_mail import Mail,Message
import secrets
from random import randint
import datetime
import json
# from werkzeug import generate_password_hash, check_password_hash
from werkzeug import *
#Upload images
import base64
from io import BytesIO
from PIL import Image
import os
from werkzeug.utils import secure_filename
import paypalrestsdk
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
app.secret_key='super_secret_key'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='saralkumar28@gmail.com'
app.config['MAIL_PASSWORD']='*********'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True


#Paypal Payments info
paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AY7CkFftQBhLyElnVFFlC7-JBcs33NkripACHrfwXkMZrEcdt1PmfpDnloCKAOnWnEKUG55WMGmhLLk3",
  "client_secret": "EBBUBQS3o2fK7u0fkwq152noTvvby_oNwH3IG8p8oIFHBHOqaWsbrXDIDP8HbQ7yGb-wCQG8-sFxzHSp" })



mail=Mail(app)

UPLOAD_FOLDER = './upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_and_save(userName,email,image_data):
    image_data=bytes(image_data,encoding="ascii")
    # im=Image.open(BytesIO)
    im = Image.open(BytesIO(base64.b64decode(image_data)))
    rgb_im = im.convert('RGB')
    imageName=userName + '.png'
    rgb_im.save(os.path.join(app.config['UPLOAD_FOLDER'], imageName))
    queryset = AdminRegister.objects.get(email__iexact=email)
    queryset.image=imageName
    queryset.save()
    return imageName

@app.route("/paymentPage")
def paymentPage():
    return render_template("payment/paypal.html")

@app.route("/payment",methods=['POST'])
def payment():
    payment = paypalrestsdk.Payment({
    "intent": "sale",
    "payer": {
        "payment_method": "paypal"},
    "redirect_urls": {
        "return_url": "http://localhost:3000/payment/execute",
        "cancel_url": "http://localhost:3000/"},
    "transactions": [{
        "item_list": {
            "items": [{
                "name": "testitem",
                "sku": "item",
                "price": "5.00",
                "currency": "USD",
                "quantity": 1}]},
        "amount": {
            "total": "5.00",
            "currency": "USD"},
        "description": "This is the payment transaction description."}]})
    if payment.create():
        print("Payment success")
        print(payment.id)

    else:
        print(payment.error)
        
    print("-----")
    return payment.id 

@app.route("/execute",methods=['POST'])
def execute():
    success = False
    payment=paypalrestsdk.Payment.find(request.form['paymentID'])

    if payment.execute({'payer_id': request.form['payerID']}):
        print("Execute success")
        success = True
    else:
        print(payment.error)
    # return "success"
    print("print success")

# @app.route("/dashboard")
# def dashboard():
#     return render_template("admin/admin_dashboard.html")





@app.route("/applyATM",methods=['POST','GET'])
def indexPage():
    firstName = request.form.get("firstName")
    lastName = request.form.get("lastName")
    emailId = request.form.get("emailId")
    status=1
    createdOn=datetime.datetime.now()

    if firstName and lastName and emailId and request.method=="POST":
        try:

            queryset = AtmHolderRegister.objects(emailId__iexact=emailId)
            if queryset:
                flash("Email already Exists!!!")
                return render_template("atm_holder_register.html")
        except Exception as e:
            pass    
        holder_data = AtmHolderRegister(
            firstName = firstName,
            lastName = lastName,
            emailId = emailId,
            
            registerNumber = randint(1111111111,9999999999),
            otp = randint(0000,9999),
            link = secrets.token_urlsafe(),
            status = status,
            createdOn = createdOn
            )
        
        holder_info = holder_data.save()
        if holder_info:
            login_details={
                    "firstName":holder_info.firstName + holder_info.lastName,
                    "link":holder_info.link,
                    "registerNumber":holder_info.registerNumber,
                    "otp":holder_info.otp
            }

            if True:
                msg=Message('Welcome to Secure Space ATM SUPER VISION',sender='saralkumar28@gmail.com',recipients=[holder_info.emailId])
                msg.html=render_template("email_temp.html",login_details=login_details)
                mail.send(msg)
                flash("Registration Successfully Completed!!!, Please Check Your Email")
                return render_template("atm_holder_register.html")
            else:
                flash("Required fields are missing!!!")
                return render_template("atm_holder_register.html")    
    else:
        return render_template("atm_holder_register.html")

@app.route("/atmHolderLogin/<link>", methods=["POST","GET"])
def atmHolderLoginPage(link):
    registerNumber = request.form.get("registerNumber")
    otp = request.form.get("otp")
    if registerNumber and otp and request.method=="POST":
        try:
            get_reg_details=AtmHolderRegister.objects.get(registerNumber__exact=registerNumber,otp__exact=otp,status__in=[1])
            if get_reg_details:
                return redirect(url_for('atmHolderNextStepRegistrationPage',link=link,d=get_reg_details.registerNumber))

            else:
                flash("Invalid Credentials!!!")
                return render_template("atm_holder_login.html")
        except AtmHolderRegister.DoesNotExist as e:
            # raise e
            flash("Invalid Credentials!!")
            return render_template("atm_holder_login.html")
                
            
    else:
        #flash("Required Fields are Missing!!!")    
        return render_template("atm_holder_login.html")

@app.route("/atmHolderNextStepRegistration/<link>",methods=["POST","GET"])
def atmHolderNextStepRegistrationPage(link):
    fullName = request.form.get("fullName",None)
    surName = request.form.get("surName",None)
    fatherName = request.form.get("fatherName",None)
    motherName = request.form.get("motherName",None)
    mobileNumber = request.form.get("mobileNumber",None)
    alternatePhone = request.form.get("alternatePhone",None)
    birthday = request.form.get("birthday",None)
    gender = request.form.get("gender",None)
    alternateEmail = request.form.get("alternateEmail",None)
    # aadharCard = request.file["aadharCard"]
    panCard = request.form.get("panCard",None)
    aadharCardNumber = request.form.get("aadharCardNumber",None)
    panCardNumber = request.form.get("panCardNumber",None)
    photo = request.form.get("photo",None)
    signature = request.form.get("signature",None)
    houseNumber = request.form.get("houseNumber",None)
    villageName = request.form.get("villageName",None)
    cityTown = request.form.get("cityTown",None)
    mandalName = request.form.get("mandalName",None)
    districtName = request.form.get("districtName",None)
    stateName = request.form.get("stateName",None)
    pinCode = request.form.get("pinCode",None)
    countryName = request.form.get("countryName",None)
    # ?registerOn = datetime.datetime.now()
    status=2
    if request.method=="POST":  
        try:
            holder_updated_data=AtmHolderRegister.objects.get(link=link)
            if holder_updated_data:
                holder_data=holder_updated_data.update(
                    fullName=fullName,
                    surName=surName,
                    fatherName=fatherName,
                    motherName=motherName,
                    mobileNumber=mobileNumber,
                    alternatePhone=alternatePhone,
                    birthday=birthday,
                    gender=gender,
                    alternateEmail=alternateEmail,
                    # aadharCard=aadharCard,
                    panCard=panCard,
                    aadharCardNumber=aadharCardNumber,
                    panCardNumber=panCardNumber,
                    photo=photo,
                    signature=signature,
                    houseNumber=houseNumber,
                    villageName=villageName,
                    cityTown=cityTown,
                    mandalName=mandalName,
                    districtName=districtName,
                    stateName=stateName,
                    pinCode=pinCode,
                    countryName=countryName,
                    status=status
                    )

                # if holder_data:
                #     return "saved"
                # if holder_data:
                #     if aadharCard.filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS:
                #         ext = aadharCard.filename.rsplit('.',1)[1].lower()
                #         file_name = str(aadharCardNumber)+"."+ext
                #         if not os.path.exists(app.config['UPLOAD_FOLDER']+"/upload"):
                #             os.mkdir(app.config['UPLOAD_FOLDER']+"/upload")
                #         aadhar_card_image = app.config['UPLOAD_FOLDER']+"/upload"
                #         aadharCard.save(os.path.join(aadhar_card_image,file_name))
                #     holder_data.update(image=file_name)    
        except Exception as e:
            raise e
               
    return render_template("atm_holder_next_step_reg.html")


@app.route("/adminRegister", methods=["POST","GET"])
def adminRegisterPage():
    userName = request.form.get("userName",None)
    email = request.form.get("email",None)
    password = request.form.get("password",None)
    image = request.form.get("image",None)
    status = 1
    createdOn = datetime.datetime.now()

    if userName and email and password and status and image and request.method=="POST":
        try:
            admin_query = AdminRegister.objects.get(email__iexact=email)
            if admin_query:
                flash("Admin Email Id already exists")
                return render_template("admin/admin_register.html")
        except Exception as e:
            pass
        admin_data = AdminRegister(
        userName = userName,
        email = email,
        password = password,
        image = image,
        createdOn = createdOn,
        status = status
        )
        admin_created=admin_data.save()
        if admin_created:
            # convert_and_save(userName,email,image)
            # return redirect(url_for("completeViewDataPage"))
            return "created"
        else:
            return "soming"
    else:
        return render_template("admin/admin_register.html")

@app.route("/completeViewData",methods=['GET'])
def completeViewDataPage():
    get_all_data=AtmHolderRegister.objects(status__in=[2,3])
    get_data_list=[]
    if get_all_data:
        for data in get_all_data:
            get_data_dict={
            "fullName":data.fullName,
            "registerNumber":data.registerNumber,
            "emailId":data.emailId,
            "mobileNumber":data.mobileNumber,
            "status":data.status,
            }
            get_data_list.append(get_data_dict)

            print(get_data_list)

        return render_template("admin/complete_view.html",holder_data=get_data_list)

@app.route("/adminDashboard",methods=['GET'])
def adminDashboardPage():
    get_all_data=AtmHolderRegister.objects(status__in=[1,2,3])
    get_data_list=[]
    if get_all_data:
        for data in get_all_data:
            get_data_dict={
               "fullName":data.fullName,
               "registerNumber":data.registerNumber,
               "emailId":data.emailId,
               "mobileNumber":data.mobileNumber,
               "status":data.status,

            }
            get_data_list.append(get_data_dict)

        return render_template("admin/admin_dashboard.html",holder_data=get_data_list)

@app.route("/holderVerification/<registerNumber>",methods=['GET'])
def holderVerificationPage(registerNumber):
    verification_data=AtmHolderRegister.objects.get(registerNumber=registerNumber)
    
    if verification_data.status==3:
        # flash("already")
        return "already Verified"
    else:
        verification_data=AtmHolderRegister.objects.get(registerNumber=registerNumber)
        #verify_data_list=[]
        if verification_data.status==2:
        
            verify_data_dict={
            "fullName":verification_data.fullName,
            "registerNumber":verification_data.registerNumber,
            "fatherName":verification_data.fatherName,
            "motherName":verification_data.motherName,
            "photo":verification_data.photo,
            "signature":verification_data.signature,
            "gender":verification_data.gender,
            "mobileNumber":verification_data.mobileNumber,
            "aadharCardNumber":verification_data.aadharCardNumber,
            "aadharCard":verification_data.aadharCard,
            "panCardNumber":verification_data.panCardNumber,
            "panCard":verification_data.panCard,
            "alternateEmail":verification_data.alternateEmail,
            "alternatePhone":verification_data.alternatePhone,
            "birthday":verification_data.birthday,
            "cityTown":verification_data.cityTown,
            "countryName":verification_data.countryName,
            "districtName":verification_data.districtName,
            "houseNumber":verification_data.houseNumber,
            "mandalName":verification_data.mandalName,
            "pinCode":verification_data.pinCode,
            "villageName":verification_data.villageName,
            "stateName":verification_data.stateName,


            }

            return render_template("admin/holder.html",verify_data=verify_data_dict)


@app.route("/atmCardGeneration/<registerNumber>",methods=["POST","GET"])
def atmCardGenerationPage(registerNumber):
    card_data_dict={}
    if request.method=="GET":
        generate_card=AtmHolderRegister.objects.get(registerNumber=registerNumber)
        # print(generate_card.fullName)
        if generate_card:
            digit1=randint(1000,9999)
            digit2=randint(1000,9999)
            digit3=randint(1000,9999)
            digit4=randint(1000,9999)
            cvv=randint(100,999)
            pinNumber=randint(1000,9999)
            month=int(generate_card.createdOn.strftime("%m")) + 5
            year=int(generate_card.createdOn.strftime("%Y")) + 7
            validDate = str(month) +"/"+str(year)
            status=3
            card_data=generate_card.update(
                digit1=str(digit1),
                digit2=str(digit2),
                digit3=str(digit3),
                digit4=str(digit4),
                cvv=str(cvv),
                pinNumber=str(pinNumber),
                validDate=validDate,
                status=status
            )
                                 
            if card_data:
                # print(card_data.fullName)
                card_data_dict={
                "digit1":digit1,
                "digit2":digit2,
                "digit3":digit3,
                "digit4":digit4,
                "cvv":cvv,
                "validDate":validDate,
                "holderName":generate_card.fullName,
                
                
                }

    return render_template("atm_card.html",final_data=card_data_dict)   

@app.route("/dummy")
def dummy():
    return render_template("dummy.html")

   

if __name__=="__main__":
    app.run(debug=True)
