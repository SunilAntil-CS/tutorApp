from fastapi import FastAPI

app = FastAPI(title="Tutor App")


@app.get("/")
def hello_world():
    return {"message": "Hello World"}


@app.get("/health")
def health():
    return {"status": "healthy"}
