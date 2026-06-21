import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.database import Base, get_db
from app.main import app

# Use a temporary SQLite database for unit tests
db_dir = os.path.join(BASE_DIR, "database")
os.makedirs(db_dir, exist_ok=True)
TEST_DB_PATH = os.path.join(db_dir, "test_clinic.db")
TEST_SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    # Remove existing test DB if any
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed initial test data
    from app.db import seed
    db = TestingSessionLocal()
    try:
        seed.seed_db(db)
    finally:
        db.close()

    yield engine

    # Teardown database after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture(scope="function")
def db_session(setup_test_db):
    engine = setup_test_db
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(setup_test_db):
    engine = setup_test_db
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
