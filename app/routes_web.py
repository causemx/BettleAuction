# app/routes_web.py - FULLY FIXED (with request context)
"""
Fixed: All TemplateResponse calls include 'request' in context
"""

import crud
import os
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from auth import create_access_token
from schemas import RegisterRequest, LoginRequest, AuctionCreate, AuctionUpdate
from database import get_db

# Setup templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router_web = APIRouter(tags=["web"])

# ============================================================================
# PAGE ROUTES
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
    
    print(f"[DEBUG] Dashboard access - Token: {bool(token)}, Username: {bool(username)}")
    
    if not token or not username:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username}
    )


@router_web.get("/auctions", response_class=HTMLResponse)
async def auctions_page(request: Request, db: Session = Depends(get_db)):
    """Auctions page - requires authentication"""
    username = request.cookies.get("username")
    token = request.cookies.get("access_token")
    
    if not token or not username:
        return RedirectResponse(url="/login", status_code=302)
    
    user = crud.get_user_by_name(db, username=username)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "auctions.html",
        {"request": request, "username": username, "user_id": user.id}
    )

# ============================================================================
# AUCTION CRUD API ROUTES
# ============================================================================

@router_web.get("/api/auctions/list", response_class=HTMLResponse)
async def get_auctions_list(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get auctions list as HTML (for HTMX)"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    auctions = crud.get_all_auctions(db, skip=skip, limit=limit)
    
    return templates.TemplateResponse(
        "components/auction_list.html",
        {"request": request, "auctions": auctions}
    )


@router_web.get("/api/auctions/create-form", response_class=HTMLResponse)
async def get_create_form(request: Request):
    """Get create form for auction - FIXED: includes request in context"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    print(f"[DEBUG CREATE-FORM] Loading create form for user: {username}")
    
    return templates.TemplateResponse(
        "components/auction_form.html",
        {
            "request": request,
            "mode": "create"
        }
    )


@router_web.post("/api/auctions/create", response_class=HTMLResponse)
async def create_auction(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create new auction (form submission via HTMX)"""
    username = request.cookies.get("username")
    print(f"[DEBUG CREATE] Starting create_auction for user: {username}")
    
    if not username:
        print("[DEBUG CREATE] No username - returning 401")
        return HTMLResponse(status_code=401)
    
    user = crud.get_user_by_name(db, username=username)
    print(f"[DEBUG CREATE] User found: {user is not None}")
    
    if not user:
        print(f"[DEBUG CREATE] User not found in DB")
        return HTMLResponse(status_code=404)
    
    try:
        form_data = await request.form()
        print(f"[DEBUG CREATE] Form keys: {list(form_data.keys())}")
        
        title = form_data.get("title", "").strip()
        content = form_data.get("content", "").strip()
        
        print(f"[DEBUG CREATE] Title: '{title}' ({len(title)} chars)")
        print(f"[DEBUG CREATE] Content length: {len(content)} chars")
        
        if not title or not content:
            print("[DEBUG CREATE] Validation failed")
            return templates.TemplateResponse(
                "components/auction_form.html",
                {
                    "request": request,  # ← ALWAYS include request
                    "error": "Title and content are required",
                    "mode": "create"
                }
            )
        
        auction = AuctionCreate(
            title=title,
            content=content,
            author=user.username
        )
        
        print("[DEBUG CREATE] Creating auction in DB")
        new_auction = crud.create_auction(db, auction)
        print(f"[DEBUG CREATE] ✓ SUCCESS - id={new_auction.id}, title={new_auction.title}")
        
        return templates.TemplateResponse(
            "components/auction_item.html",
            {"request": request, "auction": new_auction}  # ← Include request
        )
    
    except Exception as e:
        print(f"[DEBUG CREATE] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[DEBUG CREATE] Traceback: {traceback.format_exc()}")
        return templates.TemplateResponse(
            "components/auction_form.html",
            {
                "request": request,  # ← Include request
                "error": str(e),
                "mode": "create"
            }
        )


@router_web.get("/api/auctions/{auction_id}/edit", response_class=HTMLResponse)
async def edit_auction_form(
    request: Request,
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Get edit form for auction - FIXED: includes request in context"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    auction = crud.get_auction_by_id(db, auction_id)
    if not auction:
        return HTMLResponse("<p class='text-red-600'>Auction not found</p>", status_code=404)
    
    return templates.TemplateResponse(
        "components/auction_form.html",
        {
            "request": request,
            "auction": auction,
            "mode": "edit",
            "auction_id": auction_id
        }
    )


@router_web.put("/api/auctions/{auction_id}", response_class=HTMLResponse)
async def update_auction(
    request: Request,
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Update auction (form submission via HTMX)"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    try:
        form_data = await request.form()
        
        title = form_data.get("title", "").strip()
        content = form_data.get("content", "").strip()
        
        if not title or not content:
            auction = crud.get_auction_by_id(db, auction_id)
            return templates.TemplateResponse(
                "components/auction_form.html",
                {
                    "request": request,  # ← Include request
                    "auction": auction,
                    "error": "Title and content are required",
                    "mode": "edit",
                    "auction_id": auction_id
                }
            )
        
        auction_update = AuctionUpdate(
            title=title,
            content=content
        )
        
        updated_auction = crud.update_auction(db, auction_id, auction_update)
        
        if not updated_auction:
            return HTMLResponse("<p class='text-red-600'>Auction not found</p>", status_code=404)
        
        return templates.TemplateResponse(
            "components/auction_item.html",
            {"request": request, "auction": updated_auction}  # ← Include request
        )
    
    except Exception as e:
        print(f"[DEBUG UPDATE] Error: {str(e)}")
        auction = crud.get_auction_by_id(db, auction_id)
        return templates.TemplateResponse(
            "components/auction_form.html",
            {
                "request": request,  # ← Include request
                "auction": auction,
                "error": str(e),
                "mode": "edit",
                "auction_id": auction_id
            }
        )


@router_web.delete("/api/auctions/{auction_id}", response_class=HTMLResponse)
async def delete_auction(
    request: Request,
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Delete auction"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    try:
        auction = crud.delete_auction(db, auction_id)
        
        if not auction:
            return HTMLResponse("<p class='text-red-600'>Auction not found</p>", status_code=404)
        
        return HTMLResponse("")
    
    except Exception as e:
        print(f"[DEBUG DELETE] Error: {str(e)}")
        return HTMLResponse(f"<p class='text-red-600'>Error: {str(e)}</p>", status_code=500)


@router_web.get("/api/auctions/{auction_id}", response_class=HTMLResponse)
async def get_auction_detail(
    request: Request,
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Get auction detail view"""
    username = request.cookies.get("username")
    if not username:
        return HTMLResponse(status_code=401)
    
    auction = crud.get_auction_by_id(db, auction_id)
    
    if not auction:
        return HTMLResponse("<p class='text-red-600'>Auction not found</p>", status_code=404)
    
    return templates.TemplateResponse(
        "components/auction_detail.html",
        {"request": request, "auction": auction}  # ← Include request
    )

# ============================================================================
# AUTH API ROUTES
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
        print(f"[REGISTER] Error: {str(e)}")
        return JSONResponse(
            {"detail": "An error occurred during registration. Please try again."},
            status_code=500
        )


@router_web.post("/api/login")
async def login_user(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login via JSON POST"""
    try:
        username = data.username.strip()
        password = data.password
        
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

        db_user = crud.authenticate_user(db, username, password)
        
        if not db_user:
            return JSONResponse(
                {"detail": "Invalid username or password"},
                status_code=401
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={
                "sub": db_user.username,
                "role": db_user.role.value,
                "user_id": db_user.id
            },
            expires_delta=access_token_expires
        )
        
        response = JSONResponse(
            {
                "message": "Login successful",
                "redirect": "/auctions"
            },
            status_code=200
        )
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,
            samesite="Lax"
        )
        response.set_cookie(
            key="username",
            value=db_user.username,
            httponly=True,
            max_age=1800,
            samesite="Lax"
        )
        
        print(f"[LOGIN] Success: {db_user.username}")
        return response

    except Exception as e:
        print(f"[LOGIN] Error: {str(e)}")
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
# HTMX ENDPOINTS
# ============================================================================

@router_web.get("/api/user-info", response_class=HTMLResponse)
async def user_info(request: Request):
    """Get user info for navbar"""
    username = request.cookies.get("username")
    
    if not username:
        return templates.TemplateResponse(
            "components/navbar_guest.html",
            {"request": request}
        )
    
    return templates.TemplateResponse(
        "components/navbar_user.html",
        {"request": request, "username": username}
    )


@router_web.get("/api/profile", response_class=HTMLResponse)
async def profile_info(request: Request, db: Session = Depends(get_db)):
    """Get user profile info"""
    username = request.cookies.get("username")
    token_str = request.cookies.get("access_token")
    
    if not username or not token_str:
        return HTMLResponse(status_code=401)
    
    try:
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
        print(f"[PROFILE] Error: {str(e)}")
        return HTMLResponse(status_code=500)


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