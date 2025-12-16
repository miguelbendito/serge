from main import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
   
    user = db.session.execute(db.select(User).where(User.email == "admin@example.com")).scalar()
    if not user:
        print("Creating admin user...")
        hashed_password = generate_password_hash(
            "password",
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email="admin@example.com",
            name="Admin",
            password=hashed_password,
        )
        db.session.add(new_user)
        db.session.commit()
        print("User created successfully!")
        print("Email: admin@example.com")
        print("Password: password")
    else:
        print("User already exists.")
