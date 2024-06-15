"""GUI utilities."""


RED = "red"
DOMAIN = "telegraph.co.uk"
REQUEST_TIMEOUT = 5
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}


def tnr(size: int, bold: bool = False, italic: bool = False) -> tuple:
    """Helper function for Times New Roman font."""
    font = ("Times New Roman", size)
    if bold:
        font += ("bold",)
    if italic:
        font += ("italic",)
    return font
