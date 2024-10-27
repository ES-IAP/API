import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer
from app.main import app
from app.db.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import NewUser
from app.crud.user import create_user, get_user_by_email, get_user_by_cognito_id

@pytest.fixture(scope="module")
def setup():
    my_sql_test_container = MySqlContainer(
        "mysql:5.7",
        root_password="test_root_password",
        dbname="test_db",
        username="test_user",
        password="test_password"
    ).with_bind_ports(3306, 3307)

    my_sql_test_container.start()
    print("MySQL container started.")
    time.sleep(10)

    connection_url = my_sql_test_container.get_connection_url()
    engine = create_engine(connection_url, connect_args={})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    UserModel.metadata.create_all(engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield SessionLocal

    my_sql_test_container.stop()
    print("MySQL test container stopped.")

@pytest.fixture(name="test_db", scope="module")
def create_test_db(setup):
    db = setup()
    yield db
    db.close()

@pytest.fixture(name="test_user", scope="function")
def create_test_user(test_db):
    test_user = UserModel(
        id=3,
        username="username1",
        email="email1@gmail.com",
        cognito_id="cognito_id1",
    )
    test_db.add(test_user)
    test_db.commit()  
    yield test_user  
    test_db.delete(test_user)  
    test_db.commit()  

def test_create_user(test_db):
    user_data = NewUser(
        cognito_id="id2",
        username="username2",
        email="email2@gmail.com",
    )
    created_user = create_user(user_data, test_db)
    assert created_user is not None
    assert created_user.username == "username2"
    assert created_user.email == "email2@gmail.com"
    assert created_user.cognito_id == "id2"

def test_get_user_by_email_found(test_db, test_user):
    found_user = get_user_by_email(test_user.email, test_db)
    assert found_user is not None
    assert found_user.id == test_user.id

def test_get_user_by_email_not_found(test_db):
    found_user = get_user_by_email("not_exist@email.com", test_db)
    assert found_user is None

def test_get_user_by_cognito_id_found(test_db, test_user):
    found_user = get_user_by_cognito_id(test_user.cognito_id, test_db)
    assert found_user is not None
    assert found_user.id == test_user.id

def test_get_user_by_cognito_id_not_found(test_db):
    found_user = get_user_by_cognito_id("not_exist_id", test_db)
    assert found_user is None
