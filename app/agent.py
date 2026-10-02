# ruff: noqa
import datetime
import json
import os
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

load_dotenv()

FIRESTORE_PROJECT = "qwiklabs-gcp-02-a7e255b6ed17"
COLLECTION_NAME = "destinations"
BUCKET_NAME = "wanderlust-architect-media-qwiklabs-gcp-02-a7e255b6ed17"
MEMORY_BANK_ID = "1321163826086805504"


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session events to Vertex AI Memory Bank for memory extraction after each turn."""
    await callback_context.add_session_to_memory()
    return None

# Initialize clients using hardcoded project ID
db = firestore.Client(project=FIRESTORE_PROJECT)
storage_client = storage.Client(project=FIRESTORE_PROJECT)
genai_global_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")

# Configure AgentEngineSandboxCodeExecutor using deployment_metadata.json if available
metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "deployment_metadata.json")
agent_engine_resource_name = None
sandbox_resource_name = None

if os.path.exists(metadata_path):
    try:
        with open(metadata_path, "r") as f:
            meta = json.load(f)
            agent_engine_resource_name = meta.get("remote_agent_runtime_id")
            sandbox_resource_name = meta.get("sandbox_resource_name")
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=sandbox_resource_name,
    agent_engine_resource_name=agent_engine_resource_name,
)


def search_destinations(query: str = "", vibe: str = "") -> str:
    """Searches or lists travel destinations from the Firestore catalog.

    Args:
        query: Optional search keyword to filter by name, country, or description.
        vibe: Optional vibe to filter by (e.g. 'Historic', 'Scenic', 'Adventure').

    Returns:
        A JSON string containing matching destination records.
    """
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        results = []
        q_lower = query.lower() if query else ""
        v_lower = vibe.lower() if vibe else ""

        for doc in docs:
            data = doc.to_dict()
            name = data.get("name", "")
            country = data.get("country", "")
            desc = data.get("description", "")
            dest_vibe = data.get("vibe", "")

            matches_query = not q_lower or (
                q_lower in name.lower() or q_lower in country.lower() or q_lower in desc.lower()
            )
            matches_vibe = not v_lower or (v_lower in dest_vibe.lower())

            if matches_query and matches_vibe:
                results.append(data)

        if not results:
            return f"No destinations found matching query='{query}' and vibe='{vibe}'."
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching destinations: {str(e)}"


def get_destination(destination_id: str) -> str:
    """Gets details for a specific travel destination from Firestore by ID.

    Args:
        destination_id: The document ID of the destination (e.g., 'kyoto', 'santorini').

    Returns:
        A JSON string with destination details or an error message if not found.
    """
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(destination_id.lower().strip())
        doc = doc_ref.get()
        if not doc.exists:
            return f"Destination with ID '{destination_id}' was not found."
        return json.dumps(doc.to_dict(), indent=2)
    except Exception as e:
        return f"Error retrieving destination: {str(e)}"


def add_destination(
    destination_id: str,
    name: str,
    country: str,
    description: str,
    vibe: str = "Cultural",
    estimated_daily_cost_usd: int = 150,
    highlights: str = "",
    image_prompt: str = "",
) -> str:
    """Adds or updates a travel destination record in the Firestore catalog.

    Args:
        destination_id: Unique string ID for the destination (e.g., 'paris', 'tokyo').
        name: Full name of the destination (e.g., 'Paris, France').
        country: Country where the destination is located.
        description: A brief summary description of the location.
        vibe: The atmosphere or vibe of the place (e.g., 'Romantic, Historic').
        estimated_daily_cost_usd: Estimated average daily cost in USD per traveler.
        highlights: Comma-separated list of top attractions or activities.
        image_prompt: Visual prompt description for generating artwork of this location.

    Returns:
        A confirmation message upon successfully storing the document.
    """
    try:
        clean_id = destination_id.lower().strip().replace(" ", "-")
        highlights_list = [h.strip() for h in highlights.split(",")] if highlights else []

        data = {
            "id": clean_id,
            "name": name,
            "country": country,
            "description": description,
            "vibe": vibe,
            "estimated_daily_cost_usd": estimated_daily_cost_usd,
            "highlights": highlights_list,
            "image_prompt": image_prompt,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        db.collection(COLLECTION_NAME).document(clean_id).set(data)
        return f"Successfully saved destination '{name}' (ID: {clean_id}) to Firestore."
    except Exception as e:
        return f"Error adding destination: {str(e)}"


def get_destination_weather(location: str) -> str:
    """Fetches real-time weather conditions for a travel destination.

    Args:
        location: City or destination name (e.g. 'Kyoto', 'Paris', 'Santorini').

    Returns:
        A text summary of current weather conditions, temperature, humidity, and wind.
    """
    try:
        clean_location = location.strip()
        url = f"https://wttr.in/{urllib.parse.quote(clean_location)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "WanderlustArchitect/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            curr = data["current_condition"][0]
            temp_c = curr.get("temp_C")
            temp_f = curr.get("temp_F")
            desc = curr.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = curr.get("humidity")
            wind_speed = curr.get("windspeedKmph")
            return (
                f"Current weather in {clean_location}: {desc}, "
                f"{temp_c}°C ({temp_f}°F), Humidity: {humidity}%, Wind: {wind_speed} km/h."
            )
    except Exception as e:
        return f"Unable to fetch weather for '{location}': {str(e)}"


def convert_currency(amount: float = 1.0, from_currency: str = "USD", to_currency: str = "EUR") -> str:
    """Converts monetary amounts between world currencies using real-time exchange rates.

    Args:
        amount: The numerical amount of money to convert.
        from_currency: 3-letter currency code to convert from (e.g., 'USD', 'EUR', 'GBP').
        to_currency: 3-letter currency code to convert to (e.g., 'JPY', 'EUR', 'CAD', 'GBP').

    Returns:
        A text summary of the converted amount and current exchange rate.
    """
    try:
        base = from_currency.strip().upper()
        target = to_currency.strip().upper()
        if base == target:
            return f"{amount:.2f} {base} = {amount:.2f} {target}"

        api_key = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()
        headers = {"User-Agent": "WanderlustArchitect/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"https://api.frankfurter.app/latest?amount={amount}&from={base}&to={target}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            converted = data.get("rates", {}).get(target)
            if converted is None:
                return f"Unsupported target currency code '{target}'."
            rate = converted / amount if amount != 0 else 0
            return (
                f"{amount:.2f} {base} = {converted:.2f} {target} "
                f"(Exchange Rate: 1 {base} = {rate:.4f} {target}, Date: {data.get('date')})"
            )
    except Exception as e:
        return f"Error performing currency conversion from {from_currency} to {to_currency}: {str(e)}"


def geocode_address(address: str) -> str:
    """Turns an address or location name into geographic coordinates (latitude and longitude) using Google Geocoding API.

    Args:
        address: The location, landmark, or address to geocode (e.g., 'Kyoto Station', 'Eiffel Tower').

    Returns:
        A JSON string containing the formatted address, name, and latitude/longitude coordinates.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address.strip())}&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "WanderlustArchitect/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for address '{address}': {data.get('status', 'ZERO_RESULTS')}"

            result = data["results"][0]
            loc = result["geometry"]["location"]
            res_data = {
                "name": address,
                "address": result.get("formatted_address"),
                "location": {
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                },
            }
            return json.dumps(res_data, indent=2)
    except Exception as e:
        return f"Error geocoding address '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: int = 2000,
) -> str:
    """Finds nearby points of interest of a given type near specified coordinates using Google Places API (New).

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'museum', 'lodging', 'park').
        radius_meters: Search radius in meters (default is 2000 meters).

    Returns:
        A JSON string listing nearby places with their name, address, and coordinates.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = "https://places.googleapis.com/v1/places:searchNearby"
        payload = json.dumps({
            "includedTypes": [place_type.strip().lower()],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": float(radius_meters),
                }
            },
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
            "User-Agent": "WanderlustArchitect/1.0",
        }

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            places = data.get("places", [])
            if not places:
                return f"No nearby places of type '{place_type}' found within {radius_meters}m."

            clean_places = []
            for p in places:
                clean_places.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": p.get("location", {}),
                })
            return json.dumps(clean_places, indent=2)
    except Exception as e:
        return f"Error finding nearby places: {str(e)}"


async def generate_destination_artwork(prompt: str, tool_context: ToolContext) -> str:
    """Generates visual artwork or illustrations for a travel destination using gemini-3.1-flash-lite-image in the global region.

    Args:
        prompt: Detailed visual prompt or description for the image to generate (e.g., 'A vibrant digital art illustration of Kyoto Bamboo Grove at sunset').

    Returns:
        A text response containing the public Cloud Storage HTTPS URL of the generated image.
    """
    try:
        res = genai_global_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        if not res.candidates or not res.candidates[0].content.parts:
            return "Failed to generate image: No image content returned from model."

        part = res.candidates[0].content.parts[0]
        if not part.inline_data:
            return "Failed to generate image: No inline image data received."

        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"destination-{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save with tool_context.save_artifact so it shows up in Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload same image bytes to public Cloud Storage bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"artwork/{filename}")
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/artwork/{filename}"
        return f"Successfully generated destination artwork!\nPublic Image URL: {public_url}"
    except Exception as e:
        return f"Error generating destination artwork: {str(e)}"


async def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video for a travel destination using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: Detailed visual prompt or description for the video to generate (e.g., 'A scenic aerial video of waves crashing on a tropical beach in Hawaii at sunset').

    Returns:
        A text response containing the public Cloud Storage HTTPS URL of the generated video.
    """
    try:
        try:
            res = genai_global_client.interactions.create(
                model="gemini-omni-flash-preview",
                input=prompt,
                response_modalities=["video"],
            )
        except Exception:
            res = genai_global_client.models.generate_content(
                model="gemini-omni-flash-preview",
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["VIDEO"]),
            )

        video_bytes = None
        mime_type = "video/mp4"

        if hasattr(res, 'outputs') and res.outputs:
            for out in res.outputs:
                if hasattr(out, 'inline_data') and out.inline_data:
                    video_bytes = out.inline_data.data
                    mime_type = getattr(out.inline_data, 'mime_type', None) or mime_type
                    break
                elif hasattr(out, 'bytes') and out.bytes:
                    video_bytes = out.bytes
                    break

        if not video_bytes and hasattr(res, 'candidates') and res.candidates:
            part = res.candidates[0].content.parts[0]
            if part.inline_data:
                video_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or mime_type

        if not video_bytes:
            return "Failed to generate video: No video data returned from model."

        ext = "mp4"
        filename = f"video-{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save with tool_context.save_artifact so it shows up in Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload same video bytes to public Cloud Storage bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"videos/{filename}")
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/videos/{filename}"
        return f"Successfully generated destination video!\nPublic Video URL: {public_url}"
    except Exception as e:
        return f"Error generating destination video: {str(e)}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=(
        "You are Pavan Travel Guide, an expert AI travel planner and concierge. "
        "Help travelers discover destinations, geocode landmarks, find nearby attractions, generate destination artwork, generate destination videos, check live weather, convert currencies, execute Python code for calculations or data analysis, and manage travel plans. "
        "Use your tools to geocode addresses, find nearby points of interest, generate artwork illustrations, generate destination videos, search catalog destinations, view details, add locations, fetch live weather, convert currencies, and run python code. "
        "Remember the user's stated preferences and travel facts across sessions to offer personalized recommendations."
    ),
    tools=[
        PreloadMemoryTool(),
        search_destinations,
        get_destination,
        add_destination,
        get_destination_weather,
        convert_currency,
        geocode_address,
        find_nearby_places,
        generate_destination_artwork,
        generate_destination_video,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
