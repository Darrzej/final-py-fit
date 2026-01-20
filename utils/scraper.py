import requests
from bs4 import BeautifulSoup

class FitnessScraper:
    def __init__(self):
        # Using a reliable site for fitness news
        self.url = "https://www.muscleandfitness.com/workout-routines/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_latest_articles(self):
        """Scrapes the latest workout headlines."""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article titles in the site's grid
            articles = soup.find_all('h3', limit=5)
            titles = [art.get_text().strip() for art in articles if len(art.get_text().strip()) > 5]
            
            return titles if titles else ["Keep pushing your limits!", "Consistency is key to growth."]
        except Exception:
            return ["Stay focused on your goals.", "Remember to hydrate today!"]