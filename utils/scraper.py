import requests
from bs4 import BeautifulSoup

def get_fitness_tips():
    try:
        url = "https://www.muscleandfitness.com/workouts/workout-tips/"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        # Scrape a specific tip or headline
        tip = soup.find("h2").text if soup.find("h2") else "Consistency is key!"
        return f"Pro Tip: {tip}"
    except:
        return "Consistency is the secret to all fitness progress!"