import sys
import os
import asyncio
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

load_dotenv()

# Define the path to the MCP server script
SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")

# Configure the Stdio transport for the MCP server
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[SERVER_SCRIPT],
            env=os.environ.copy()
        )
    )
)

# Initialize the ADK Agent
github_card_agent = LlmAgent(
    name="github_card_agent",
    instruction=(
        "You are a GitHub profile analyst and dev card generator. "
        "When a user gives you a GitHub username and a card theme (either 'standard' or 'pokemon'), "
        "you ALWAYS follow this exact sequence: "
        "first call scrape_github, "
        "then analyze_profile with the result and the specified card_type (pass standard or pokemon), "
        "then generate_card_html with all inputs including the card_type, "
        "then save_card. "
        "Never skip steps. Be enthusiastic about developers' work. "
        "If the profile is private or doesn't exist, say so clearly."
    ),
    model="gemini-2.5-flash",
    tools=[mcp_toolset]
)

from google.genai import types

async def test_agent(username: str):
    session_service = InMemorySessionService()
    app_name = "github_card_app"
    user_id = "test_user"
    session_id = "test_session"
    
    # Explicitly create the session
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    
    runner = Runner(
        app_name=app_name,
        agent=github_card_agent, 
        session_service=session_service
    )
    print(f"Testing agent with username: {username}")
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=f"Generate a card for {username}")]
    )
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message
    ):
        print(f"Event: {event}")

if __name__ == "__main__":
    asyncio.run(test_agent("torvalds"))
