from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import init_db
# from routes_image import router_img
from routes_web import router_web
from routes import router_auction

init_db()

app = FastAPI(
    title="foo",
    description="foo",
    version="1.0.0"
)

# ============================================================================
# CORS MIDDLEWARE - FIX FOR NETWORK ERRORS
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # If you have a separate frontend
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router_auction)
app.include_router(router_web)


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