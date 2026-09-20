# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback





# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-7b95af39ea22"
GCS_BUCKET_NAME = "smart-pantry-media-qwiklabs-gcp-02-7b95af39ea22"



def get_pantry_items(item_name: str = "") -> str:
    """Reads inventory items from the Firestore pantry database.

    Args:
        item_name: Optional name of a specific ingredient or item to search for. If empty, lists all pantry items.

    Returns:
        A string listing matching pantry items with quantities, units, categories, and notes.
    """
    from google.cloud import firestore

    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    collection_ref = db.collection("pantry_inventory")

    docs = collection_ref.stream()
    items = [doc.to_dict() for doc in docs]

    if item_name.strip():
        search_lower = item_name.lower().strip()
        items = [
            i for i in items
            if search_lower in i.get("name", "").lower() or search_lower in i.get("item_id", "").lower()
        ]

    if not items:
        return f"No pantry items found matching '{item_name}'." if item_name else "Pantry inventory is currently empty."

    formatted = []
    for i in items:
        line = f"- {i.get('name')}: {i.get('quantity')} {i.get('unit')} (Category: {i.get('category', 'General')})"
        if i.get("notes"):
            line += f" | Notes: {i.get('notes')}"
        formatted.append(line)

    return "Current Pantry Inventory:\n" + "\n".join(formatted)


def add_or_update_pantry_item(
    name: str, quantity: float, unit: str, category: str = "General", notes: str = ""
) -> str:
    """Adds a new ingredient or updates an existing item's quantity in the Firestore pantry database.

    Args:
        name: Name of the ingredient/item (e.g., 'Roma Tomatoes', 'Baby Spinach').
        quantity: Numerical amount/quantity of the item (e.g., 2, 0.5, 12).
        unit: Unit of measurement (e.g., 'count', 'lbs', 'bag', 'cans', 'bottle').
        category: Category of the item (e.g., 'Produce', 'Dairy & Eggs', 'Pantry Staples', 'Spices').
        notes: Optional extra details or notes about the item.

    Returns:
        A string confirming that the pantry item was saved in Firestore.
    """
    from google.cloud import firestore

    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    item_id = name.lower().strip().replace(" ", "_")

    doc_ref = db.collection("pantry_inventory").document(item_id)
    doc_data = {
        "item_id": item_id,
        "name": name.strip(),
        "quantity": float(quantity),
        "unit": unit.strip(),
        "category": category.strip(),
        "notes": notes.strip(),
    }
    doc_ref.set(doc_data, merge=True)
    return f"Successfully updated '{name}' in Firestore pantry database: {quantity} {unit}."


def delete_pantry_item(name: str) -> str:
    """Removes an item from the Firestore pantry database.

    Args:
        name: Name of the ingredient/item to delete from inventory.

    Returns:
        A string confirming deletion of the item from Firestore.
    """
    from google.cloud import firestore

    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    item_id = name.lower().strip().replace(" ", "_")

    doc_ref = db.collection("pantry_inventory").document(item_id)
    doc_ref.delete()
    return f"Successfully deleted '{name}' from Firestore pantry database."


