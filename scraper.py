import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_url(url: str) -> str:
    """Ensures URL starts with http:// or https://"""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url

def fetch_website_links(url: str) -> list[str]:
    """Extracts internal and relevant external hyperlinks from a given URL."""
    url = clean_url(url)
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        parsed_base = urlparse(url)
        base_domain = parsed_base.netloc
        
        found_links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            
            full_url = urljoin(url, href)
            parsed_href = urlparse(full_url)
            
            # Keep links on the same domain or close subdomains
            if parsed_href.netloc == base_domain or parsed_href.netloc.endswith(f".{base_domain}"):
                found_links.add(full_url)
                
        return sorted(list(found_links))[:40]  # Cap to top 40 candidate links
    except Exception as e:
        print(f"[Scraper Error] Fetching links failed for {url}: {e}")
        return []

def fetch_website_contents(url: str, max_chars: int = 4000) -> str:
    """Fetches and strips cleaned text body content from a webpage."""
    url = clean_url(url)
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip script, style, nav, and footer noise
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ", strip=True)
        # Collapse excessive whitespace
        cleaned_text = " ".join(text.split())
        return cleaned_text[:max_chars]
    except Exception as e:
        print(f"[Scraper Error] Fetching content failed for {url}: {e}")
        return f"Failed to retrieve content for {url}."
