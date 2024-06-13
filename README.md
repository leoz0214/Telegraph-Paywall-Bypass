# The Telegraph Paywall Bypass

## Overview
The Telegraph is a very commonly read newspaper in the United Kingdom, offering high-quality articles that allow readers to keep up with the news. However, there is unfortunately a paywall that limits the number of free articles that can be read by a signed-in user before requiring a subscription to continue reading articles. This is frustrating and unfortunate, but luckily, there is actually a shocking bypass.

Likely due to a lack of technical expertise, JavaScript code is used to prevent the article being read in full without signing in (or if the number of free articles has been reached, without subscribing). However, the article contents such as text and images are still existent in the HTML source even whenever it is visually locked. Of course, the average user will never realise it is possible to read the article contents through HTML, similarly due to the average user not having a lot of technical expertise.

Nonetheless, this project aims to in summary, be able to accept a Telegraph article URL and render the article contents onto a GUI screen, also allowing exporting the article into various formats such as documents. Whilst at it, relevant metadata may also be extracted, such as date and author. It is fairly simple but interesting to perform.

## Planned Features
Below is a list of target features to implement in this project:
- Create a simple GUI as the user interface.
- Fetch an article given the URL.
- Display the article heading, description, subheadings, paragraphs, text, images and metadata (date, author) on screen.
- Provide settings to optionally exclude images/metadata. Not rendering images in particular saves a lot of bandwidth.
- Export the article in DOCX or PDF form with the ability to adjust font size.
- Save fetched articles in a database so they can be read again in the future without re-requesting.

Note: perfection is not the goal - it will be too demanding to embed video content and preserving formatting and hyperlinks is overkill.

At the end of the day, if you are serious about reading the Telegraph and can afford to subscribe, do so.