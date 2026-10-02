"""Seed script for Wanderlust Architect Firestore collection."""

from google.cloud import firestore

FIRESTORE_PROJECT = "qwiklabs-gcp-02-a7e255b6ed17"
COLLECTION_NAME = "destinations"

INITIAL_DESTINATIONS = [
    {
        "id": "kyoto",
        "name": "Kyoto, Japan",
        "country": "Japan",
        "description": "Japan's cultural capital known for historic temples, traditional wooden houses, cherry blossoms, and peaceful bamboo groves.",
        "best_season": "Spring (Mar-May) & Autumn (Oct-Nov)",
        "vibe": "Historic, Cultural, Peaceful",
        "estimated_daily_cost_usd": 160,
        "highlights": ["Fushimi Inari Shrine", "Arashiyama Bamboo Grove", "Kinkaku-ji (Golden Pavilion)", "Gion Geisha District"],
        "image_prompt": "Serene traditional wooden pagoda in Kyoto surrounded by vibrant pink cherry blossoms at sunset.",
    },
    {
        "id": "santorini",
        "name": "Santorini, Greece",
        "country": "Greece",
        "description": "Famed Aegean island featuring cliffside whitewashed buildings, blue-domed churches, and dramatic volcanic sea views.",
        "best_season": "Late Spring (May-Jun) & Early Autumn (Sep-Oct)",
        "vibe": "Romantic, Scenic, Relaxing",
        "estimated_daily_cost_usd": 220,
        "highlights": ["Oia Sunset Viewpoint", "Red Beach", "Akrotiri Archaeological Site", "Fira to Oia Caldera Hike"],
        "image_prompt": "Whitewashed houses with blue domes on Santorini cliffside overlooking sparkling Aegean blue sea at dusk.",
    },
    {
        "id": "banff",
        "name": "Banff National Park, Canada",
        "country": "Canada",
        "description": "Breathtaking Canadian Rockies destination renowned for turquoise glacial lakes, snow-capped peaks, and alpine wildlife.",
        "best_season": "Summer (Jun-Aug) for hiking & Winter (Dec-Mar) for skiing",
        "vibe": "Adventure, Nature, Majestic",
        "estimated_daily_cost_usd": 180,
        "highlights": ["Lake Louise", "Moraine Lake", "Banff Upper Hot Springs", "Johnston Canyon Walk"],
        "image_prompt": "Turquoise waters of Moraine Lake in Banff surrounded by towering Canadian Rocky Mountains and pine trees.",
    },
    {
        "id": "marrakech",
        "name": "Marrakech, Morocco",
        "country": "Morocco",
        "description": "Vibrant imperial city filled with bustling souks, intricate Islamic architecture, peaceful riads, and fragrant spice markets.",
        "best_season": "Spring (Mar-May) & Autumn (Sep-Nov)",
        "vibe": "Exotic, Vibrant, Historical",
        "estimated_daily_cost_usd": 110,
        "highlights": ["Jemaa el-Fnaa Square", "Bahia Palace", "Jardin Majorelle", "Koutoubia Mosque"],
        "image_prompt": "Colorful Moroccan souk in Marrakech with glowing brass lanterns, ceramic tiles, and vibrant spice piles.",
    },
]

def seed_database():
    db = firestore.Client(project=FIRESTORE_PROJECT)
    collection_ref = db.collection(COLLECTION_NAME)

    print(f"Seeding '{COLLECTION_NAME}' collection in project '{FIRESTORE_PROJECT}'...")
    for dest in INITIAL_DESTINATIONS:
        doc_id = dest["id"]
        collection_ref.document(doc_id).set(dest)
        print(f"  ✓ Added/Updated destination: {dest['name']} ({doc_id})")

    print(f"Successfully seeded {len(INITIAL_DESTINATIONS)} items into Firestore!")

if __name__ == "__main__":
    seed_database()
