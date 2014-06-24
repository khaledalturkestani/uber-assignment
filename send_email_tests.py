import os
import send_email
import unittest
import tempfile
from flask import json

class SendEmailTests(unittest.TestCase):

    def setUp(self):
        self.db_fd, send_email.app.config['DATABASE'] = tempfile.mkstemp()
        send_email.app.config['TESTING'] = True
        self.app = send_email.app.test_client()
        send_email.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(send_email.app.config['DATABASE'])

    # helper function
    def make_json(self, to, fro, to_e, fro_e, subj, bod):
	return json.dumps({
        		  "to_name":to,
        		  "from_name":fro,
        		  "to":to_e,
        		  "from":fro_e,
        		  "subject":subj,
        		  "body":bod})

    def test_empty_fields(self):
	fields = self.make_json("", "", "", "", "", "")
        rv = self.app.post('/email', 
			   data=fields)
	assert "Error: Email fields cannot be empty" in rv.data
        assert "Error: invalid to/from email address" in rv.data	

    def test_valid_fields_but_invalid_emails(self):
	fields = self.make_json("a","a","invalid","invalid","a","a")
        rv = self.app.post('/email', 
			   data=fields)
	assert "Error: Email fields cannot be empty" not in rv.data
        assert "Error: invalid to/from email address" in rv.data	

    def test_valid_emails_but_invalid_fields(self):
	fields = self.make_json("","","example@example.com","example@example.com","","")
        rv = self.app.post('/email', 
			   data=fields)
	assert "Error: Email fields cannot be empty" in rv.data
        assert "Error: invalid to/from email address" not in rv.data	

    def test_missing_field(self):
	fields = json.dumps({"to_name":"a","from_name":"a","to":"a","from":"a","subject":"a"})
        rv = self.app.post('/email', 
			   data=fields)
	assert "Error: Missing some email fields." in rv.data

    def test_invalid_time(self):
	fields = json.dumps({"to_name":"a","from_name":"a","to":"a","from":"a","subject":"a","body":"a", "datetime":"invalid"})
        rv = self.app.post('/email', 
			   data=fields)
        assert "Error: invalid to/from email address" in rv.data	
	assert "Error: Incorrect time format OR specified time is not in the future" in rv.data

    def test_past_time(self):
        fields = json.dumps({"to_name":"a","from_name":"a","to":"a","from":"a","subject":"a","body":"a", "datetime":"1973-10-12 20:30:00"})
        rv = self.app.post('/email',
                           data=fields)
        assert "Error: invalid to/from email address" in rv.data
        assert "Error: Incorrect time format OR specified time is not in the future" in rv.data


if __name__ == '__main__':
    unittest.main()
