"""
Contains the Article class comprehensively
representing a Telegraph article.
"""
import datetime as dt
import json
from contextlib import suppress
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class Text:
    """Sub-Heading or paragraph."""
    contents: str
    is_subheading: bool


@dataclass
class Image:
    """Represents an image in the article, including metadata."""
    data: bytes
    caption: str
    credits: str


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
        self.keywords = json_data["keywords"].split(",")
        # Ensure author name is normalised in terms of whitespace.
        self.author_name = " ".join(json_data["author"][0]["name"].split())
        self.description = soup.find(
            "meta", {"property": "og:description"})["content"].strip()

        self.elements = []
        article_element = soup.find("article")
        # TODO - parse article paragraphs, subheadings and images!