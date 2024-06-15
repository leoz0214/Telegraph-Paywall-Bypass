import tkinter as tk
from ctypes import windll
from tkinter import messagebox
from tkinter import ttk

import requests as rq
from bs4 import BeautifulSoup

from article import Article
from utils import tnr, RED, DOMAIN, REQUEST_TIMEOUT


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
        self.notebook.add(self.url_input_frame, text="URL Input")
        self.title_label.pack()
        self.notebook.pack()


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
            article = Article(soup)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred whilst loading the article: {e}")


def main() -> None:
    """Main procedure of the program."""
    root = TelegraphPaywallBypass()
    root.mainloop()


if __name__ == "__main__":
    main()
