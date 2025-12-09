from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import init_db
from routes import router
# from routes_image import router_img
from routes_web import router_web
from routes_auth import router_auth

init_db()

app = FastAPI(
    title="foo",
    description="foo",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)
app.include_router(router_auth)
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