import crud
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db


router_bid = APIRouter(tags=["bidding"])

@router_bid.post("/api/auctions/{auction_id}/bid", response_model=dict)
async def place_bid(request: Request, auction_id: int, db: Session=Depends(get_db)):
    username = request.cookies.get("username")
    print(f"[BID] username: {username}")
    if not username:
        print("[BID] No username found")
        return JSONResponse(
            status_code=401,
            content={"detail": "You must be logged in to place a bid"}
        )
    try:
        user = crud.get_user_by_name(db, username)
        auction = crud.get_auction_by_id(db, auction_id)

        # Check auction is_active
        if not auction.is_active:
            print("[BID] Auction not active")
            return JSONResponse(
                status_code=400,
                content={"detail": "Auction not active"}
            )

        # Check auction expired
        if datetime.utcnow() >= auction.ends_at:
            print("[BID] Auction is expired")
            return JSONResponse(
                status_code=400,
                content={"detail": "Auction has expired"}
            )
        
        body = await request.json()
        bid_amount_str = body.get("amount")
       
        try:
            bid_amount = float(bid_amount_str)
        except Exception:
            print(f"[BID] Invalid bid amount: {bid_amount_str}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Bid amount must be a valid number"}
            )
        min_bid = auction.current_price + 1.0
        if bid_amount < min_bid:
            print(f"[BID] Bid too low: {bid_amount} < {min_bid}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": f"Bid must be at least ${min_bid:.2f}",
                    "minimum_bid": min_bid,
                    "current_price": auction.current_price
                }
            )
        
        if bid_amount <= 0:
            print(f"[BID] Negative bid: {bid_amount}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Bid amount must be positive"}
            )
        
        bid = crud.create_bid(db, auction_id, user.id, bid_amount)
        if not bid:
            print("[BID] Failed to create bid")
            return JSONResponse(
                status_code=500,
                content={"detail": "Failed to place bid"}
            )
        
        print(f"[BID] Placed: User {username} (ID: {user.id}) bid ${bid_amount:.2f} on auction {auction_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Bid of ${bid_amount:.2f} placed successfully!",
                "bid_id": bid.id,
                "amount": bid.amount,
                "new_minimum": bid_amount + 1.00
            }
        )
            
    except Exception as e:
        print(f"[BID] ✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error while placing bid"}
        )


@router_bid.get("/api/auctions/{auction_id}/bids")
async def get_auction_bids(auction_id: int, db: Session=Depends(get_db)):
    bids = crud.get_auction_bids(db, auction_id)
    bid_list = [
        {
            "id": bid.id,
            "auction_id": bid.auction_id,
            "bid_id": bid.bidder_id,
            "amount": float(bid.amount),
            "bid_time": bid.bid_time.isoformat() if bid.bid_time else None,
        } for bid in bids
    ]
    return JSONResponse(
        status_code=200,
        content=bid_list
    )


