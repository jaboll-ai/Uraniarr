stringy = """
<div class="trackdetails">
        <a href="/autor/derek+landy-852812/" class="element-link-small ellipsis">Derek Landy</a>
    <p class="element-text-standard ellipsis track-title">1. Auferstehung</p>
</div>
"""

from bs4 import BeautifulSoup
soup = BeautifulSoup(stringy, 'html.parser')
text = soup.find(href=lambda href: href and "/autor/" in href)
print(text)  # Output: Taschenbuch