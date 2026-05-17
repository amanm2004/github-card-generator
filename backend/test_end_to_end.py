import asyncio
import json
import os
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
from dotenv import load_dotenv

async def test_end_to_end():
    username = "torvalds"
    load_dotenv()
    
    print(f"--- Step 1: Scraping GitHub for '{username}' ---")
    try:
        github_data = await scrape_github(username)
        print("Success! Data retrieved.")
        # print(json.dumps(github_data, indent=2))
    except Exception as e:
        print(f"FAILED at scrape_github: {e}")
        return

    print(f"\n--- Step 2: Analyzing profile with Gemini ---")
    try:
        analysis = await analyze_profile(github_data)
        print("Success! Analysis complete.")
    except Exception as e:
        print(f"FAILED at analyze_profile: {e}")
        print("Note: This tool requires a valid GEMINI_API_KEY in the .env file.")
        return

    print(f"\n--- Step 3: Generating HTML card ---")
    try:
        html = generate_card_html(username, github_data, analysis)
        print("Success! HTML generated.")
    except Exception as e:
        print(f"FAILED at generate_card_html: {e}")
        return

    print(f"\n--- Step 4: Results ---")
    print(f"Card Theme: {analysis.get('card_theme')}")
    print(f"Developer Vibe: {analysis.get('developer_vibe')}")
    
    # Optional: save it
    # save_card(username, html)

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
