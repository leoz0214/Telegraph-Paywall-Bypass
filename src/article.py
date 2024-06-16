"""
Contains the Article class comprehensively
representing a Telegraph article.
"""
import datetime as dt
import json
from contextlib import suppress
from dataclasses import dataclass

import requests as rq
from bs4 import BeautifulSoup

from utils import DOMAIN, HEADERS, REQUEST_TIMEOUT


@dataclass
class Text:
    """Sub-Heading or paragraph."""
    contents: str
    is_subheading: bool


@dataclass
class Image:
    """Represents an image in the article, including metadata."""
    data: bytes
    caption: str = None
    credits: str = None


@dataclass
class Article:
    """Represents a Telegraph article."""
    heading: str
    date_time_published: dt.datetime
    keywords: list[str]
    author_name: str
    description: str
    elements: list[Text | Image]


def load_article_from_soup(soup: BeautifulSoup, fetch_images: bool) -> Article:
    """Loads an article from the HTML contents."""
    json_data = json.loads(
        soup.find("script", {"data-js": "main-json-schema"}).text)
    heading = json_data["headline"]
    # Account for both with and without timezone (just in case).
    for datetime_format in ("%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M"):
        with suppress(ValueError):
            date_time_published = dt.datetime.strptime(
                json_data["datePublished"], datetime_format)
            break
    else:
        raise RuntimeError("Could not determine date published.")
    # Form list of keywords from a comma-separated list.
    keywords = sorted(set(json_data["keywords"].split(",")))
    # Ensure author name is normalised in terms of whitespace.
    author_name = " ".join(json_data["author"][0]["name"].split())
    description = soup.find(
        "meta", {"property": "og:description"})["content"].strip()

    elements = []
    article_element = soup.find("article")
    image = None
    for child in article_element.find_all(recursive=True):
        text = child.text.strip()
        if (
            child.name == "p" and child.get("itemprop") != "description"
            # Ignore 'Recommended' text.
            and child.get("data-test") != "cmp-teaser__pretitle"
        ):
            # Paragraph of text.
            if image is not None:
                elements.append(image)
                image = None
            elements.append(Text(text, False))
        if (
            child.name == "h2"
            and "u-heading-size-medium" in child.get("class", "")
        ):
            # Subheading.
            if image is not None:
                elements.append(image)
                image = None
            elements.append(Text(text, True))
        if not fetch_images:
            # IMAGES OFF - DO NOT CONTINUE FURTHER.
            continue
        if child.name == "picture":
            # Image (use <img> inside the <picture>)
            response = rq.get(
                f"https://{DOMAIN}/{child.find('img')['src']}",
                headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Image fetch status code: {response.status_code}")
            image = Image(response.content)                
        if child.get("itemprop") == "caption":
            # Image caption (must follow image).
            image.caption = text
        if child.get("itemprop") == "copyrightHolder":
            # Image credits (must follow image).
            image.credits = text.removeprefix("Credit:").strip()
    if image is not None:
        elements.append(image)
    return Article(
        heading, date_time_published, keywords,
        author_name, description, elements)
