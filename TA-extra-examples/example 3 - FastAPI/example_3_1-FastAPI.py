from fastapi import FastAPI
from openai import OpenAI
import os

app = FastAPI()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# You just wrap functions with the @app decorator 
# and make sure the output is a dictionary.

@app.get("/")
def root_controller():
    return {"status": "healthy"}


@app.get("/chat")
def chat_controller(prompt: str = "Inspire me"):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    statement = response.choices[0].message.content.strip()
    return {"statement": statement}

# To run, move to the directory containing this file and run:
# uvicorn example_3_1-FastAPI:app --reload

# Then go to http://127.0.0.1:8000/docs#/