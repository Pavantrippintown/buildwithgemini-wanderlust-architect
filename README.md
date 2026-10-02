# Pavan Travel Guide

Pavan Travel Guide is an AI-powered travel concierge and planner built with the **Google Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Engine**. It acts as a comprehensive travel assistant, offering personalized destination recommendations, interactive maps, live telemetry, and generative multimedia capabilities.

![Pavan Travel Guide Demo](pavan_travel_guide_demo.gif)

## Architecture & Wired Services

This agent project fully implements and wires together several advanced Google Cloud and third-party APIs:

### 1. Vertex AI Agent Engine & ADK
- Built using the ADK framework.
- Capable of being deployed natively to **Vertex AI Agent Runtime** (Agent Engine) exposing an A2A JSONRPC interface.
- Powered by the `gemini-2.5-flash` model.
- Secured execution environment with `AgentEngineSandboxCodeExecutor` for safely running Python calculations and data analytics.

### 2. Multi-Modal Generation (Images & Video)
- **Destination Artwork**: Dynamically generates visual illustrations using `gemini-3.1-flash-lite-image` in the `global` region.
- **Destination Video**: Capable of generating short video clips using the `gemini-omni-flash-preview` interactions API.
- **Cloud Storage**: Both image and video bytes are securely stored in a public **Google Cloud Storage Bucket** and rendered inline in the chat interface.

### 3. Cross-Session Memory (Memory Bank)
- Incorporates long-term cross-session memory via **Vertex AI Memory Bank**.
- The `PreloadMemoryTool` and `generate_memories_callback` ensure the agent recalls user preferences, previous itineraries, and context across different conversational sessions.

### 4. Database & External APIs
- **Firestore Integration**: Catalogs destinations and retrieves data (`search_destinations`, `get_destination`, `add_destination`) directly from a connected Google Cloud Firestore database.
- **Google Maps API**: Geocodes addresses (`geocode_address`) and finds nearby points of interest (`find_nearby_places`) using Google Maps APIs.
- **Open-Meteo API**: Fetches real-time live weather telemetry for any destination (`get_destination_weather`).
- **Frankfurter API**: Conducts live currency conversions (`convert_currency`).

### 5. Custom Frontend Proxy & Rich UI (A2UI)
- Features a custom built **FastAPI Proxy** that talks to the deployed agent over the A2A protocol.
- The web interface (`frontend/static/index.html`) leverages **Agent to UI (A2UI)** protocols to render rich, structured, interactive display cards instead of plain text.
- Fully styled with a custom **Google Antigravity Aesthetic** (Zero-gravity floating HTML5 canvas particles, glassmorphism, and live model telemetry).
- Natively parses and renders generated `<img src="..">` and `<video>` tags directly in the chat dialogue.

## How to Run Locally

### 1. Backend Agent (Playground)
To test the agent locally using the ADK playground, ensure your `deployment_metadata.json` is present and run the web playground pointing to your live Memory Bank:

```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<YOUR_AGENT_ENGINE_ID>
```

### 2. Frontend Interface
To run the custom FastAPI frontend proxy and UI:

```bash
cd frontend
uv run main.py
# The UI will be available at http://localhost:8080 (or the port defined in main.py)
```

> **Note**: The frontend requires `AGENT_ENGINE_RESOURCE_NAME` to be configured, either as an environment variable or resolvable from the project's `deployment_metadata.json`.
