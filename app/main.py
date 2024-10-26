from fastapi import FastAPI
from app.routes import auth
from app.db.database import engine, Base


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)