import os
import sys
from passlib.context import CryptContext

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import SessionLocal, engine
from db.models import Base, User, Student

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Seed admin
    if not db.query(User).filter(User.username == "admin").first():
        hashed = pwd_context.hash("admin123")
        admin = User(username="admin", password_hash=hashed, role="researcher")
        db.add(admin)
    
    # Seed 15 students
    for i in range(1, 16):
        code = f"STU{i:03d}"
        if not db.query(Student).filter(Student.access_code == code).first():
            student = Student(access_code=code, name=f"طالب {i}")
            db.add(student)
            
    db.commit()
    db.close()
    print("Seeding completed successfully.")

if __name__ == "__main__":
    seed()
