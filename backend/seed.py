from app.database import Base, SessionLocal, engine
from app.services.transit import seed_database


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        print("PostgreSQL seed complete.")
    finally:
        db.close()
