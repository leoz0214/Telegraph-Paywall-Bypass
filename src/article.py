"""
Contains the Article class comprehensively
representing a Telegraph article.
"""
import datetime as dt
import json
import io
from contextlib import suppress
from dataclasses import dataclass

import requests as rq
from bs4 import BeautifulSoup
from PIL import Image as PilImage

from utils import DOMAIN, HEADERS, REQUEST_TIMEOUT


@dataclass
class Text:
    """Sub-Heading or paragraph."""
    contents: str
    is_subheading: bool


@dataclass
class Image:
    """Represents an image in the article, including metadata."""
    data: PilImage.Image
    caption: str = None
    credits: str = None


class Article:

    def __init__(self, soup: BeautifulSoup) -> None:
        json_data = json.loads(
            soup.find("script", {"data-js": "main-json-schema"}).text)
        self.heading = json_data["headline"]
        # Account for both with and without timezone (just in case).
        for datetime_format in ("%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M"):
            with suppress(ValueError):
                self.date_time_published = dt.datetime.strptime(
                    json_data["datePublished"], datetime_format)
                break
        else:
            raise RuntimeError("Could not determine date published.")
        # Form list of keywords from a comma-separated list.
        self.keywords = json_data["keywords"].split(",")
        # Ensure author name is normalised in terms of whitespace.
        self.author_name = " ".join(json_data["author"][0]["name"].split())
        self.description = soup.find(
            "meta", {"property": "og:description"})["content"].strip()

        self.elements = []
        article_element = soup.find("article")
        image = None
        for child in article_element.find_all(recursive=True):
            text = child.text.strip()
            if child.name == "p" and child.get("itemprop") != "description":
                # Paragraph of text.
                if image is not None:
                    self.elements.append(image)
                    image = None
                self.elements.append(Text(text, False))
            if (
                child.name == "h2"
                and "u-heading-size-medium" in child.get("class", "")
            ):
                # Subheading.
                if image is not None:
                    self.elements.append(image)
                    image = None
                self.elements.append(Text(text, True))
            if child.name == "picture":
                # Image (use <img> inside the <picture>)
                response = rq.get(
                    f"https://{DOMAIN}/{child.find('img')['src']}",
                    headers=HEADERS, timeout=REQUEST_TIMEOUT)
                if response.status_code >= 400:
                    raise RuntimeError(
                        f"Image fetch status code: {response.status_code}")
                with io.BytesIO(response.content) as image_bytes:
                    image = Image(PilImage.open(image_bytes))
            if child.get("itemprop") == "caption":
                # Image caption (must follow image).
                image.caption = text
            if child.get("itemprop") == "copyrightHolder":
                # Image credits (must follow image).
                image.credits = text.removeprefix("Credit:").strip()
        if image is not None:
            self.elements.append(image)
            