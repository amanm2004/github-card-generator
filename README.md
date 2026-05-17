# GitHub Developer Card Generator

A full-stack application that analyzes public GitHub profiles and generates structured developer personas and animated, collectible retro trading cards.

Powered by Google Gemini AI, this application retrieves developer statistics including repositories, languages, commits, and followers, then designs a custom visual representation. Users can choose between a clean, modern **Standard Developer Card** or a vintage, gold-bordered **Pokémon-style Trading Card** featuring dynamic elemental typings, custom HP, and AI-generated attacks/abilities with pure-CSS holographic shimmer overlays.

---

## Key Features

- **Gemini AI Analysis**  
  Evaluates GitHub metadata to extract developer personality profiles, top technical skills, and unique behavioral fun facts.

- **Retro Trading Card Mode**  
  Dynamically designs vintage-style trading cards by mapping developer specialties to elemental energy classes such as Fire, Water, Electric, Steel, and Psychic.

- **Holographic Foil Shader**  
  Implements a shimmering, moving holographic gradient overlay on the avatar frame using pure CSS animations.

- **Dual-Orchestrated Fallbacks**  
  Built-in automatic direct tool fallbacks help keep card generation operational even during API quota limitations.

- **Cloud Run Native Integration**  
  Ready to deploy globally using stateless container overlays on Google Cloud Run with separated session isolation.

- **Intelligent Cache Layering**  
  Smart cache routing saves separate Standard and Pokémon-style variations, such as `{username}.html` and `{username}_pokemon.html`, to prevent rendering collisions.

---

## Technical Stack

### Backend
- FastAPI
- Python
- Google Gemini 2.5 Flash API
- Uvicorn
- Model Context Protocol MCP toolset

### Frontend
- HTML5
- CSS3
- JavaScript
- Responsive glassmorphic UI

### Deployment
- Docker
- Google Cloud Run
- Google Artifact Registry

---

## Quick Start

### 1. Configure Secrets

Create a `.env` file inside the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_personal_access_token
Contributions, issues, and feature requests are welcome. Feel free to open a pull request or submit feedback.
