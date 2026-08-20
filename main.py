import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import llm_client

app = FastAPI(title="Northstar One Homes Sales Agent API")

# in-memory store for sessions: {session_id: [{"role": "user"|"model", "text": "..."}]}
sessions = {}

# track site visit status per session: "none", "booked", "failed"
booking_records = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    force_booking_fail: Optional[bool] = False

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    site_visit_status: str

class EndSessionRequest(BaseModel):
    session_id: str

class BookVisitRequest(BaseModel):
    session_id: str
    date_time: str
    contact_number: str
    force_failure: Optional[bool] = False

def simulate_booking_service(force_fail: bool = False) -> bool:
    # 85% success rate unless forced
    if force_fail:
        return False
    return random.random() > 0.15

@app.get("/")
def health_check():
    return {"status": "running", "service": "Northstar One Homes Sales Agent"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    sess_id = req.session_id
    if not sess_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    if sess_id not in sessions:
        sessions[sess_id] = []
        booking_records[sess_id] = "not requested"

    # append user turn
    sessions[sess_id].append({"role": "user", "text": req.message})

    # Use LLM to detect booking intent across English, Hindi, and Hinglish
    is_booking_intent = llm_client.detect_booking_intent(req.message)
    
    if is_booking_intent:
        success = simulate_booking_service(force_fail=req.force_booking_fail)
        if success:
            booking_records[sess_id] = "booked"
        else:
            booking_records[sess_id] = "failed"
            # inject context note so the agent knows the backend booking failed
            sessions[sess_id].append({
                "role": "user",
                "text": "[SYSTEM NOTIFICATION: Site booking API failed due to slot conflict/server error. Inform customer and offer manual callback.]"
            })

    # call gemini
    reply = llm_client.get_agent_response(sessions[sess_id])

    # append agent response
    sessions[sess_id].append({"role": "model", "text": reply})

    return ChatResponse(
        session_id=sess_id,
        reply=reply,
        site_visit_status=booking_records.get(sess_id, "not requested")
    )

@app.post("/book-site-visit")
def book_site_visit(req: BookVisitRequest):
    """
    Direct endpoint to simulate a site visit booking event
    """
    success = simulate_booking_service(req.force_failure)
    if success:
        booking_records[req.session_id] = "booked"
        return {"success": True, "message": "Site visit confirmed for Sector 79 Gurugram"}
    else:
        booking_records[req.session_id] = "failed"
        return {"success": False, "message": "Booking slot unavailable or internal server error"}

@app.post("/end-session")
def end_session(req: EndSessionRequest):
    sess_id = req.session_id
    history = sessions.get(sess_id, [])
    
    if not history:
        return {
            "session_id": sess_id,
            "analytics": {
                "budget_mentioned": None,
                "configuration_interest": "undecided",
                "interest_level": "cold",
                "site_visit_status": "not requested",
                "follow_up_required": False,
                "preferred_language": "English",
                "objections_raised": [],
                "opted_out": False,
                "summary": "Session was empty or never started."
            }
        }

    # extract analytics using Gemini
    analytics_data = llm_client.extract_analytics(history)
    
    # ensure backend booking status overrides if already recorded
    if booking_records.get(sess_id) in ["booked", "failed"]:
        analytics_data["site_visit_status"] = booking_records.get(sess_id)

    return {
        "session_id": sess_id,
        "analytics": analytics_data
    }

@app.get("/history/{session_id}")
def get_history(session_id: str):
    return {"session_id": session_id, "messages": sessions.get(session_id, [])}