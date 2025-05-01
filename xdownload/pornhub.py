import re
import time
import requests
from requests.exceptions import ConnectionError, RequestException
from pyquery import PyQuery as pq
from urllib.parse import quote
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import webscrapper module if available
try:
    from webscrapper.client import get_page
    WEBSCRAPPER_AVAILABLE = True
except ModuleNotFoundError:
    WEBSCRAPPER_AVAILABLE = False
    logger.warning("Webscrapper module not found. You can install it with: pip install webscrapper")


def login() -> requests.Session:
    """
    Create and return a session with proper headers for the website.
    
    Returns:
        requests.Session: Configured session object
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Referer": "https://www.pornhub.com/",
        "Accept-encoding": "gzip, deflate",
    }
    ses = requests.Session()
    ses.cookies.clear()
    ses.headers.update(headers)
    
    # Set age verification cookies
    ses.cookies.set("age_verified", "1")
    ses.cookies.set("accessAgeDisclaimerPH", "1")
    
    return ses


def load_ph_page(
    url: str, 
    ses: requests.Session, 
    max_tries: int, 
    scrapper_key: Optional[str] = None, 
    timeout: int = 5
) -> Optional[str]:
    """
    Load a page using webscrapper API or internal session with retries.
    
    Args:
        url: URL to load
        ses: Session object
        max_tries: Maximum number of retries
        scrapper_key: API key for webscrapper service
        timeout: Timeout between retries (in seconds)
        
    Returns:
        HTML content or None if all retries failed
    """
    retries = 0
    data = None
    
    while data is None and retries <= max_tries:
        try:
            if scrapper_key and WEBSCRAPPER_AVAILABLE:
                logger.info("Using Scrapper API")
                result = get_page(url, api_key=scrapper_key)
                
                if result.get("error"):
                    data = None
                    logger.error(f"Scrapper API error: {result.get('error')}")
                else:
                    data = result.get("html")
            else:
                r = ses.get(url, timeout=timeout)
                if r.status_code == 200:
                    data = r.text
                else:
                    logger.error(f"HTTP error: {r.status_code}")
                    data = None
        except ConnectionError:
            retries += 1
            sleep_time = timeout * retries
            logger.warning(f"Connection error, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
        except RequestException as e:
            retries += 1
            sleep_time = timeout * retries
            logger.error(f"Request error: {e}, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            
        if data is None and retries <= max_tries:
            retries += 1
    
    if data is None:
        logger.error(f"Failed to load page after {max_tries} attempts: {url}")
    
    return data


def get_video_info(
    ses: requests.Session, 
    url: str, 
    tries: int = 3, 
    timeout: int = 5, 
    scrapper_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract video information from a video page.
    
    Args:
        ses: Session object
        url: Video URL
        tries: Maximum number of retries
        timeout: Timeout between retries
        scrapper_key: API key for webscrapper service
        
    Returns:
        Dictionary with video information
    """
    # Add Twitter referrer to bypass some restrictions
    if "?" in url:
        url += "&utm_source=twitter"
    else:
        url += "?utm_source=twitter"
        
    data = load_ph_page(url, ses, tries, scrapper_key, timeout)
    
    if not data:
        return {
            "page": url,
            "title": None,
            "categories": [],
            "tags": [],
            "pornstars": [],
            "error": "Failed to load page"
        }
    
    parsed = pq(data)
    title = parsed("h1.title:first").text() or None
    categories = [c.text() for c in parsed(".categoriesWrapper a").items()]
    pornstars = [c.text() for c in parsed(".pornstarsWrapper a.pstar-list-btn").items()]
    tags = [c.text() for c in parsed(".tagsWrapper a").items()]
    
    return {
        "page": url,
        "title": title,
        "categories": categories,
        "tags": tags,
        "pornstars": pornstars,
        "error": None
    }


def parse_pornhub_url(
    ses: requests.Session, 
    url: str, 
    domain: str, 
    DEBUG: bool = False, 
    tries: int = 3, 
    timeout: int = 5, 
    scrapper_key: Optional[str] = None
) -> List[str]:
    """
    Parse a list page and extract video URLs.
    
    Args:
        ses: Session object
        url: List page URL
        domain: Base domain
        DEBUG: Enable debug output
        tries: Maximum number of retries
        timeout: Timeout between retries
        scrapper_key: API key for webscrapper service
        
    Returns:
        List of video URLs
    """
    result = []
    data = load_ph_page(url, ses, tries, scrapper_key, timeout)
    
    if not data:
        logger.error(f"Failed to load page: {url}")
        return result
    
    parsed = pq(data)
    items = parsed.items("li.videoBox a:first")
    i = 0
    
    for el in items:
        i += 1
        video_url = el.attr("href")
        if video_url and "view_video" in video_url:
            if DEBUG:
                logger.info(f"New video URL found: {video_url}")
            
            # Ensure URL is properly formatted
            if video_url.startswith('/'):
                full_url = f"{domain}{video_url}"
            else:
                full_url = f"{domain}/{video_url}"
                
            result.append(full_url)
    
    if i == 0:
        logger.error(f"No videos found on page: {url}")
        if DEBUG:
            logger.debug(f"Page content: {data[:1000]}...")
    
    return result


