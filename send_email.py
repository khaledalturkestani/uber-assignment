from flask import Flask, request, make_response, render_template, json 
import requests
import re
import mandrill
import datetime
from sent_emails_db import db_session, init_db
from models import SentEmail
import time
import calendar
from email import utils


app = Flask(__name__)

# Mailgun variabls:
mailgun_key = "mailgun_api_key"
mailgun_server = "mailgun_sandbox_server"

# Mandrill variables:
mandrill_key = "mandrill_api_key"

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route("/")
def display_form():
    return render_template("form.html")
   
@app.route("/email", methods=["POST"])
def send_email():
    email_fields = json.loads(request.data)
    errors = []
    fields_validated = validate_fields(email_fields, errors)

    # Return 400 status if fields are not valid
    if not fields_validated:
    	return make_response(json.dumps(errors), "400", {})

    # Send via Mailgun first:
    mailgun_response = send_via_mailgun(email_fields)
    if mailgun_response.status_code == 200:
	email_fields["service"] = "mailgun"
	email_fields["service_response"] = json.dumps(mailgun_response.json())
	save_to_db(email_fields)
    	return make_response("Success")
    
    # Mailgun failed -- Send via Mailgun:
    mandrill_response = send_via_mandrill(email_fields)
    if mandrill_response[0]["status"] not in ("rejected", "invalid"):
	email_fields["service"] = "mandrill"
	email_fields["service_response"] = json.dumps(mandrill_response[0])
	save_to_db(email_fields)
    	return make_response("success")

    return make_response("Both email services failed", "502", {})
 
def send_via_mailgun(fields):
    data = {"from": fields["from_name"] + " <" + fields["from"] + ">",
              "to": fields["to_name"] + " <" + fields["to"] + ">",
              "subject": fields["subject"],
              "html": fields["body"]}

    if fields.has_key("datetime") and len(fields["datetime"]) != 0:
	delayed_t = datetime.datetime.strptime(fields["datetime"], '%Y-%m-%d %H:%M:%S')
        delayed_t_tuple = delayed_t.timetuple()
	delayed_t_stamp = calendar.timegm(delayed_t_tuple)
        t = utils.formatdate(delayed_t_stamp)
	data["o:deliverytime"] = t
    
    return requests.post(
        mailgun_server,
        auth=("api", mailgun_key),
	data=data)

def send_via_mandrill(fields):
 
    try:
    	mandrill_client = mandrill.Mandrill(mandrill_key)
    	message = {
	  "from_email": fields["from"],
   	  "from_name": fields["from_name"],
          "to": [{"email": fields["to"],
                 "name": fields["to_name"]}],
	  "subject": fields["subject"],
   	  "html": fields["body"]} 

        if fields.has_key("datetime") and len(fields["datetime"]) != 0:
	    result = mandrill_client.messages.send(message=message, async=False, ip_pool="Main Pool", send_at=fields["datetime"])
	else: # Note: delayed sending costs money --> only use "send_at" parameter when we're actually scheduling an email
	    result = mandrill_client.messages.send(message=message, async=False, ip_pool="Main Pool")

	return result

    except mandrill.Error, e:
    	print "A mandrill error occurred: %s - %s" % (e.__class__, e)
    	raise

def save_to_db(f):
    if f.has_key("datetime") and len(f["datetime"]) != 0:
	f["datetime"] = datetime.datetime.strptime(f["datetime"], '%Y-%m-%d %H:%M:%S')
    else:
	f["datetime"] = None

    email_model = SentEmail(f["to_name"], f["to"], f["from_name"], f["from"], f["subject"], f["body"], f["service"], f["service_response"], f["datetime"])
    db_session.add(email_model)
    db_session.commit()

# Checks that 1) all fields are not empty strings, 2) emails must have a valid format, 
# and 3) 
def validate_fields(f,errors):
    try:
	ret_val = True
	if len(f["to_name"]) == 0 or len(f["from_name"]) == 0 or len(f["subject"]) == 0 or len(f["body"]) == 0:
	    errors.append("Error: Email fields cannot be empty.")
	    ret_val = False

	if not is_valid_email(f["to"]) or not is_valid_email(f["from"]):
	    errors.append("Error: invalid to/from email address")
	    ret_val = False

	if f.has_key("datetime") and len(f["datetime"]) == 0:
	    pass

	elif f.has_key("datetime") and not is_valid_time(f["datetime"]):
	    errors.append("Error: Incorrect time format OR specified time is not in the future")
	    ret_val = False

	return ret_val

    except KeyError:
	errors.append("Error: Missing some email fields.")
	return False

# Simple validation. Checks that theres only one @ followed by a .
def is_valid_email(email):
	if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
	    return False
	return True

def is_valid_time(timetext):
    try:
	current_time = datetime.datetime.utcnow()
        time = datetime.datetime.strptime(timetext, '%Y-%m-%d %H:%M:%S')
	if current_time > time:
	    return False
	return True
    except ValueError:
	return False       

if __name__ == "__main__":
    app.debug = True # or: app.run(debug=True).
    init_db()
    app.run(host="0.0.0.0")
