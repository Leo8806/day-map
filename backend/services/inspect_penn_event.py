
import requests
from bs4 import BeautifulSoup

# --------------------------------------------------
# Event Page to Inspect
# --------------------------------------------------

URL = (
    "https://events.engineering.upenn.edu/event/"
    "meam-ph-d-thesis-defense-fracture-of-brittle-and-"
    "elastic-plastic-lattices-with-varying-relative-density/"
)

# --------------------------------------------------
# Fetch Event Page
# --------------------------------------------------

response = requests.get(
    URL,
    timeout=15
)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

# --------------------------------------------------
# Find Possible Description Containers
# --------------------------------------------------

selectors = [
    ".tribe-events-single-event-description",
    ".tribe-events-content",
    ".entry-content",
    ".event-description",
    "article",
    "main",
]

for selector in selectors:
    elements = soup.select(selector)

    print(f"\n=== {selector} ===")
    print(f"Matches: {len(elements)}")

    for element in elements[:2]:
        print(
            element.get_text(
                "\n",
                strip=True
            )[:2000]
        )


# --------------------------------------------------
# Inspect Description HTML Structure
# --------------------------------------------------

print("\n=== DESCRIPTION HTML STRUCTURE ===")

article = soup.find("article")

if article:
    paragraphs = article.find_all("p")

    print(f"Found {len(paragraphs)} paragraphs")

    for index, paragraph in enumerate(paragraphs[:10]):
        print(f"\nParagraph {index + 1}")

        print("Parent tag:", paragraph.parent.name)
        print("Parent classes:", paragraph.parent.get("class"))

        print(
            "Text:",
            paragraph.get_text(" ", strip=True)[:300]
        )

