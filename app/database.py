from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import time

DATABASE_URL = "postgresql://foo:foo@localhost:5432/foodb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        print("Error on db retrieve")
    finally:
        db.close()
        
def init_db():
    """Initialize database with retries"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            Base.metadata.create_all(bind=engine)
            print("Database connected and tables created successfully!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("Failed to connect to database after all retries!")
                raise