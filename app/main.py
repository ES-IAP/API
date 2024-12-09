from fastapi import FastAPI
from app.routes import auth,task
from app.db.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(task.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the To-Do List API"}