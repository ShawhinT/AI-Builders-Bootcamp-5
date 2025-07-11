from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from openai import OpenAI
import os

# SQLAlchemy setup - using SQLite file database
# Use environment variable for database path or default to ./test.db
db_path = os.getenv("SQLITE_DB_PATH", "./test.db")
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="messages")

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic models for request validation
class UserCreate(BaseModel):
    username: str
    email: str  # Added email field
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        return value

class MessageCreate(BaseModel):
    content: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User creation endpoint
@app.post("/users")
def create_user_controller(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user in database
    new_user = User(username=user.username, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Add a welcome message for the new user
    welcome_msg = Message(content=f"Welcome, {new_user.username}!", user_id=new_user.id)
    db.add(welcome_msg)
    db.commit()
    
    return {"name": user.username, "message": "Account successfully created"}

# Create a message for a user
@app.post("/users/{email}/messages")
def create_message(email: str, message: MessageCreate, db: Session = Depends(get_db)):
    # Find the user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create a new message
    new_message = Message(content=message.content, user_id=user.id)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return {"id": new_message.id, "content": new_message.content}

# Get messages for a user
@app.get("/users/{email}/messages")
def get_user_messages(email: str, db: Session = Depends(get_db)):
    # Find the user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all messages for the user
    messages = db.query(Message).filter(Message.user_id == user.id).all()
    
    # Format the messages for the response
    return [{"id": msg.id, "content": msg.content} for msg in messages]

# Health check endpoint
@app.get("/")
def root_controller():
    return {"status": "healthy"}

# Chat endpoint with user association
@app.get("/chat/{email}")
def chat_controller(email: str, prompt: str = "Inspire me", db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get OpenAI response
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    statement = response.choices[0].message.content.strip()
    
    # Save user prompt
    user_msg = Message(content=f"User: {prompt}", user_id=user.id)
    db.add(user_msg)
    
    # Save AI response
    ai_msg = Message(content=f"AI: {statement}", user_id=user.id)
    db.add(ai_msg)
    db.commit()
    
    return {"statement": statement}


# Add some sample data for testing
def create_sample_data():
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(User).count() > 0:
            return
        
        # Create a test user
        test_user = User(
            username="testuser", 
            email="test@example.com",
            password="TestPassword1"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Add some messages for the test user
        messages = [
            Message(content="This is the first message", user_id=test_user.id),
            Message(content="This is another message", user_id=test_user.id)
        ]
        db.add_all(messages)
        db.commit()
    finally:
        db.close()

# Create sample data on startup
create_sample_data()



# uvicorn example_3_2-Full:app --reload

'''
# Navigate to the directory
cd "TA-extra-examples\example 3 - FastAPI"

# Build the Docker image
docker build -t fastapi-chat .

# Run the container
docker run -p 8000:8000 --env-file .env -v ./data:/app/data fastapi-chat
'''