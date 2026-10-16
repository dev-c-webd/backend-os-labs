from fastapi import FastAPI, Depends
from app.core.config import settings
from sqlalchemy.orm import Session
from app.db.database import get_db

from sqlalchemy import text

app = FastAPI(title=settings.app_name)

@app.get("/")
def run_get():
    return "setup initial" 

@app.get("/check")
def health_check(db : Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    # result.scalar_one()
    print(result.scalar_one())
    return {"status": "ok"}