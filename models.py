# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True, server_default=text("nextval('event_id_seq'::regclass)"))
    should_escalate = Column(String(25))
    country_of_authentication1 = Column(String(25))
    number_successful_logins1 = Column(String(25))
    number_failed_logins1 = Column(String(25))
    source_provider1 = Column(String(50))
    country_of_authentication2 = Column(String(25))
    number_successful_logins2 = Column(String(25))
    number_failed_logins2 = Column(String(25))
    source_provider2 = Column(String(50))
    time_between_authentications = Column(String(25))
    vpn_confidence = Column(String(5))


class EventClicked(Base):
    __tablename__ = 'event_clicked'

    id = Column(Integer, primary_key=True, server_default=text("nextval('event_clicked_id_seq'::regclass)"))
    user = Column(String(50))
    event_id = Column(Integer)
    time_event_click = Column(DateTime)


class EventDecision(Base):
    __tablename__ = 'event_decision'

    id = Column(Integer, primary_key=True, server_default=text("nextval('event_decision_id_seq'::regclass)"))
    user = Column(String(50))
    event_id = Column(Integer)
    escalate = Column(String(15))
    confidence = Column(String(5))
    time_event_decision = Column(DateTime)


class PrequestionnaireAnswer(Base):
    __tablename__ = 'prequestionnaire_answers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('prequestionnaire_answers_id_seq'::regclass)"))
    timestamp = Column(DateTime)
    user = Column(String(50))
    role = Column(String(50))
    exp_researcher = Column(String(50))
    exp_admin = Column(String(50))
    exp_software = Column(String(50))
    exp_security = Column(String(50))
    familiarity_none = Column(Boolean)
    familiarity_read = Column(Boolean)
    familiarity_controlled = Column(Boolean)
    familiarity_public = Column(Boolean)
    familiarity_engineered = Column(Boolean)
    subnet_mask = Column(String(256))
    network_address = Column(String(256))
    tcp_faster = Column(String(256))
    http_port = Column(String(256))
    firewall = Column(String(256))
    socket = Column(String(256))
    which_model = Column(String(256))


class SurveyAnswer(Base):
    __tablename__ = 'survey_answers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('survey_answers_id_seq'::regclass)"))
    timestamp = Column(DateTime)
    user = Column(String(50))
    mental = Column(Integer)
    physical = Column(Integer)
    temporal = Column(Integer)
    performance = Column(Integer)
    effort = Column(Integer)
    frustration = Column(Integer)
    useful_info = Column(Text)
    feedback = Column(Text)


class TrainingEvent(Base):
    __tablename__ = 'training_event'

    id = Column(Integer, primary_key=True, server_default=text("nextval('training_event_id_seq'::regclass)"))
    should_escalate = Column(String(25))
    country_of_authentication1 = Column(String(25))
    number_successful_logins1 = Column(Integer)
    number_failed_logins1 = Column(Integer)
    source_provider1 = Column(String(50))
    country_of_authentication2 = Column(String(25))
    number_successful_logins2 = Column(Integer)
    number_failed_logins2 = Column(Integer)
    source_provider2 = Column(String(50))
    time_between_authentications = Column(Float(53))
    vpn_confidence = Column(String(5))
    rationale = Column(Text)


class TrainingEventDecision(Base):
    __tablename__ = 'training_event_decision'

    id = Column(Integer, primary_key=True, server_default=text("nextval('training_event_decision_id_seq'::regclass)"))
    user = Column(String(50))
    event_id = Column(Integer)
    escalate = Column(String(15))
    confidence = Column(String(5))
    time_event_decision = Column(DateTime)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, server_default=text("nextval('user_id_seq'::regclass)"))
    username = Column(String(50), unique=True)
    group = Column(Integer)
    time_begin = Column(DateTime)
    time_end = Column(DateTime)
    events = Column(String(256))
    questionnaire_complete = Column(Boolean)
    training_complete = Column(Boolean)
    experiment_complete = Column(Boolean)
    survey_complete = Column(Boolean)
    completion_code = Column(String(6))
