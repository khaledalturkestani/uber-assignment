from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import validates
from sent_emails_db import Base
import re

class SentEmail(Base):
    __tablename__ = "sent_emails"
    id = Column(Integer, primary_key=True)
    to_name = Column(String(80), nullable=False)
    to_email = Column(String(80), nullable=False)
    from_name = Column(String(80), nullable=False)
    from_email = Column(String(80), nullable=False)
    subject = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    service = Column(String(80), nullable=False)
    service_response = Column(Text, nullable=False)
    scheduled_time = Column(DateTime)

    # Simple validation. Checks that theres only one @ followed by a .
    # TODO: check regex
    @validates("to_email", "from_email")
    def validate_email(self, key, address):
        assert re.match(r"[^@]+@[^@]+\.[^@]+", address)
        return address

    def __init__(self, to_name, to_email, from_name, from_email, subject, body, service, service_response, datetime):
        self.to_name = to_name
        self.to_email = to_email
        self.from_name = from_name
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.service = service
        self.service_response = service_response
	self.scheduled_time = datetime
