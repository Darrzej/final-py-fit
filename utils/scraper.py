import requests
from bs4 import BeautifulSoup

class FitnessScraper:
    def __init__(self):
        self.url = "https://www.muscleandfitness.com/workout-routines/"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def get_latest_articles(self):
        try:
            res = requests.get(self.url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.find_all('h3', limit=5)
            return [a.get_text().strip() for a in articles if len(a.get_text()) > 5]
        except:
            return ["Focus on form over weight.", "Consistency beats intensity."]