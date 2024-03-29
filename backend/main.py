from fastapi import FastAPI, HTTPException, Depends, UploadFile
from typing import List
from src.database import SessionLocal, engine
from sqlalchemy.orm import Session
from src import models, schemas, methods

import nltk
nltk.download('stopwords', './static')
nltk.download('punkt', './static')

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# placeholder logged in user
curr_user_id: int = 2

@app.get("/")
def home():
    return {"Hello": "World"}

@app.post("/user/create", response_model=schemas.User)
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    check_user = db.query(models.User).filter(models.User.username == user.username).first()
    if(check_user):
        raise HTTPException(409, 'Username already taken!')
    else:
        return methods.create_user(user, db)

@app.post("/user/sessions")
def auth_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    return methods.authenticate_user(user, db)

@app.post("/user/{username}/score", response_model=schemas.UserScores)
def add_score(username: str, create_score: schemas.UserScoresCreate, db: Session = Depends(get_db)):
    check_user = db.query(models.User).filter(models.User.username == username).first()
    if(not check_user):
        raise HTTPException(404, 'User Does Not Exist!')
    else:
        return methods.add_score(username, create_score, db)
    
@app.post("/user/{username}/resume")
def upload_resume(username: str, file: UploadFile, db: Session = Depends(get_db)):
    check_user = db.query(models.User).filter(models.User.username == username).first()
    if(not check_user): # check if the user exists, if they do not exist then throw an error
        raise HTTPException(404, 'User Does Not Exist!')
    
    else: # if they do exist, and the file format is docx then store the file as {username}_resume.docx in the static folder
        # check for document type
        if file.content_type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            raise HTTPException(415, "Unsupported filetype. Only '.docx' files are accepted! ")
        
        else:
            file_location = f"./static/{username}_resume.docx"
            with open(file_location, mode='wb') as new_file:
                new_file.write(file.file.read())
            return {"User": "Valid", "Path": file_location}

@app.post("/user/{username}/keywords")
def get_keywords(username: str, job_desc: schemas.JobDesc, db: Session = Depends(get_db)):
    resume_keywords = methods.extract_keywords_from_docx(username, db)
    job_desc_keywords = methods.extract_keywords_from_job_desc_text(username, job_desc.text, db)
    return methods.extract_common_keywords(resume_keywords=resume_keywords,
                                           job_desc_keywords=job_desc_keywords)

@app.get("/user/score", response_model=List[schemas.UserScores])
def get_user_scores(db: Session = Depends(get_db)):
    return db.query(models.UserScores).filter(models.UserScores.user_id == curr_user_id).all()