from app.db.database import engine, Base
from app.models.user import User  # Import all models here

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()