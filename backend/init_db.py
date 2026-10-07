import sys
from os.path import abspath, dirname
sys.path.insert(0, dirname(abspath(__file__)))

from app.core.database import Base, engine, SessionLocal, ensure_user_avatar_column
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.password_reset import PasswordResetToken
from app.models.feedback import PatientFeedback
from app.models.user import User, UserRole


DEFAULT_DEPARTMENTS = [
    {"name": "Cardiology", "description": "Heart, vascular health, and cardiovascular diseases care."},
    {"name": "Neurology", "description": "Brain, nervous system, and neurological disorders specializations."},
    {"name": "Pediatrics", "description": "Comprehensive healthcare for infants, children, and adolescents."},
    {"name": "Orthopedics", "description": "Musculoskeletal system, bone, joint, and spine treatments."},
    {"name": "General Medicine", "description": "Primary healthcare, chronic disease management, and internal medicine."},
    {"name": "Dermatology", "description": "Skin, hair, and nail conditions diagnosis and care."}
]


def seed_database():
    print("Creating database tables if not present...")
    Base.metadata.create_all(bind=engine)
    ensure_user_avatar_column()
    
    db = SessionLocal()
    try:
        # Seed Departments
        print("Seeding initial hospital departments...")
        for dept_data in DEFAULT_DEPARTMENTS:
            existing_dept = db.query(Department).filter(Department.name == dept_data["name"]).first()
            if not existing_dept:
                dept = Department(name=dept_data["name"], description=dept_data["description"])
                db.add(dept)
                print(f"  + Added Department: {dept_data['name']}")
        
        # Seed Default Admin Account
        admin_email = settings.ADMIN_EMAIL.lower()
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            if not settings.ADMIN_PASSWORD:
                raise RuntimeError(
                    "Set ADMIN_PASSWORD in backend/.env before creating the initial admin account."
                )
            admin_user = User(
                full_name="System Administrator",
                email=admin_email,
                phone="+10000000000",
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            print(f"  + Created Default Admin: {admin_email}")

        db.commit()
        print("Database initialization & seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
