import io
import tkinter as tk
from ctypes import windll
from tkinter import messagebox
from tkinter import ttk

import requests as rq
from bs4 import BeautifulSoup
from PIL import Image as PilImage, ImageTk

from article import Article, load_article_from_soup, Text, Image
from data import insert_article, load_articles
from utils import tnr, RED, DOMAIN, REQUEST_TIMEOUT, ARTICLE_TEXT_PARAMS


windll.shcore.SetProcessDpiAwareness(True) # Enhanced GUI quality.
TITLE = "The Telegraph Paywall Bypass"
ARTICLE_TABLE_HEADINGS_WIDTHS = {
    "ID": 75,
    "Heading": 800,
    "Author": 300,
    "Published": 225,
    "Fetched": 225,
}
ARTICLE_TABLE_HEIGHT = 15
TREEVIEW_ROW_HEIGHT = 25


class TelegraphPaywallBypass(tk.Tk):
    """Telegraph Paywall Bypass GUI program."""

    def __init__(self) -> None:
        super().__init__()
        ttk.Style().configure(".", font=tnr(15))
        ttk.Style().configure("Treeview.Heading", font=tnr(15, True))
        ttk.Style().configure(
            "Treeview", font=tnr(11), rowheight=TREEVIEW_ROW_HEIGHT)
        self.title(TITLE)
        self.title_label = tk.Label(
            self, font=tnr(50, True), text="The Telegraph Paywall Bypass")
        self.notebook = ttk.Notebook(self)
        self.url_input_frame = UrlInputFrame(self.notebook)
        self.articles_frame = ArticlesFrame(self.notebook)
        self.notebook.add(self.url_input_frame, text="URL Input")
        self.notebook.add(self.articles_frame, text="Saved Articles")
        self.title_label.pack()
        self.notebook.pack()
    
    def render_article(self, article: Article) -> None:
        """Renders an article on screen."""
        ArticleToplevel(
            article, self.url_input_frame.settings_frame.display_metadata)


class UrlInputFrame(tk.Frame):
    """Allows a Telegraph Article URL to be input and validated."""

    def __init__(self, master: ttk.Notebook) -> None:
        super().__init__(master)
        self._url = tk.StringVar()
        self._url.trace("w", lambda *_: self.validate_url())
        self.info_label = tk.Label(
            self, font=tnr(15), text=(
                "Enter the URL of the article you would "
                "like to be able to read."))
        self.entry = ttk.Entry(
            self, width=100, font=tnr(12), textvariable=self._url)
        self.feedback_label = tk.Label(self, fg=RED, font=tnr(8))
        self.settings_frame = SettingsFrame(self)
        self.load_button = ttk.Button(
            self, text="Load", width=15, command=self.load, state="disabled")
        self.info_label.pack(padx=25, pady=25)
        self.entry.pack(padx=25)
        self.feedback_label.pack(padx=25)
        self.settings_frame.pack(padx=25, pady=25)
        self.load_button.pack(padx=25, pady=25)
    
    @property
    def url(self) -> str:
        # Normalise URL, removing the protocol and www if specified.
        url = self._url.get().strip().lower()
        if url.startswith("http://"):
            url = url.removeprefix("http://")
        elif url.startswith("https://"):
            url = url.removeprefix("https://")
        if url.startswith("www."):
            url = url.removeprefix("www.")
        return url

    def validate_url(self) -> None:
        """Validate the URL in real time."""
        self.load_button.config(state="disabled")
        self.feedback_label.config(text="")
        if not self._url.get().strip():
            # No input at all.
            return
        url = self.url
        parts = url.split("/")
        if not url or parts[0] != DOMAIN or len(parts) < 3:
            self.feedback_label.config(text="Invalid URL")
            return
        self.load_button.config(state="normal")
    
    def load(self) -> None:
        """Loads the article at the input URL if possible."""
        url = f"https://{self.url}"
        try:
            response = rq.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code >= 400:
                raise RuntimeError(f"Status code {response.status_code}")
            soup = BeautifulSoup(response.content, "html.parser")
            self.master.master.render_article(
                load_article_from_soup(soup, self.settings_frame.display_images))
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred whilst loading the article: {e}")


class ArticleToplevel(tk.Toplevel):
    """Toplevel to display the fetched article contents."""
    
    def __init__(self, article: Article, display_metadata: bool) -> None:
        super().__init__()
        self.title(article.heading)
        self.canvas = tk.Canvas(self, width=1200, height=700)
        self.vertical_scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.vertical_scrollbar.set)
        self.article_frame = ArticleFrame(self, article, display_metadata)
        self.canvas.create_window(
            0, 0, anchor=tk.NW, window=self.article_frame)
        self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.pack(side=tk.LEFT)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


