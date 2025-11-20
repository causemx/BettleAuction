from fastapi import FastAPI
from database import init_db
from routes import router

init_db()

app = FastAPI(
    title="foo",
    description="foo",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "foo",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)