"""Database handling - saving article data and fetching it."""
import datetime as dt
import pathlib
import sqlite3

from article import Article, Text, Image


# Paths
DATA_FOLDER = pathlib.Path(__file__).parent.parent / "data"
DATA_FOLDER.mkdir(exist_ok=True)
DATABASE = DATA_FOLDER / "articles.db"
# Table names
ARTICLE_TABLE = "articles"
TEXT_TABLE = "texts"
IMAGE_TABLE = "images"
ARTICLE_KEYWORD_TABLE = "articles_keywords"
KEYWORD_TABLE = "keywords"


class Database:
    """Sqlite3 database wrapper."""

    def __enter__(self) -> sqlite3.Cursor:
        """Start of database processing context manager."""
        self.connection = sqlite3.connect(DATABASE)
        cursor = self.connection.cursor()
        # Ensure foreign keys are enabled for integrity.
        cursor.execute("PRAGMA foreign_keys = ON")
        return cursor
    
    def __exit__(self, exception: Exception | None, *_) -> None:
        """Context manager exited - commit if no error occurred."""
        if exception is None:
            self.connection.commit()
        self.connection.close()
        self.connection = None


def create_tables() -> None:
    """Creates all tables in case they do not exist."""
    with Database() as cursor:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ARTICLE_TABLE}(
                article_id INTEGER PRIMARY KEY AUTOINCREMENT,
                heading TEXT, description TEXT, author_name TEXT,
                published_timestamp INTEGER, fetched_timestamp INTEGER
            )""")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TEXT_TABLE}(
                text_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER, is_subheading INTEGER,
                contents TEXT, position INTEGER,
                FOREIGN KEY (article_id) REFERENCES {ARTICLE_TABLE}(article_id)
            )""")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {IMAGE_TABLE}(
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER, data BLOB, caption TEXT,
                credits TEXT, position INTEGER,
                FOREIGN KEY (article_id) REFERENCES {ARTICLE_TABLE}(article_id)
            )""")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {KEYWORD_TABLE}(
                keyword_id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT
            )""")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ARTICLE_KEYWORD_TABLE}(
                article_id INTEGER, keyword_id INTEGER,
                PRIMARY KEY (article_id, keyword_id)
            )""")


def insert_article(article: Article) -> None:
    """Inserts an article into the database."""
    published_timestamp = int(article.date_time_published.timestamp())
    fetched_timestamp = int(article.date_time_fetched.timestamp())
    with Database() as cursor:
        cursor.execute(
            f"INSERT INTO {ARTICLE_TABLE} VALUES(NULL, ?, ?, ?, ?, ?)",
            (article.heading, article.description, article.author_name,
                published_timestamp, fetched_timestamp))
        article_id = cursor.lastrowid
        for pos, element in enumerate(article.elements):
            if isinstance(element, Text):
                cursor.execute(
                    f"INSERT INTO {TEXT_TABLE} VALUES(NULL, ?, ?, ?, ?)",
                    (article_id, element.is_subheading, element.contents, pos))
            else:
                cursor.execute(
                    f"INSERT INTO {IMAGE_TABLE} VALUES(NULL, ?, ?, ?, ?, ?)",
                    (article_id, element.data, element.caption,
                        element.credits, pos))
        for keyword in article.keywords:
            keyword_id = cursor.execute(
                f"SELECT keyword_id FROM {KEYWORD_TABLE} "
                    "WHERE keyword = ?", (keyword,)).fetchone()
            if keyword_id is None:
                cursor.execute(
                    f"INSERT INTO {KEYWORD_TABLE} VALUES(NULL, ?)", (keyword,))
                keyword_id = cursor.lastrowid
            else:
                keyword_id = keyword_id[0]
            cursor.execute(
                f"INSERT INTO {ARTICLE_KEYWORD_TABLE} VALUES(?, ?)",
                (article_id, keyword_id))
            

def load_article_from_record(record: tuple, cursor: sqlite3.Cursor) -> Article:
    """Fully loads an article given the full main article record."""
    (
        article_id, heading, description,
        author_name, published_timestamp, fetched_timestamp) = record
    date_time_published = dt.datetime.fromtimestamp(published_timestamp)
    date_time_fetched = dt.datetime.fromtimestamp(fetched_timestamp)
    elements_dict = {}
    # Load text elements.
    text_records = cursor.execute(
        "SELECT is_subheading, contents, position "
        f"FROM {TEXT_TABLE} WHERE article_id = ?", (article_id,)).fetchall()
    for record in text_records:
        is_subheading, contents, position = record
        elements_dict[position] = Text(contents, is_subheading)
    # Load image elements.
    image_records = cursor.execute(
        "SELECT data, caption, credits, position "
        f"FROM {IMAGE_TABLE} WHERE article_id = ?", (article_id,)).fetchall()
    for record in image_records:
        data, caption, credits_, position = record
        elements_dict[position] = Image(data, caption, credits_)
    elements = [
        elements_dict[position] for position in range(len(elements_dict))]
    article_keyword_records = cursor.execute(
        f"SELECT keyword_id FROM {ARTICLE_KEYWORD_TABLE} WHERE article_id = ?",
        (article_id,)).fetchall()
    # Load keywords.
    keywords = []
    for record in article_keyword_records:
        keyword = cursor.execute(
            f"SELECT keyword FROM {KEYWORD_TABLE} WHERE keyword_id = ?",
            (record[0],)).fetchone()[0]
        keywords.append(keyword)
    keywords.sort()
    return Article(
        heading, date_time_published, date_time_fetched,
        keywords, author_name, description, elements, article_id)


def load_articles() -> list[Article]:
    """Returns all Articles stored inside the database."""
    with Database() as cursor:
        article_records = cursor.execute(
            f"SELECT * FROM {ARTICLE_TABLE}").fetchall()
        return [
            load_article_from_record(record, cursor)
                for record in article_records]


# Create tables upon startup if they do not exist.
create_tables()