class ArticleFrame(tk.Frame):
    """Frame of the article, that can be scrolled as needed."""

    def __init__(
        self, master: tk.Canvas, article: Article, display_metdata: bool
    ) -> None:
        super().__init__(master)
        self.heading = tk.Label(
            self, font=tnr(25, True), text=article.heading,
            **ARTICLE_TEXT_PARAMS)
        self.description = tk.Label(
            self, font=tnr(15), text=article.description,
            **ARTICLE_TEXT_PARAMS)
        self.options_frame = ArticleOptionsFrame(self, article)
        self.heading.pack(padx=5, pady=5, anchor=tk.W)
        self.description.pack(padx=5, pady=5, anchor=tk.W)
        if article.date_time_published is not None and display_metdata:
            # Metadata enabled.
            metadata_lines = [
                f"{article.author_name} | "
                f"{article.date_time_published.strftime('%Y-%m-%dT%H:%M%z')}",
                f"Topics: {' | '.join(article.keywords)}"]
            self.metadata = tk.Label(
                self, font=tnr(11), text="\n".join(metadata_lines),
                **ARTICLE_TEXT_PARAMS)
            self.metadata.pack(padx=5, pady=5, anchor=tk.W)
        self.options_frame.pack(padx=5, pady=5, anchor=tk.W)
        for element in article.elements:
            if isinstance(element, Text):
                font = tnr(20, True) if element.is_subheading else tnr(14)
                tk.Label(
                    self, font=font, text=element.contents,
                    **ARTICLE_TEXT_PARAMS).pack(padx=5, pady=5, anchor=tk.W)
            else:
                ImageFrame(self, element).pack(padx=5, pady=5, anchor=tk.W)


class ArticleOptionsFrame(tk.Frame):
    """
    Allows the current article to be exported
    in document form or saved to the database.
    """

    def __init__(self, master: ArticleFrame, article: Article) -> None:
        super().__init__(master)
        self.article = article
        self.save_button = ttk.Button(
            self, text="Save", width=15, command=self.save)
        self.export_docx_button = ttk.Button(
            self, text="Export DOCX", width=15, command=self.export_docx)
        self.export_pdf_button = ttk.Button(
            self, text="Export PDF", width=15, command=self.export_pdf)
        self.save_button.grid(row=0, column=0, padx=5, pady=5)
        self.export_docx_button.grid(row=0, column=1, padx=5, pady=5)
        self.export_pdf_button.grid(row=0, column=2, padx=5, pady=5)
    
    def save(self) -> None:
        """Saves the article to the database for future viewing."""
        try:
            insert_article(self.article)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred whilst saving the article: {e}")
            return
        messagebox.showinfo("Success", "Successfully saved the article.")
    
    def export_docx(self) -> None:
        """Allows the user to export the article in DOCX form."""

    def export_pdf(self) -> None:
        """Allows the user to export the article in PDF form."""


class ImageFrame(tk.Frame):
    """Frame holding an image and its caption/credits."""

    def __init__(self, master: ArticleFrame, image: Image) -> None:
        super().__init__(master)
        with io.BytesIO(image.data) as image_bytes:
            pil_image = PilImage.open(image_bytes)
            self.image = ImageTk.PhotoImage(pil_image)
        self.image_label = tk.Label(self, image=self.image)
        info_text = ""
        if image.caption is not None:
            info_text += image.caption
        if image.credits is not None:
            info_text += f" © {image.credits}"
        self.info_label = tk.Label(
            self, font=tnr(11), text=info_text, **ARTICLE_TEXT_PARAMS)
        self.image_label.pack(padx=5, pady=5, anchor=tk.W)
        if info_text:
            self.info_label.pack(padx=5, pady=5, anchor=tk.W)


class SettingsFrame(tk.Frame):
    """Controls whether to display/fetch metadata and images."""

    def __init__(self, master: UrlInputFrame) -> None:
        super().__init__(master)
        self._metadata = tk.BooleanVar(value=True)
        self._images = tk.BooleanVar(value=True)
        for (text, variable) in (
            ("Display metadata", self._metadata),
            ("Display images", self._images)
        ):
            checkbutton = tk.Checkbutton(
                self, text=text, variable=variable, font=tnr(15))
            checkbutton.pack()
    
    @property
    def display_metadata(self) -> bool:
        return self._metadata.get()

    @property
    def display_images(self) -> bool:
        return self._images.get()


class ArticlesFrame(tk.Frame):
    """
    Frame storing a table of saved articles
    that can be opened (viewed) and deleted.
    """

    def __init__(self, master: ttk.Notebook) -> None:
        super().__init__(master)
        self.articles = load_articles()
        self.table = ArticlesTable(self)
        self.table.pack(padx=25, pady=25)
        self.table.display_articles(self.articles)


class ArticlesTable(tk.Frame):
    """Contains the articles table (treeview) and scrollbar."""

    def __init__(self, master: ArticlesFrame) -> None:
        super().__init__(master)
        self.treeview = ttk.Treeview(
            self, columns=tuple(ARTICLE_TABLE_HEADINGS_WIDTHS),
            height=ARTICLE_TABLE_HEIGHT, show="headings")
        for heading, width in ARTICLE_TABLE_HEADINGS_WIDTHS.items():
            self.treeview.heading(heading, text=heading)
            self.treeview.column(heading, width=width)
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.treeview.yview)
        self.treeview.config(yscrollcommand=self.scrollbar.set)
        self.treeview.grid(row=0, column=0)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
    
    def display_articles(self, articles: list[Article]) -> None:
        """Displays the given list of articles in the table."""
        for article in articles:
            date_time_published = (
                article.date_time_published.strftime("%Y-%m-%dT%H:%M%z"))
            date_time_fetched = (
                article.date_time_fetched.strftime("%Y-%m-%dT%H:%M%z"))
            table_record = (
                article.id, article.heading, article.author_name,
                date_time_published, date_time_fetched)
            self.treeview.insert("", "end", values=table_record)


def main() -> None:
    """Main procedure of the program."""
    root = TelegraphPaywallBypass()
    root.mainloop()


if __name__ == "__main__":
    main()
