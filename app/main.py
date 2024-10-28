from fastapi import FastAPI
from app.routes import auth,task
from app.db.database import engine, Base


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(task.router)