def search_videos(
    ses: requests.Session,
    query: str,
    pages: List[int] = [2],
    rus: bool = False,
    recent: bool = False,
    DEBUG: bool = False,
    scrapper_key: Optional[str] = None,
    wait_time: int = 10
) -> List[str]:
    """
    Search for videos matching a query.
    
    Args:
        ses: Session object
        query: Search query
        pages: List of page numbers to fetch
        rus: Use Russian domain
        recent: Sort by most recent
        DEBUG: Enable debug output
        scrapper_key: API key for webscrapper service
        wait_time: Time to wait between page loads
        
    Returns:
        List of video URLs
    """
    recent_query = "&o=mr" if recent else ""
    www_domain = "rt" if rus else "www"
    domain = f"https://{www_domain}.pornhub.com"
    
    b_url = (
        f"https://{www_domain}.pornhub.com/video/search?search="
        f"{quote(query)}{recent_query}&p=homemade&page="
    )
    
    result = []
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            logger.info(f"Loading: {url}")
            
        new = parse_pornhub_url(ses, url, domain, DEBUG, scrapper_key=scrapper_key)
        if new:
            result.extend(new)
            
        if p < max(pages) and wait_time > 0:  # Don't wait after the last page
            logger.info(f"Waiting {wait_time} seconds before next request")
            time.sleep(wait_time)  # User behavior emulation
    
    return result


def get_recent_videos(
    ses: requests.Session,
    pages: List[int] = [2],
    rus: bool = False,
    DEBUG: bool = False,
    scrapper_key: Optional[str] = None,
    wait_time: int = 10
) -> List[str]:
    """
    Get recent videos from the home page.
    
    Args:
        ses: Session object
        pages: List of page numbers to fetch
        rus: Use Russian domain
        DEBUG: Enable debug output
        scrapper_key: API key for webscrapper service
        wait_time: Time to wait between page loads
        
    Returns:
        List of video URLs
    """
    result = []
    
    if rus:
        domain = "https://rt.pornhub.com"
        b_url = "https://rt.pornhub.com/video?p=homemade&o=mv&t=a&cc=ru&hd=1&page="
    else:
        domain = "https://www.pornhub.com"
        b_url = "https://www.pornhub.com/video?p=homemade&o=mv&cc=ru&page="

    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            logger.info(f"Loading: {url}")
            
        new = parse_pornhub_url(ses, url, domain, DEBUG, scrapper_key=scrapper_key)
        if new:
            result.extend(new)
            
        if p < max(pages) and wait_time > 0:  # Don't wait after the last page
            logger.info(f"Waiting {wait_time} seconds before next request")
            time.sleep(wait_time)  # User behavior emulation
    
    return result


def get_hot_videos(
    ses: requests.Session,
    pages: List[int] = [2],
    hm: bool = True,
    country: Optional[str] = None,
    DEBUG: bool = False,
    mv: bool = False,
    scrapper_key: Optional[str] = None,
    wait_time: int = 10
) -> List[str]:
    """
    Get hot videos from the home page.
    
    Args:
        ses: Session object
        pages: List of page numbers to fetch
        hm: Filter for homemade videos
        country: Filter by country code
        DEBUG: Enable debug output
        mv: Sort by most viewed instead of hottest
        scrapper_key: API key for webscrapper service
        wait_time: Time to wait between page loads
        
    Returns:
        List of video URLs
    """
    result = []
    domain = "https://www.pornhub.com"
    
    # Build the URL
    if mv:
        b_url = f"{domain}/video?o=mv"  # Most viewed
    else:
        b_url = f"{domain}/video?o=ht"  # Hottest
        
    if hm:
        b_url = f"{b_url}&p=homemade"
        
    if country:
        b_url = f"{b_url}&cc={country}"
        
    b_url = f"{b_url}&page="
    
    for p in pages:
        url = b_url + str(p)
        if DEBUG:
            logger.info(f"Loading: {url}")
            
        new = parse_pornhub_url(ses, url, domain, DEBUG, scrapper_key=scrapper_key)
        if new:
            result.extend(new)
            
        if p < max(pages) and wait_time > 0:  # Don't wait after the last page
            logger.info(f"Waiting {wait_time} seconds before next request")
            time.sleep(wait_time)  # User behavior emulation
    
    return result


if __name__ == "__main__":
    ses = login()
    # example usage:
    for v in search_videos(ses, "blowjob and anal", DEBUG=True)[:5]:
        print("Video:", v)
        print(get_video_info(ses, v))
        time.sleep(5)

    for v in get_recent_videos(ses, DEBUG=True)[:5]:
        print("Video:", v)
        print(get_video_info(ses, v))
        time.sleep(5)
        
