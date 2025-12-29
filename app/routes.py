import os
import crud
import uuid
from datetime import datetime
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import AuctionCreate, AuctionUpdate, AuctionResponse


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
UPLOAD_DIR = os.path.join(BASE_DIR, "app", "uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router_auction = APIRouter(tags=["posts"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# ============================================================================
# AUCTION CRUD API ROUTES
# ============================================================================

@router_auction.post("/api/auctions/upload-image")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
     
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
        
    return JSONResponse({
        "success": True,
        "filename": filename,
        "size": len(contents),
        "path": filepath
    })
    
@router_auction.get("/api/auctions/list", response_class=HTMLResponse)
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


@router_auction.get("/api/auctions/create-form", response_class=HTMLResponse)
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


@router_auction.post("/api/auctions/create", response_class=HTMLResponse)
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
        print("[DEBUG CREATE] User not found in DB")
        return HTMLResponse(status_code=404)
    
    try:
        form_data = await request.form()
        print(f"[DEBUG CREATE] Form keys: {list(form_data.keys())}")
        
        title = form_data.get("title", "").strip()
        content = form_data.get("content", "").strip()
        start_price_str = form_data.get("start_price", "").strip()
        ends_at_str = form_data.get("ends_at", "").strip()
        image_filename = form_data.get("image_filename", "").strip()
        image_filenames_json = form_data.get("image_filenames", "").strip()
        
        try:
            start_price = float(start_price_str)
            if start_price < 0:
                raise ValueError("Start price must positive")
            ends_at = datetime.fromisoformat(ends_at_str)
            if ends_at <= datetime.utcnow():
                raise ValueError("End time must be in future")
        except ValueError as e:
            print(e)
        
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
            author=user.username,
            start_price=start_price,
            ends_at=ends_at,
            image_path = image_filename if image_filename else None,
            image_paths=image_filenames_json
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


@router_auction.get("/api/auctions/{auction_id}/edit", response_class=HTMLResponse)
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


@router_auction.put("/api/auctions/{auction_id}", response_class=HTMLResponse)
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
        image_filename = form_data.get("image_filename", "").strip()
        image_filenames_json = form_data.get("image_filenames", "").strip()
        
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
            content=content,
            image_path=image_filename if image_filename else None,
            image_paths=image_filenames_json if image_filenames_json else None
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


@router_auction.delete("/api/auctions/{auction_id}", response_class=HTMLResponse)
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
        
        # Delete image file if exist
        if auction.image_path:
            image_path = os.path.join(UPLOAD_DIR, auction.image_path)
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                print("Could not delete the image file")
        
        # Delete multiple images
        if auction.image_paths:
            import json
            try:
                image_paths = json.loads(auction.image_paths)
                for img_filename in image_paths:
                    image_path = os.path.join(UPLOAD_DIR, img_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            except json.JSONDecodeError:
                pass
    
    except Exception as e:
        print(f"[DEBUG DELETE] Error: {str(e)}")
        return HTMLResponse(f"<p class='text-red-600'>Error: {str(e)}</p>", status_code=500)


@router_auction.get("/api/auctions/{auction_id}", response_class=HTMLResponse)
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