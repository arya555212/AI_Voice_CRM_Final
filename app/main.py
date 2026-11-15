import os
import secrets
from datetime import datetime
from typing import Optional

import httpx

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from passlib.context import CryptContext

from sqlalchemy import (
    create_engine,
    String,
    Integer,
    DateTime,
    Text,
    select,
    or_,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE = os.path.dirname(os.path.abspath(__file__))

DB_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./crm.db"
)

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False}
    if DB_URL.startswith("sqlite")
    else {}
)

SessionLocal = sessionmaker(
    bind=engine
)

# PBKDF2 password hashing
pwd = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


# ============================================================
# DATABASE BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# USER MODEL
# ============================================================

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(80),
        unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )


# ============================================================
# CONTACT MODEL
# ============================================================

class Contact(Base):

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(120)
    )

    email: Mapped[str] = mapped_column(
        String(160),
        default=""
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        default=""
    )

    company: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# LEAD MODEL
# ============================================================

class Lead(Base):

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(120)
    )

    company: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    email: Mapped[str] = mapped_column(
        String(160),
        default=""
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="New"
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CALL HISTORY MODEL
# ============================================================

class CallHistory(Base):

    __tablename__ = "call_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    contact_name: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        default=""
    )

    call_type: Mapped[str] = mapped_column(
        String(30),
        default="AI Call"
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    result: Mapped[str] = mapped_column(
        String(40),
        default="Pending"
    )

    lead_status: Mapped[str] = mapped_column(
        String(40),
        default="Not a Lead"
    )

    ai_summary: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    keywords: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    recall_required: Mapped[str] = mapped_column(
        String(10),
        default="No"
    )

    follow_up_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CHAT HISTORY MODEL
# ============================================================

class ChatHistory(Base):

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    contact_name: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    contact_phone: Mapped[str] = mapped_column(
        String(50),
        default=""
    )

    message: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    ai_reply: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    ai_summary: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    keywords: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    lead_status: Mapped[str] = mapped_column(
        String(40),
        default="Unknown"
    )

    follow_up_required: Mapped[str] = mapped_column(
        String(10),
        default="No"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# VOICE ARCHITECTURE MODEL
# ============================================================

class VoiceArchitecture(Base):

    __tablename__ = "voice_architecture"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # Healthcare, Retail, Banking, etc.
    industry: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    # Sales Agent, Customer Support, Receptionist, etc.
    voice_type: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    # Female, Male, Neutral
    voice_gender: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    # Human-like, Robotic, Natural, Professional
    voice_style: Mapped[str] = mapped_column(
        String(50),
        default=""
    )

    # Inbound, Outbound, Both
    usage_area: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    # ElevenLabs, Telnyx, etc.
    voice_provider: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(engine)


# ============================================================
# CREATE DEFAULT ADMIN
# ============================================================

with SessionLocal() as db:

    admin = db.scalar(
        select(User).where(
            User.username == "admin"
        )
    )

    if not admin:

        db.add(
            User(
                username="admin",
                password_hash=pwd.hash("admin123")
            )
        )

        db.commit()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Voice CRM"
)


# ============================================================
# STATIC FILES
# ============================================================

static_directory = os.path.join(
    BASE,
    "static"
)

os.makedirs(
    static_directory,
    exist_ok=True
)

app.mount(
    "/static",
    StaticFiles(directory=static_directory),
    name="static"
)


# ============================================================
# TEMPLATES
# ============================================================

templates = Jinja2Templates(
    directory=os.path.join(
        BASE,
        "templates"
    )
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def logged_in(request: Request):

    return bool(
        request.cookies.get(
            "crm_session"
        )
    )


def guard(request: Request):

    if not logged_in(request):

        return RedirectResponse(
            "/login",
            status_code=303
        )

    return None


def ctx(request: Request, **kw):

    return {
        "request": request,
        **kw
    }


# ============================================================
# LOGIN PAGE
# ============================================================

@app.get(
    "/login",
    response_class=HTMLResponse
)
def login_page(request: Request):

    if logged_in(request):

        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=ctx(request)
    )


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.username == username
            )
        )

    if not user:

        return RedirectResponse(
            "/login?error=1",
            status_code=303
        )

    if not pwd.verify(
        password,
        user.password_hash
    ):

        return RedirectResponse(
            "/login?error=1",
            status_code=303
        )

    response = RedirectResponse(
        "/",
        status_code=303
    )

    response.set_cookie(
        key="crm_session",
        value=secrets.token_urlsafe(24),
        httponly=True,
        samesite="lax"
    )

    return response


