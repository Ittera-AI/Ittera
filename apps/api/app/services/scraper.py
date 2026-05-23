import httpx
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, Any

class ScraperService:
    @staticmethod
    def validate_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False
            # Basic check to reject local IPs or localhost
            hostname = parsed.hostname or ""
            if hostname in ["localhost", "127.0.0.1", "0.0.0.0"] or hostname.startswith("192.168.") or hostname.startswith("10."):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    async def scrape_x(url: str) -> Dict[str, Any]:
        """
        Scrapes a Twitter/X profile using the syndication API for zero-cost scraping.
        Extracts user info (bio, followers, etc.) and recent tweets.
        """
        if not ScraperService.validate_url(url):
            raise ValueError("Invalid or restricted URL")

        try:
            parsed = urlparse(url)
            # Extract username from path (e.g., /elonmusk -> elonmusk)
            path_parts = [p for p in parsed.path.split("/") if p]
            if not path_parts:
                raise ValueError("No username found in URL")
            username = path_parts[0]

            syndication_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                }
                response = await client.get(syndication_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                next_data_script = soup.find("script", id="__NEXT_DATA__")
                
                if not next_data_script or not next_data_script.string:
                    raise ValueError("Could not find timeline data in response")

                import json
                data = json.loads(next_data_script.string)
                
                # Extract user details and tweets
                page_props = data.get("props", {}).get("pageProps", {})
                timeline = page_props.get("timeline", {})
                entries = timeline.get("entries", [])

                clean_parts = []
                user_info = {}
                tweets = []

                if entries:
                    # Get user info from the first valid tweet
                    for entry in entries:
                        tweet_data = entry.get("content", {}).get("tweet", {})
                        if tweet_data:
                            user = tweet_data.get("user", {})
                            if user and not user_info:
                                user_info = {
                                    "name": user.get("name", ""),
                                    "screen_name": user.get("screen_name", ""),
                                    "description": user.get("description", ""),
                                    "followers_count": user.get("followers_count", 0),
                                }
                                clean_parts.append(f"Name: {user_info['name']}")
                                clean_parts.append(f"Handle: @{user_info['screen_name']}")
                                clean_parts.append(f"Bio: {user_info['description']}")
                                clean_parts.append(f"Followers: {user_info['followers_count']}")
                                clean_parts.append("\nRecent Tweets:")
                                
                            text = tweet_data.get("text", "")
                            if text:
                                tweets.append(text)
                                clean_parts.append(f"- {text}")

                if not clean_parts:
                    # Fallback if no tweets found but page loaded
                    clean_text = "No profile or tweet data found."
                    title = f"@{username} on X"
                    description = ""
                else:
                    clean_text = "\n".join(clean_parts)
                    title = f"{user_info.get('name', username)} (@{user_info.get('screen_name', username)}) on X"
                    description = user_info.get("description", "")

                # Limit size
                max_chars = 20000
                if len(clean_text) > max_chars:
                    clean_text = clean_text[:max_chars]

                content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

                return {
                    "url": url,
                    "title": title,
                    "description": description,
                    "clean_text": clean_text,
                    "metadata": {
                        "username": username,
                        "tweets_scraped": len(tweets)
                    },
                    "content_hash": content_hash
                }
        except Exception as e:
            raise ValueError(f"Failed to scrape X profile: {str(e)}")

    @staticmethod
    async def scrape_url(url: str, source_type: str) -> Dict[str, Any]:
        """
        Entrypoint for scraping based on source type.
        """
        if source_type.lower() == "x":
            return await ScraperService.scrape_x(url)
        else:
            # We are only implementing X right now as per user instruction.
            raise NotImplementedError(f"Scraping for source type '{source_type}' is not yet implemented.")
