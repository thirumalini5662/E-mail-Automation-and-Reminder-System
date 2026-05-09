from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
import uuid, datetime as dt

app = FastAPI()

engine = create_engine("sqlite:///db/email.db", future=True)

class Contact(BaseModel):
    name: str
    email: EmailStr

class Template(BaseModel):
    name: str
    subject: str
    body_md: str

class Campaign(BaseModel):
    name: str
    template_id: str
    sender_name: str
    sender_email: EmailStr

class Reminder(BaseModel):
    title: str
    contact_id: str
    campaign_id: str
    start_at_utc: str

@app.get("/")
def home():
    return {"status": "API running"}

@app.post("/contacts")
def create_contact(c: Contact):
    with engine.begin() as db:
        cid = str(uuid.uuid4())
        db.execute(text("INSERT INTO contacts(id,name,email) VALUES(:i,:n,:e)"),
                   dict(i=cid,n=c.name,e=c.email))
        return {"id": cid}

@app.post("/templates")
def create_template(t: Template):
    with engine.begin() as db:
        tid = str(uuid.uuid4())
        db.execute(text("INSERT INTO templates(id,name,subject,body_md,created_at) VALUES(:i,:n,:s,:b,:ts)"),
                   dict(i=tid,n=t.name,s=t.subject,b=t.body_md,ts=dt.datetime.utcnow()))
        return {"id": tid}

@app.post("/campaigns")
def create_campaign(c: Campaign):
    with engine.begin() as db:
        cid = str(uuid.uuid4())
        db.execute(text("INSERT INTO campaigns(id,name,template_id,sender_name,sender_email,created_at) VALUES(:i,:n,:t,:sn,:se,:ts)"),
                   dict(i=cid,n=c.name,t=c.template_id,sn=c.sender_name,se=c.sender_email,ts=dt.datetime.utcnow()))
        return {"id": cid}

@app.post("/reminders")
def create_reminder(r: Reminder):
    with engine.begin() as db:
        rid = str(uuid.uuid4())
        db.execute(text("INSERT INTO reminders(id,title,contact_id,campaign_id,start_at_utc,active) VALUES(:i,:t,:ct,:ca,:st,1)"),
                   dict(i=rid,t=r.title,ct=r.contact_id,ca=r.campaign_id,st=r.start_at_utc))
        return {"id": rid}