# ============================================================
# LOGOUT
# ============================================================

@app.get("/logout")
def logout():

    response = RedirectResponse(
        "/login",
        status_code=303
    )

    response.delete_cookie(
        "crm_session"
    )

    return response


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def dashboard(request: Request):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        contacts = db.query(
            Contact
        ).count()

        leads = db.query(
            Lead
        ).count()

        new = db.query(
            Lead
        ).filter_by(
            status="New"
        ).count()

        total_calls = db.query(
            CallHistory
        ).count()

        successful_calls = db.query(
            CallHistory
        ).filter_by(
            result="Successful"
        ).count()

        unsuccessful_calls = db.query(
            CallHistory
        ).filter_by(
            result="Unsuccessful"
        ).count()

        follow_ups = db.query(
            CallHistory
        ).filter_by(
            recall_required="Yes"
        ).count()

        voice_configurations = db.query(
            VoiceArchitecture
        ).count()

        latest_voice = db.scalars(
            select(VoiceArchitecture).order_by(
                VoiceArchitecture.id.desc()
            )
        ).first()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=ctx(
            request,
            contacts=contacts,
            leads=leads,
            new=new,
            total_calls=total_calls,
            successful_calls=successful_calls,
            unsuccessful_calls=unsuccessful_calls,
            follow_ups=follow_ups,
            voice_configurations=voice_configurations,
            latest_voice=latest_voice
        )
    )


# ============================================================
# CONTACTS PAGE
# ============================================================

