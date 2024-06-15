import tkinter as tk
from ctypes import windll
from tkinter import messagebox
from tkinter import ttk

import requests as rq
from bs4 import BeautifulSoup

from article import Article, Text, Image
from utils import tnr, RED, DOMAIN, REQUEST_TIMEOUT, ARTICLE_TEXT_PARAMS


windll.shcore.SetProcessDpiAwareness(True) # Enhanced GUI quality.
TITLE = "The Telegraph Paywall Bypass"


class TelegraphPaywallBypass(tk.Tk):
    """Telegraph Paywall Bypass GUI program."""

    def __init__(self) -> None:
        super().__init__()
        ttk.Style().configure(".", font=tnr(15))
        self.title(TITLE)
        self.title_label = tk.Label(
            self, font=tnr(50, True), text="The Telegraph Paywall Bypass")
        self.notebook = ttk.Notebook(self)
        self.url_input_frame = UrlInputFrame(self.notebook)
        self.display_frame = DisplayFrame(self.notebook)
        self.notebook.add(self.url_input_frame, text="URL Input")
        self.notebook.add(self.display_frame, text="Output")
        self.title_label.pack()
        self.notebook.pack()
    
    def render_article(self, article: Article) -> None:
        """Renders an article on screen."""
        self.display_frame.render(article)


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
        self.load_button = ttk.Button(
            self, text="Load", width=15, command=self.load, state="disabled")
        self.info_label.pack(padx=25, pady=25)
        self.entry.pack(padx=25)
        self.feedback_label.pack(padx=25)
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
            self.master.master.render_article(Article(soup))
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred whilst loading the article: {e}")


class DisplayFrame(tk.Frame):
    """Frame to display the fetched article contents."""
    
    def __init__(self, master: ttk.Notebook) -> None:
        super().__init__(master)
        self.initial_label = tk.Label(
            self, font=tnr(25), text="No article to view.")
        self.initial_label.pack(padx=25, pady=25)
        self.canvas = None
    
    def render(self, article: Article) -> None:
        """Renders a given article."""
        self.initial_label.pack_forget()
        if self.canvas is not None:
            self.canvas.destroy()
            self.vertical_scrollbar.destroy()
        self.canvas = tk.Canvas(self, width=1200, height=700)
        self.vertical_scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.vertical_scrollbar.set)
        self.article_frame = ArticleFrame(self, article)
        self.canvas.create_window(
            0, 0, anchor=tk.NW, window=self.article_frame)
        self.canvas.update()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.pack(side=tk.LEFT)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


class ArticleFrame(tk.Frame):
    """Frame of the article, that can be scrolled as needed."""

    def __init__(self, master: tk.Canvas, article: Article) -> None:
        super().__init__(master)
        self.heading = tk.Label(
            self, font=tnr(25, True), text=article.heading,
            **ARTICLE_TEXT_PARAMS)
        self.description = tk.Label(
            self, font=tnr(15), text=article.description,
            **ARTICLE_TEXT_PARAMS)
        self.heading.pack(padx=5, pady=5, anchor=tk.W)
        self.description.pack(padx=5, pady=5, anchor=tk.W)
        for element in article.elements:
            if isinstance(element, Text):
                font = tnr(20, True) if element.is_subheading else tnr(14)
                tk.Label(
                    self, font=font, text=element.contents,
                    **ARTICLE_TEXT_PARAMS).pack(padx=5, pady=5, anchor=tk.W)


def main() -> None:
    """Main procedure of the program."""
    root = TelegraphPaywallBypass()
    root.mainloop()


if __name__ == "__main__":
    main()
