from fastmcp import FastMCP
import httpx
import os
import json
from collections import Counter
from google import genai
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("GitHub Card Tool")

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub stats for a given username."""
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    async with httpx.AsyncClient(headers=headers) as client:
        # Fetch user profile
        user_resp = await client.get(f"https://api.github.com/users/{username}")
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        # Fetch repos
        repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100")
        repos_resp.raise_for_status()
        repos = repos_resp.json()
        
        # Aggregate languages and top repos
        languages = Counter()
        top_repos = []
        
        # Sort repos by stars
        sorted_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)
        
        for repo in sorted_repos:
            lang = repo.get("language")
            if lang:
                languages[lang] += 1
            
            if len(top_repos) < 6:
                top_repos.append({
                    "name": repo["name"],
                    "stars": repo.get("stargazers_count", 0),
                    "language": lang,
                    "description": repo.get("description", "")
                })
        
        return {
            "name": user_data.get("name") or username,
            "bio": user_data.get("bio", ""),
            "location": user_data.get("location", ""),
            "avatar_url": user_data.get("avatar_url", ""),
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "top_repos": top_repos,
            "most_used_languages": dict(languages.most_common(5))
        }

@mcp.tool()
async def analyze_profile(github_data: dict, card_type: str = "standard") -> dict:
    """Analyze GitHub data to determine developer vibe and theme (standard or pokemon)."""
    if card_type == "pokemon":
        prompt = f"""
        Analyze this GitHub profile and return ONLY a JSON object styled as an authentic Pokémon Trading Card:
        - pokemon_name: A clever, evolved Pokémon-style name for the developer (e.g. Torvaldus).
        - energy_type: One of "Fire" (Backend/Systems), "Water" (Frontend/UI), "Electric" (Fullstack/JS), "Steel" (DevOps/Cloud), "Psychic" (AI/Data Science).
        - hp: An integer between 50 and 150 based on their commits/repos/followers (e.g., 120).
        - stage: "Basic", "Stage 1", or "Stage 2" based on developer experience level (new vs veteran).
        - power_name: A short, clever 1-3 word developer power (e.g., "Refactoring Shield").
        - power_desc: 1-sentence description of the power.
        - attack1_cost: list of 1-3 emoji energy symbols matching their energy type (e.g., ["💧", "💧"]).
        - attack1_name: A developer-themed attack name (e.g., "Force Push").
        - attack1_desc: 1-sentence description of the attack.
        - attack1_damage: An integer or string damage value (e.g., 30 or "50+").
        - attack2_cost: list of 1-4 emoji energy symbols matching their energy type.
        - attack2_name: An advanced developer-themed attack name (e.g., "Regex Magic").
        - attack2_desc: 1-sentence description of this advanced attack.
        - attack2_damage: An integer or string damage value (e.g., 90 or "120x").
        - weakness: A developer weakness (e.g., "Deadlines" or "Unchecked PRs").
        - resistance: A developer strength/shield (e.g., "Caffeine" or "Unit Tests").
        - flavor_text: A funny, nostalgic Pokémon-style description at the bottom (e.g. "Known to cause server fires when cold coffee is consumed. LV. 45 #001").

        Data: {json.dumps(github_data)}
        """
    else:
        prompt = f"""
        Analyze this GitHub profile and return ONLY a JSON object:
        - developer_vibe: 1-sentence personality.
        - top_skills: list of top 3 skills.
        - fun_fact: clever inference.
        - card_theme: "hacker", "builder", "researcher", "designer", or "open-source-hero".

        Data: {json.dumps(github_data)}
        """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"ERROR in analyze_profile: {e}")
        # Fallback if AI fails (quota issue)
        if card_type == "pokemon":
            return {
                "pokemon_name": "DevMon",
                "energy_type": "Electric",
                "hp": 100,
                "stage": "Stage 1",
                "power_name": "Coffee Catalyst",
                "power_desc": "Transforms coffee into working code twice as fast.",
                "attack1_cost": ["⚡"],
                "attack1_name": "Hot Patch",
                "attack1_desc": "Apply a rapid fix directly in production.",
                "attack1_damage": "30",
                "attack2_cost": ["⚡", "⚡"],
                "attack2_name": "Git Push Force",
                "attack2_desc": "Overwrites conflicts, ignoring all warnings.",
                "attack2_damage": "80",
                "weakness": "Deadlines",
                "resistance": "Caffeine",
                "flavor_text": "A diligent developer who turns caffeine into digital creations. LV. 50"
            }
        return {
            "developer_vibe": "A dedicated developer exploring the digital frontier.",
            "top_skills": ["Python", "GitHub", "Innovation"],
            "fun_fact": "This developer's code is so clean, it's practically sparkling.",
            "card_theme": "builder"
        }


@mcp.tool()
def generate_card_html(username: str, github_data: dict, analysis: dict, card_type: str = "standard") -> str:
    """Generate a self-contained HTML string for a beautiful dev card (standard or pokemon)."""
    if card_type == "pokemon":
        # Get pokemon properties
        p_name = analysis.get("pokemon_name", "GitMon")
        p_type = analysis.get("energy_type", "Electric")
        p_hp = analysis.get("hp", "100")
        p_stage = analysis.get("stage", "Basic")
        p_power_name = analysis.get("power_name", "Coffee Catalyst")
        p_power_desc = analysis.get("power_desc", "Transforms coffee into code.")
        p_attack1_name = analysis.get("attack1_name", "Hot Patch")
        p_attack1_desc = analysis.get("attack1_desc", "Apply rapid live fix.")
        p_attack1_dmg = analysis.get("attack1_damage", "30")
        p_attack1_cost = "".join([f'<span class="energy-bubble">{c}</span>' for c in analysis.get("attack1_cost", ["⚡"])])
        
        p_attack2_name = analysis.get("attack2_name", "Git Push Force")
        p_attack2_desc = analysis.get("attack2_desc", "Overwrites all server branches.")
        p_attack2_dmg = analysis.get("attack2_damage", "80")
        p_attack2_cost = "".join([f'<span class="energy-bubble">{c}</span>' for c in analysis.get("attack2_cost", ["⚡", "⚡"])])
        
        p_weakness = analysis.get("weakness", "Deadlines")
        p_resistance = analysis.get("resistance", "Caffeine")
        p_flavor = analysis.get("flavor_text", "Transforms cold caffeine into compileable code. LV. 50")
        
        # Energy type color mapping
        type_mapping = {
            "Fire": {"color": "#ef4444", "bg": "linear-gradient(135deg, #fecaca 0%, #ef4444 100%)", "symbol": "🔥"},
            "Water": {"color": "#3b82f6", "bg": "linear-gradient(135deg, #bfdbfe 0%, #3b82f6 100%)", "symbol": "💧"},
            "Electric": {"color": "#eab308", "bg": "linear-gradient(135deg, #fef08a 0%, #eab308 100%)", "symbol": "⚡"},
            "Steel": {"color": "#64748b", "bg": "linear-gradient(135deg, #cbd5e1 0%, #64748b 100%)", "symbol": "⚙️"},
            "Psychic": {"color": "#a855f7", "bg": "linear-gradient(135deg, #e9d5ff 0%, #a855f7 100%)", "symbol": "🧠"}
        }
        t = type_mapping.get(p_type, type_mapping["Electric"])
        
        html = f"""
        <div class="pokemon-card">
            <!-- Stage Header -->
            <div class="card-top-info">
                <span class="stage-badge">{p_stage} Pokémon</span>
                <span class="stage-text">Evolves from GitHub Profile</span>
            </div>
            
            <!-- Main Header (Name, HP, Energy) -->
            <div class="card-header">
                <h2 class="pokemon-title">{p_name}</h2>
                <div class="hp-energy">
                    <span class="hp-label">{p_hp} HP</span>
                    <span class="type-icon">{t['symbol']}</span>
                </div>
            </div>
            
            <!-- Picture Frame (Holo Avatar) -->
            <div class="picture-frame holo-effect">
                <img src="{github_data['avatar_url']}" alt="{username}" class="pokemon-avatar" />
            </div>
            
            <!-- Info Bar -->
            <div class="info-bar">
                <span>GitHub Dev Pokémon. Repos: {github_data['public_repos']}, Followers: {github_data['followers']}</span>
            </div>
            
            <!-- Ability Box -->
            <div class="ability-box">
                <span class="ability-title">Pokémon Power: {p_power_name}</span>
                <p class="ability-desc">{p_power_desc}</p>
            </div>
            
            <!-- Attacks Section -->
            <div class="attacks-section">
                <div class="attack-row">
                    <div class="attack-cost">{p_attack1_cost}</div>
                    <div class="attack-details">
                        <span class="attack-name">{p_attack1_name}</span>
                        <p class="attack-desc">{p_attack1_desc}</p>
                    </div>
                    <div class="attack-damage">{p_attack1_dmg}</div>
                </div>
                
                <div class="attack-row border-top">
                    <div class="attack-cost">{p_attack2_cost}</div>
                    <div class="attack-details">
                        <span class="attack-name">{p_attack2_name}</span>
                        <p class="attack-desc">{p_attack2_desc}</p>
                    </div>
                    <div class="attack-damage">{p_attack2_dmg}</div>
                </div>
            </div>
            
            <!-- Weakness / Resistance -->
            <div class="bottom-stats">
                <div class="stat-col">
                    <span class="stat-label">weakness</span>
                    <span class="stat-val">{p_weakness}</span>
                </div>
                <div class="stat-col">
                    <span class="stat-label">resistance</span>
                    <span class="stat-val">{p_resistance} -30</span>
                </div>
                <div class="stat-col">
                    <span class="stat-label">retreat cost</span>
                    <span class="stat-val">⭐ ⭐</span>
                </div>
            </div>
            
            <!-- Flavor Text Box -->
            <div class="flavor-box">
                <p class="flavor-text">"{p_flavor}"</p>
            </div>
            
            <style>
                body {{
                    background: transparent !important;
                    margin: 0;
                    padding: 10px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .pokemon-card {{
                    background: #fbc821; /* Classic Pokemon Yellow border */
                    border: 12px solid #fbc821;
                    border-radius: 18px;
                    width: 100%;
                    max-width: 400px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                    font-family: 'Inter', -apple-system, sans-serif;
                    box-sizing: border-box;
                    padding: 8px;
                    color: #1f2937;
                    background-image: linear-gradient(135deg, #fbc821 0%, #d97706 100%);
                    position: relative;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                .pokemon-card:hover {{
                    transform: translateY(-5px) rotate(1deg);
                    box-shadow: 0 15px 35px rgba(217, 119, 6, 0.4);
                }}
                .card-top-info {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.65rem;
                    font-weight: 700;
                    color: #4b5563;
                    margin-bottom: 2px;
                    padding: 0 4px;
                }}
                .card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: linear-gradient(180deg, #fef08a 0%, #fde047 100%);
                    border: 3px double #b45309;
                    border-radius: 8px 8px 0 0;
                    padding: 4px 10px;
                    box-shadow: inset 0 1px 3px rgba(255,255,255,0.8);
                }}
                .pokemon-title {{
                    margin: 0;
                    font-size: 1.15rem;
                    font-weight: 800;
                    color: #b45309;
                    text-shadow: 1px 1px 0px rgba(255,255,255,0.8);
                }}
                .hp-energy {{
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }}
                .hp-label {{
                    font-size: 0.95rem;
                    font-weight: 900;
                    color: #dc2626;
                }}
                .type-icon {{
                    font-size: 1.1rem;
                }}
                .picture-frame {{
                    background: #d1d5db;
                    border: 5px solid #d97706;
                    border-image: linear-gradient(to bottom, #d97706, #f59e0b) 1;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2), inset 0 0 10px rgba(0,0,0,0.3);
                    height: 220px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    position: relative;
                    overflow: hidden;
                    margin: 4px 0;
                }}
                .pokemon-avatar {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    z-index: 1;
                }}
                /* Holographic Glimmer Effect */
                .holo-effect::after {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: linear-gradient(125deg, 
                        rgba(255,255,255,0) 0%, 
                        rgba(255,255,255,0.2) 30%, 
                        rgba(239,68,68,0.2) 40%, 
                        rgba(59,130,246,0.2) 50%, 
                        rgba(234,179,8,0.2) 60%, 
                        rgba(255,255,255,0.2) 70%, 
                        rgba(255,255,255,0) 100%);
                    background-size: 250% 250%;
                    animation: holoShimmer 5s ease infinite;
                    pointer-events: none;
                    z-index: 2;
                }}
                @keyframes holoShimmer {{
                    0% {{ background-position: 0% 0%; }}
                    50% {{ background-position: 100% 100%; }}
                    100% {{ background-position: 0% 0%; }}
                }}
                .info-bar {{
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    border: 1px solid #78350f;
                    border-radius: 2px;
                    font-size: 0.62rem;
                    font-weight: 700;
                    text-align: center;
                    padding: 2px 0;
                    color: #fff;
                    margin-bottom: 6px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                }}
                .ability-box {{
                    background: #fef3c7;
                    border: 2px solid #d97706;
                    border-radius: 6px;
                    padding: 6px 10px;
                    margin-bottom: 6px;
                }}
                .ability-title {{
                    font-size: 0.78rem;
                    font-weight: 800;
                    color: #dc2626;
                    display: block;
                    margin-bottom: 2px;
                }}
                .ability-desc {{
                    margin: 0;
                    font-size: 0.72rem;
                    line-height: 1.2;
                    color: #374151;
                }}
                .attacks-section {{
                    background: #fffbeb;
                    border: 2px solid #b45309;
                    border-radius: 8px;
                    padding: 4px;
                    margin-bottom: 6px;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
                }}
                .attack-row {{
                    display: flex;
                    align-items: center;
                    padding: 8px 6px;
                }}
                .border-top {{
                    border-top: 1px solid rgba(180, 83, 9, 0.2);
                }}
                .attack-cost {{
                    display: flex;
                    gap: 3px;
                    width: 60px;
                    flex-shrink: 0;
                }}
                .energy-bubble {{
                    font-size: 0.85rem;
                }}
                .attack-details {{
                    flex-grow: 1;
                    padding: 0 8px;
                }}
                .attack-name {{
                    font-size: 0.85rem;
                    font-weight: 800;
                    color: #1f2937;
                    display: block;
                }}
                .attack-desc {{
                    margin: 2px 0 0 0;
                    font-size: 0.68rem;
                    color: #4b5563;
                    line-height: 1.25;
                }}
                .attack-damage {{
                    width: 35px;
                    text-align: right;
                    font-size: 0.95rem;
                    font-weight: 900;
                    color: #1f2937;
                }}
                .bottom-stats {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.6rem;
                    font-weight: 800;
                    color: #4b5563;
                    border-bottom: 2px solid #b45309;
                    padding: 2px 8px 4px 8px;
                    margin-bottom: 6px;
                }}
                .stat-col {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                .stat-label {{
                    text-transform: uppercase;
                    font-size: 0.52rem;
                    color: #6b7280;
                    margin-bottom: 1px;
                }}
                .stat-val {{
                    font-weight: 800;
                }}
                .flavor-box {{
                    background: #fef08a;
                    border: 2px solid #b45309;
                    border-radius: 4px;
                    padding: 4px 8px;
                    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
                }}
                .flavor-text {{
                    margin: 0;
                    font-size: 0.65rem;
                    font-style: italic;
                    color: #78350f;
                    text-align: center;
                    line-height: 1.3;
                }}
            </style>
        </div>
        """
        return html

    theme = analysis.get("card_theme", "builder")
    
    # Simple theme mapping
    themes = {
        "hacker": {"bg": "#0d1117", "text": "#58a6ff", "accent": "#238636"},
        "builder": {"bg": "#ffffff", "text": "#24292f", "accent": "#0969da"},
        "researcher": {"bg": "#f6f8fa", "text": "#1f2328", "accent": "#8250df"},
        "designer": {"bg": "#fff8f2", "text": "#3b2300", "accent": "#bf4b00"},
        "open-source-hero": {"bg": "#f0fff4", "text": "#1a7f37", "accent": "#2da44e"}
    }
    
    t = themes.get(theme, themes["builder"])
    
    repo_list = "".join([
        f'<li><strong>{r["name"]}</strong> ({r["stars"]}⭐) - {r["language"]}</li>'
        for r in github_data["top_repos"][:3]
    ])
    
    skills = "".join([f'<span class="badge">{s}</span>' for s in analysis["top_skills"]])

    html = f"""
    <div class="card" style="background: {t['bg']}; color: {t['text']}; border: 1px solid {t['accent']}; padding: 20px; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <img src="{github_data['avatar_url']}" style="width: 60px; height: 60px; border-radius: 50%; border: 2px solid {t['accent']}; margin-right: 15px;" />
            <div>
                <h2 style="margin: 0;">{github_data['name']}</h2>
                <p style="margin: 0; font-style: italic; opacity: 0.8;">@{username}</p>
            </div>
        </div>
        <p><strong>Vibe:</strong> {analysis['developer_vibe']}</p>
        <div style="margin: 10px 0;">{skills}</div>
        <p><strong>Fun Fact:</strong> {analysis['fun_fact']}</p>
        <hr style="border: 0; border-top: 1px solid {t['accent']}; opacity: 0.3;" />
        <div style="display: flex; justify-content: space-between;">
            <span>Repos: {github_data['public_repos']}</span>
            <span>Followers: {github_data['followers']}</span>
        </div>
        <h4 style="margin-top: 15px; margin-bottom: 5px;">Top Projects:</h4>
        <ul style="padding-left: 20px; margin: 0;">{repo_list}</ul>
        <style>
            .badge {{ background: {t['accent']}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px; }}
        </style>
    </div>
    """
    return html

@mcp.tool()
def save_card(username: str, html: str) -> str:
    """Save the HTML to static/cards/{username}.html and return relative URL path."""
    dir_path = "static/cards"
    os.makedirs(dir_path, exist_ok=True)
    
    suffix = "_pokemon" if 'class="pokemon-card"' in html else ""
    file_path = f"{dir_path}/{username}{suffix}.html"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}{suffix}.html"

if __name__ == "__main__":
    mcp.run(transport="stdio")