@app.get(
    "/contacts",
    response_class=HTMLResponse
)
def contacts(
    request: Request,
    q: str = ""
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        stmt = select(Contact)

        if q:

            stmt = stmt.where(
                or_(
                    Contact.name.ilike(f"%{q}%"),
                    Contact.email.ilike(f"%{q}%"),
                    Contact.phone.ilike(f"%{q}%"),
                    Contact.company.ilike(f"%{q}%")
                )
            )

        rows = db.scalars(
            stmt.order_by(
                Contact.id.desc()
            )
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="contacts.html",
        context=ctx(
            request,
            contacts=rows,
            q=q
        )
    )


# ============================================================
# ADD CONTACT
# ============================================================

@app.post("/contacts")
def add_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form("")
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        db.add(
            Contact(
                name=name,
                email=email,
                phone=phone,
                company=company
            )
        )

        db.commit()

    return RedirectResponse(
        "/contacts",
        status_code=303
    )


# ============================================================
# EDIT CONTACT
# ============================================================

@app.post("/contacts/{id}/edit")
def edit_contact(
    request: Request,
    id: int,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form("")
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        contact = db.get(
            Contact,
            id
        )

        if not contact:

            raise HTTPException(
                status_code=404,
                detail="Contact not found"
            )

        contact.name = name
        contact.email = email
        contact.phone = phone
        contact.company = company

        db.commit()

    return RedirectResponse(
        "/contacts",
        status_code=303
    )


# ============================================================
# DELETE CONTACT
# ============================================================

@app.post("/contacts/{id}/delete")
def delete_contact(
    request: Request,
    id: int
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        contact = db.get(
            Contact,
            id
        )

        if contact:

            db.delete(contact)
            db.commit()

    return RedirectResponse(
        "/contacts",
        status_code=303
    )


# ============================================================
# LEADS PAGE
# ============================================================

@app.get(
    "/leads",
    response_class=HTMLResponse
)
def leads(request: Request):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        rows = db.scalars(
            select(Lead).order_by(
                Lead.id.desc()
            )
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="leads.html",
        context=ctx(
            request,
            leads=rows
        )
    )


# ============================================================
# ADD LEAD
# ============================================================

@app.post("/leads")
def add_lead(
    request: Request,
    name: str = Form(...),
    company: str = Form(""),
    email: str = Form(""),
    status: str = Form("New"),
    notes: str = Form("")
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        db.add(
            Lead(
                name=name,
                company=company,
                email=email,
                status=status,
                notes=notes
            )
        )

        db.commit()

    return RedirectResponse(
        "/leads",
        status_code=303
    )


# ============================================================
# UPDATE LEAD STATUS
# ============================================================

@app.post("/leads/{id}/status")
def lead_status(
    request: Request,
    id: int,
    status: str = Form(...)
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        lead = db.get(
            Lead,
            id
        )

        if lead:

            lead.status = status
            db.commit()

    return RedirectResponse(
        "/leads",
        status_code=303
    )


# ============================================================
# DELETE LEAD
# ============================================================

@app.post("/leads/{id}/delete")
def delete_lead(
    request: Request,
    id: int
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        lead = db.get(
            Lead,
            id
        )

        if lead:

            db.delete(lead)
            db.commit()

    return RedirectResponse(
        "/leads",
        status_code=303
    )


# ============================================================
# CALL HISTORY PAGE
# ============================================================

@app.get(
    "/calls",
    response_class=HTMLResponse
)
def calls(
    request: Request,
    q: str = ""
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        stmt = select(CallHistory)

        if q:

            stmt = stmt.where(
                or_(
                    CallHistory.contact_name.ilike(
                        f"%{q}%"
                    ),
                    CallHistory.phone.ilike(
                        f"%{q}%"
                    ),
                    CallHistory.result.ilike(
                        f"%{q}%"
                    ),
                    CallHistory.ai_summary.ilike(
                        f"%{q}%"
                    ),
                    CallHistory.keywords.ilike(
                        f"%{q}%"
                    )
                )
            )

        rows = db.scalars(
            stmt.order_by(
                CallHistory.id.desc()
            )
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="calls.html",
        context=ctx(
            request,
            calls=rows,
            q=q
        )
    )


# ============================================================
# ADD CALL RECORD
# ============================================================

@app.post("/calls")
def add_call(
    request: Request,
    contact_name: str = Form(""),
    phone: str = Form(""),
    call_type: str = Form("AI Call"),
    duration_seconds: int = Form(0),
    result: str = Form("Pending"),
    lead_status: str = Form("Not a Lead"),
    ai_summary: str = Form(""),
    keywords: str = Form(""),
    recall_required: str = Form("No"),
    follow_up_date: str = Form("")
):

    g = guard(request)

    if g:
        return g

    follow_date = None

    if follow_up_date:

        try:

            follow_date = datetime.strptime(
                follow_up_date,
                "%Y-%m-%d"
            )

        except ValueError:

            follow_date = None

    with SessionLocal() as db:

        db.add(
            CallHistory(
                contact_name=contact_name,
                phone=phone,
                call_type=call_type,
                duration_seconds=duration_seconds,
                result=result,
                lead_status=lead_status,
                ai_summary=ai_summary,
                keywords=keywords,
                recall_required=recall_required,
                follow_up_date=follow_date
            )
        )

        db.commit()

    return RedirectResponse(
        "/calls",
        status_code=303
    )


# ============================================================
# DELETE CALL RECORD
# ============================================================

@app.post("/calls/{id}/delete")
def delete_call(
    request: Request,
    id: int
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        call = db.get(
            CallHistory,
            id
        )

        if call:

            db.delete(call)
            db.commit()

    return RedirectResponse(
        "/calls",
        status_code=303
    )


# ============================================================
# VOICE ARCHITECTURE PAGE
# ============================================================

@app.get(
    "/voice-architecture",
    response_class=HTMLResponse
)
def voice_architecture_page(request: Request):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        voices = db.scalars(
            select(VoiceArchitecture).order_by(
                VoiceArchitecture.id.desc()
            )
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="voice_architecture.html",
        context=ctx(
            request,
            voices=voices
        )
    )


# ============================================================
# ADD VOICE ARCHITECTURE
# ============================================================

@app.post("/voice-architecture")
def add_voice_architecture(

    request: Request,

    industry: str = Form(...),

    voice_type: str = Form(...),

    voice_gender: str = Form(...),

    voice_style: str = Form(...),

    usage_area: str = Form(...),

    voice_provider: str = Form("")

):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        db.add(
            VoiceArchitecture(
                industry=industry,
                voice_type=voice_type,
                voice_gender=voice_gender,
                voice_style=voice_style,
                usage_area=usage_area,
                voice_provider=voice_provider
            )
        )

        db.commit()

    return RedirectResponse(
        "/voice-architecture",
        status_code=303
    )


# ============================================================
# DELETE VOICE ARCHITECTURE
# ============================================================

@app.post("/voice-architecture/{id}/delete")
def delete_voice_architecture(
    request: Request,
    id: int
):

    g = guard(request)

    if g:
        return g

    with SessionLocal() as db:

        voice = db.get(
            VoiceArchitecture,
            id
        )

        if voice:

            db.delete(voice)
            db.commit()

    return RedirectResponse(
        "/voice-architecture",
        status_code=303
    )


# ============================================================
# INBOUND CALLING
# ============================================================

@app.get(
    "/inbound",
    response_class=HTMLResponse
)
def inbound(request: Request):

    g = guard(request)

    if g:
        return g

    return templates.TemplateResponse(
        request=request,
        name="placeholder.html",
        context=ctx(
            request,
            title="Inbound Calling",
            description=(
                "Inbound calling is currently a "
                "display-only placeholder. "
                "A voice provider can be connected later."
            )
        )
    )


# ============================================================
# OUTBOUND CALLING
# ============================================================

@app.get(
    "/outbound",
    response_class=HTMLResponse
)
def outbound(request: Request):

    g = guard(request)

    if g:
        return g

    return templates.TemplateResponse(
        request=request,
        name="placeholder.html",
        context=ctx(
            request,
            title="Outbound Calling",
            description=(
                "Outbound calling is currently a "
                "display-only placeholder. "
                "A voice provider can be connected later."
            )
        )
    )


# ============================================================
# AI ASSISTANT PAGE
# ============================================================

@app.get(
    "/assistant",
    response_class=HTMLResponse
)
def assistant_page(request: Request):

    g = guard(request)

    if g:
        return g

    return templates.TemplateResponse(
        request=request,
        name="assistant.html",
        context=ctx(request)
    )


# ============================================================
# AI ASSISTANT API
# ============================================================

@app.post("/api/assistant")
async def assistant(request: Request):

    if not logged_in(request):

        raise HTTPException(
            status_code=401,
            detail="Not logged in"
        )

    data = await request.json()

    prompt = (
        data.get("prompt") or ""
    ).strip()

    contact_name = (
        data.get("contact_name") or ""
    ).strip()

    contact_phone = (
        data.get("contact_phone") or ""
    ).strip()

    if not prompt:

        return JSONResponse(
            {
                "reply":
                "Please enter a question."
            }
        )

    url = (
        os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434"
        ).rstrip("/")
        + "/api/generate"
    )

    model = os.getenv(
        "OLLAMA_MODEL",
        "gemma4:2b"
    )

    try:

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                url,
                json={
                    "model": model,
                    "prompt": (
                        "You are a concise AI assistant "
                        "for an AI Voice CRM. "
                        + prompt
                    ),
                    "stream": False
                }
            )

            response.raise_for_status()

            reply = response.json().get(
                "response",
                "No response."
            )

        with SessionLocal() as db:

            db.add(
                ChatHistory(
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    message=prompt,
                    ai_reply=reply
                )
            )

            db.commit()

        return JSONResponse(
            {
                "reply": reply
            }
        )

    except Exception as error:

        print(
            "Ollama error:",
            error
        )

        return JSONResponse(
            {
                "reply": (
                    "Ollama is unavailable. "
                    "Start Ollama and make sure the "
                    f"model '{model}' is installed."
                )
            }
        )


# ============================================================
# CHAT HISTORY API
# ============================================================

@app.get("/api/chat-history")
def chat_history(
    request: Request,
    q: str = ""
):

    if not logged_in(request):

        raise HTTPException(
            status_code=401,
            detail="Not logged in"
        )

    with SessionLocal() as db:

        stmt = select(ChatHistory)

        if q:

            stmt = stmt.where(
                or_(
                    ChatHistory.contact_name.ilike(
                        f"%{q}%"
                    ),
                    ChatHistory.contact_phone.ilike(
                        f"%{q}%"
                    ),
                    ChatHistory.message.ilike(
                        f"%{q}%"
                    ),
                    ChatHistory.ai_reply.ilike(
                        f"%{q}%"
                    ),
                    ChatHistory.keywords.ilike(
                        f"%{q}%"
                    )
                )
            )

        rows = db.scalars(
            stmt.order_by(
                ChatHistory.id.desc()
            )
        ).all()

        result = []

        for chat in rows:

            result.append(
                {
                    "id": chat.id,
                    "contact_name":
                        chat.contact_name,
                    "contact_phone":
                        chat.contact_phone,
                    "message":
                        chat.message,
                    "ai_reply":
                        chat.ai_reply,
                    "ai_summary":
                        chat.ai_summary,
                    "keywords":
                        chat.keywords,
                    "lead_status":
                        chat.lead_status,
                    "follow_up_required":
                        chat.follow_up_required,
                    "created_at":
                        chat.created_at.isoformat()
                }
            )

    return JSONResponse(
        {
            "chats": result
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return JSONResponse(
        {
            "status": "ok",
            "service": "AI Voice CRM"
        }
    )