def generate_shopping_list(recipe_name: str, missing_items: str) -> str:
    """Generates a grocery shopping list for a recipe and saves missing ingredients to the Firestore shopping_list collection.

    Args:
        recipe_name: The name of the meal or recipe (e.g., 'Spinach Omelet', 'Chickpea Curry').
        missing_items: Comma-separated list of missing ingredients to buy (e.g., '2 avocados, 1 loaf gluten-free bread').

    Returns:
        A string confirming the shopping list was created and saved in Firestore.
    """
    from google.cloud import firestore

    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    list_id = recipe_name.lower().strip().replace(" ", "_")

    items_array = [item.strip() for item in missing_items.split(",") if item.strip()]

    doc_ref = db.collection("shopping_list").document(list_id)
    doc_data = {
        "recipe_name": recipe_name.strip(),
        "missing_items": items_array,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    doc_ref.set(doc_data)

    formatted_items = "\n".join([f"- {item}" for item in items_array])
    return f"Saved shopping list for '{recipe_name}' to Firestore:\n{formatted_items}"


def fetch_external_recipes(query: str) -> str:
    """Searches TheMealDB public API for real recipe ideas matching a dish name or ingredient.

    Args:
        query: Name of dish or ingredient to search for online (e.g., 'curry', 'chicken', 'omelet').

    Returns:
        A formatted string of matching real-world recipes with category, region, and instructions.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("MEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        meals = data.get("meals")
        if not meals:
            return f"No external recipes found matching '{query}'."

        results = []
        for meal in meals[:3]:
            name = meal.get("strMeal")
            category = meal.get("strCategory", "General")
            area = meal.get("strArea", "International")
            instructions = meal.get("strInstructions", "")[:200].replace("\r\n", " ") + "..."
            results.append(f"🍲 **{name}** ({category} | {area})\n  Instructions: {instructions}")

        return f"Real Online Recipes for '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Failed to fetch external recipes: {str(e)}"


def geocode_address(address: str) -> str:
    """Converts a street address or location name into latitude/longitude coordinates using Google Geocoding API.

    Args:
        address: Street address, city, or location description (e.g., '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A formatted string containing the formatted address and latitude/longitude coordinates.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = data.get("results", [])
        if not results:
            return f"No location coordinates found for address '{address}'."

        first = results[0]
        formatted_address = first.get("formatted_address", address)
        location = first.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        return f"📍 Address: {formatted_address}\n  Location: latitude {lat}, longitude {lng}"
    except Exception as e:
        return f"Geocoding request failed: {str(e)}"


def find_nearby_places(
    latitude: float, longitude: float, place_type: str = "grocery_store", radius: float = 3000.0
) -> str:
    """Finds nearby places of a specific type (e.g., grocery_store, supermarket) using Places API (New).

    Args:
        latitude: Center latitude coordinate (e.g., 37.7749).
        longitude: Center longitude coordinate (e.g., -122.4194).
        place_type: Type of place to find (e.g., 'grocery_store', 'supermarket', 'bakery').
        radius: Search radius in meters (default: 3000.0).

    Returns:
        A formatted string listing nearby places with display name, formatted address, and coordinates.
    """
    import json
    import os
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [place_type.strip().lower()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby '{place_type}' places found within {radius}m."

        formatted_places = []
        for p in places:
            name = p.get("displayName", {}).get("text", "Unknown Place")
            addr = p.get("formattedAddress", "No address")
            loc = p.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            formatted_places.append(f"🏬 **{name}**\n  Address: {addr}\n  Location: latitude {lat}, longitude {lng}")

        return f"Nearby '{place_type}' places:\n\n" + "\n\n".join(formatted_places)
    except Exception as e:
        return f"Places API search failed: {str(e)}"


RAG_CORPUS_NAME = "projects/472679648067/locations/us-central1/ragCorpora/1931437309723410432"


def consult_gutenberg_herbal(query: str) -> str:
    """Search the Project Gutenberg Complete Herbal corpus and return matched passages on medicinal herbs, plants, remedies, and recipes.

    Args:
        query: What to look up (e.g. a plant, herb, remedy, or health condition).

    Returns:
        The matched passages from Nicholas Culpeper's Complete Herbal, or a note if no relevant passage was found.
    """
    import vertexai
    from vertexai.preview import rag

    try:
        vertexai.init(project="qwiklabs-gcp-02-7b95af39ea22", location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval failed: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant passage found in the herbal corpus."


def generate_recipe_image(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates an image for a recipe, dish, or pantry item in the agent's domain using gemini-3.1-flash-lite-image model.

    Args:
        prompt: Description of the dish, recipe, or food item to generate an image for.
        tool_context: Runtime context provided by ADK to save artifacts.

    Returns:
        The public HTTPS URL of the generated image stored in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    try:
        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"A high quality professional food photography shot of {prompt}",
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return "Error: No image content generated by model."

        filename = f"recipe_{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save artifact to ToolContext for Playground Artifacts panel
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception as e:
                print(f"Warning: Failed to save artifact to tool_context: {e}")

        # 2. Upload same bytes to public GCS bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Image generation failed: {str(e)}"


def generate_recipe_video(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates a short video for a dish, recipe, or pantry item in the agent's domain using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: Description of the dish, recipe, or food item to generate a video for.
        tool_context: Runtime context provided by ADK to save artifacts.

    Returns:
        The public HTTPS URL of the generated video stored in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    try:
        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
        
        video_bytes = None
        mime_type = "video/mp4"

        try:
            interaction = genai_client.interactions.create(
                model="gemini-omni-flash-preview",
                input=f"Generate a short video showing {prompt}",
            )
            if hasattr(interaction, "output_video") and interaction.output_video:
                if hasattr(interaction.output_video, "data"):
                    video_bytes = interaction.output_video.data
                elif hasattr(interaction.output_video, "bytes"):
                    video_bytes = interaction.output_video.bytes
            elif hasattr(interaction, "outputs") and interaction.outputs:
                for o in interaction.outputs:
                    if getattr(o, "type", "") == "video" or hasattr(o, "video_bytes"):
                        video_bytes = getattr(o, "video_bytes", None) or getattr(o, "data", None)
                        if video_bytes:
                            break
        except Exception as e:
            print(f"Interactions video call fallback: {e}")

        if not video_bytes:
            video_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + prompt.encode("utf-8")

        filename = f"recipe_video_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact to ToolContext for Playground Artifacts panel
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception as e:
                print(f"Warning: Failed to save video artifact to tool_context: {e}")

        # 2. Upload same video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Video generation failed: {str(e)}"


AGENT_ENGINE_RESOURCE_NAME = "projects/472679648067/locations/us-east4/reasoningEngines/5311986964390477824"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
)
code_executor._agent_engine_creation_lock = None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a helpful AI pantry and recipe assistant designed to provide accurate "
        "and personalized information."
    ),
    workflow_description=(
        "Analyze the request and return structured UI when appropriate.\n\n"
        "CRITICAL ALLERGY & MEMORY DIRECTIVE:\n"
        "1. Always pay close attention to any food allergies, intolerances, and dietary restrictions mentioned by the user.\n"
        "2. Store and recall all user allergies (e.g., peanuts, gluten, dairy, shellfish, low-sodium, tree nuts) across all conversations.\n"
        "3. Never suggest or recommend any recipe, ingredient, or meal that contains known allergens for the user.\n"
        "4. Actively apply remembered allergy constraints to all pantry management and recipe recommendation responses.\n\n"
        "PANTRY, RECIPES, GROCERY, MAPS, HERBAL RETRIEVAL, CODE EXECUTION, IMAGE & VIDEO GENERATION MANAGEMENT:\n"
        "- Use `get_pantry_items` to inspect current ingredients stored in the Firestore database.\n"
        "- Use `add_or_update_pantry_item` when the user adds or updates items in their pantry.\n"
        "- Use `delete_pantry_item` when items are removed or consumed.\n"
        "- Use `generate_shopping_list` to save a list of missing ingredients required for a recipe to Firestore.\n"
        "- Use `fetch_external_recipes` to look up real recipe ideas and cooking instructions from TheMealDB public API.\n"
        "- Use `geocode_address` to convert an address or city into latitude/longitude coordinates.\n"
        "- Use `find_nearby_places` to search for nearby grocery stores, supermarkets, or bakeries via Google Places API (New).\n"
        "- Use `consult_gutenberg_herbal` to search the Project Gutenberg Herbal corpus for traditional herbal remedies and plant facts.\n"
        "- Use `generate_recipe_image` to generate food photography images for recipes and dishes using gemini-3.1-flash-lite-image model.\n"
        "- Use `generate_recipe_video` to generate short food videos using Google's Omni model (gemini-omni-flash-preview) in the global region.\n"
        "- Use Python code execution to solve complex math, calculate nutrition metrics, or process data safely in a sandbox environment."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=False,
    include_examples=True,
)



root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        location="us-east4",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        get_weather,
        get_current_time,
        get_pantry_items,
        add_or_update_pantry_item,
        delete_pantry_item,
        generate_shopping_list,
        fetch_external_recipes,
        geocode_address,
        find_nearby_places,
        consult_gutenberg_herbal,
        generate_recipe_image,
        generate_recipe_video,
        PreloadMemoryTool(),
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)




