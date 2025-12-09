from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
import os

from database import get_db
from models import UserModel, Role
from schemas import UserCreate, UserLogin, UserResponse, Token
from auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    verify_token,
)

# Setup templates from app/templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router_web = APIRouter(tags=["web"])

# ============================================================================
# PAGE ROUTES (Return HTML)
# ============================================================================

@router_web.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router_web.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router_web.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("register.html", {"request": request})


@router_web.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page - requires authentication"""
    token = request.cookies.get("access_token")
    username = request.cookies.get("username")
    
    if not token or not username:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username}
    )


# ============================================================================
# API ROUTES (Web Form Submission - Returns HTML)
# ============================================================================

@router_web.post("/api/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Register new user via form - HTML response"""
    try:
        # Validate input
        if not username or len(username) < 3 or len(username) > 100:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Username must be 3-100 characters",
                },
                status_code=400
            )
        
        if not email or "@" not in email:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Invalid email address",
                },
                status_code=400
            )
        
        if not password or len(password) < 6:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Password must be at least 6 characters",
                },
                status_code=400
            )

        # Check if user exists
        exist_user = db.query(UserModel).filter(
            (UserModel.username == username) | (UserModel.email == email)
        ).first()
        
        if exist_user:
            error_msg = "Username already taken" if exist_user.username == username else "Email already registered"
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": error_msg,
                },
                status_code=400
            )
        
        # Create user
        db_user = UserModel(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=Role.USER
        )
        db.add(db_user)
        db.commit()
        
        # Redirect to login with success message
        response = RedirectResponse(
            url="/login?success=Account created successfully. Please login.",
            status_code=303
        )
        return response

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "An error occurred during registration. Please try again.",
            },
            status_code=500
        )


@router_web.post("/api/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login via form - returns HTML with token in cookie"""
    try:
        # Authenticate user
        db_user = authenticate_user(username, password, db)
        
        if not db_user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Invalid username or password",
                },
                status_code=401
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={
                "sub": db_user.username,
                "role": db_user.role.value,
                "user_id": db_user.id
            },
            expires_delta=access_token_expires
        )
        
        # Render dashboard
        response_html = templates.get_template("dashboard.html").render(
            request=request,
            username=db_user.username
        )
        
        response = HTMLResponse(content=response_html)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,  # 30 minutes
            samesite="Lax"
        )
        response.set_cookie(
            key="username",
            value=db_user.username,
            max_age=1800,
            samesite="Lax"
        )
        
        return response

    except Exception as e:
        print(f"Login error: {str(e)}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "An error occurred during login. Please try again.",
            },
            status_code=500
        )


@router_web.get("/logout")
async def logout():
    """Logout - clear cookies and redirect"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("username")
    return response


# ============================================================================
# HTMX ENDPOINTS (Dynamic Content)
# ============================================================================

@router_web.get("/api/user-info", response_class=HTMLResponse)
async def user_info(request: Request):
    """Get user info for navbar - HTMX endpoint"""
    username = request.cookies.get("username")
    
    if not username:
        return templates.TemplateResponse(
            "navbar_guest.html",
            {"request": request}
        )
    
    return templates.TemplateResponse(
        "navbar_user.html",
        {"request": request, "username": username}
    )


@router_web.get("/api/profile", response_class=HTMLResponse)
async def profile_info(request: Request, db: Session = Depends(get_db)):
    """Get user profile info - for dashboard updates"""
    username = request.cookies.get("username")
    token_str = request.cookies.get("access_token")
    
    if not username or not token_str:
        return HTMLResponse(status_code=401)
    
    try:
        # Get user from database
        user = db.query(UserModel).filter(UserModel.username == username).first()
        
        if not user:
            return HTMLResponse(status_code=404)
        
        return HTMLResponse(
            f"""
            <div class="space-y-2">
                <p><strong>Username:</strong> {user.username}</p>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Role:</strong> <span class="capitalize font-semibold text-indigo-600">{user.role.value}</span></p>
                <p><strong>Member Since:</strong> {user.create_at.strftime('%Y-%m-%d')}</p>
            </div>
            """
        )
    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
        return HTMLResponse(status_code=500)


# ============================================================================
# VALIDATION ENDPOINTS (For form validation)
# ============================================================================

@router_web.get("/api/check-username/{username}")
async def check_username_available(username: str, db: Session = Depends(get_db)):
    """Check if username is available"""
    if len(username) < 3:
        return JSONResponse(
            {"available": False, "message": "Username too short"},
            status_code=400
        )
    
    existing = db.query(UserModel).filter(UserModel.username == username).first()
    
    return JSONResponse({
        "available": existing is None,
        "username": username
    })


@router_web.get("/api/check-email/{email}")
async def check_email_available(email: str, db: Session = Depends(get_db)):
    """Check if email is available"""
    if "@" not in email:
        return JSONResponse(
            {"available": False, "message": "Invalid email"},
            status_code=400
        )
    
    existing = db.query(UserModel).filter(UserModel.email == email).first()
    
    return JSONResponse({
        "available": existing is None,
        "email": email
    })