from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from agent import github_card_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
import os
import uuid
import uvicorn

app = FastAPI(title="GitHub Dev Card Generator")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for cards
os.makedirs("static/cards", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ADK Services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/card/{username}")
async def get_card(username: str, theme: str = "standard"):
    suffix = "_pokemon" if theme == "pokemon" else ""
    file_path = f"static/cards/{username}{suffix}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Card not found")

@app.post("/generate")
async def generate_card(payload: dict):
    username = payload.get("username")
    theme_choice = payload.get("theme", "standard")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    try:
        app_name = "github_card_app"
        user_id = f"user_{username}"
        session_id = f"session_{username}_{theme_choice}" # Separate session per theme
        
        # Ensure session exists (ADK sessions are persistent in the service)
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        runner = Runner(
            app_name=app_name,
            agent=github_card_agent,
            session_service=session_service,
            memory_service=memory_service
        )
        
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=f"Generate a dev card for {username} with card theme {theme_choice}")]
        )
        
        # --- 1. Attempt Agentic Generation ---
        final_response_text = ""
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                if hasattr(event, 'text') and event.text:
                    final_response_text += event.text
        except Exception as agent_error:
            print(f"Agent failed (Quota or Technical): {agent_error}. Falling back to direct tool orchestration.")

        # --- 2. Verification & Direct Fallback ---
        suffix = "_pokemon" if theme_choice == "pokemon" else ""
        file_path = f"static/cards/{username}{suffix}.html"
        card_url = f"/static/cards/{username}{suffix}.html"
        
        if not os.path.exists(file_path):
            print(f"DEBUG: Agent failed to create card. Running direct tools for {username}...")
            # Direct Tool Orchestration (The "Bulletproof" Path)
            from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
            
            github_data = await scrape_github(username)
            analysis = await analyze_profile(github_data, card_type=theme_choice)
            html = generate_card_html(username, github_data, analysis, card_type=theme_choice)
            save_card(username, html)
            
            final_response_text = "Generated using direct fallback mode (AI Agent was unavailable)."

        return {
            "status": "success",
            "username": username,
            "card_url": card_url,
            "agent_message": final_response_text
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
