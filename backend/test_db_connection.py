import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def test_connection():
    try:
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("DATABASE CONNECTION SUCCESSFUL")
            print(f"PostgreSQL version: {version}")

        return True

    except Exception as e:
        print("DATABASE CONNECTION FAILED")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\nReady to set up migrations!")
    else:
        print("\nCheck your database connection settings.")