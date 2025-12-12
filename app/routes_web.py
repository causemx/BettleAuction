import crud
import os
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from auth import create_access_token
from schemas import RegisterRequest, LoginRequest
from database import get_db

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

@router_web.post("/api/register")
async def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new user via JSON POST"""
    try:
        username = data.username.strip()
        email = data.email.strip()
        password = data.password
        
        # Validate input
        if not username or len(username) < 3 or len(username) > 100:
            return JSONResponse(
                {"detail": "Username must be 3-100 characters"},
                status_code=400
            )
        
        if not email or "@" not in email:
            return JSONResponse(
                {"detail": "Invalid email address"},
                status_code=400
            )
        
        if not password or len(password) < 6:
            return JSONResponse(
                {"detail": "Password must be at least 6 characters"},
                status_code=400
            )

        try:
            crud.create_user(db, username, email, password)
        except ValueError as e:
            return JSONResponse(
                {"detail": str(e)},
                status_code=400
            )
        
        return JSONResponse(
            {"message": "User registered successfully"},
            status_code=201
        )

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return JSONResponse(
            {"detail": "An error occurred during registration. Please try again."},
            status_code=500
        )


@router_web.post("/api/login")
async def login_user(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login via JSON POST - returns JSON with redirect URL
    
    Uses CRUD operations for user authentication
    """
    try:
        username = data.username.strip()
        password = data.password
        
        # Validate input
        if not username:
            return JSONResponse(
                {"detail": "Username is required"},
                status_code=400
            )

        if not password:
            return JSONResponse(
                {"detail": "Password is required"},
                status_code=400
            )

        # Authenticate user using CRUD operation
        db_user = crud.authenticate_user(db, username, password)
        
        if not db_user:
            return JSONResponse(
                {"detail": "Invalid username or password"},
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
        
        # Create response with redirect URL
        response = JSONResponse(
            {
                "message": "Login successful",
                "redirect": "/dashboard"
            },
            status_code=200
        )
        
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
        return JSONResponse(
            {"detail": "An error occurred during login. Please try again."},
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
        user = crud.get_user_by_name(db, username=username)
        
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
    
    existing = crud.get_user_by_name(db, username=username)
    
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
    
    existing = crud.get_user_by_email(db, email=email)
    
    return JSONResponse({
        "available": existing is None,
        "email": email
    })