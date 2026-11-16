import json
import os
import re
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()


@app.get("/")
def accueil():
  return {"statut": "Serveur SEBA en ligne"}


@app.get("/images")
def recuperer_images(url_tableau: str, limite: int = 3):
  # Récupération sécurisée du cookie stocké dans les paramètres de Render
  cookie_pinterest = os.environ.get("PINTEREST_COOKIE", "")

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
  }

  if cookie_pinterest:
    headers["Cookie"] = cookie_pinterest

  try:
    reponse = requests.get(url_tableau, headers=headers, timeout=15)
    reponse.raise_for_status()
  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Erreur de connexion Pinterest : {e}"
    )

  urls_trouvees = []

  # Extraction des liens d'images haute résolution présents dans les données de la page
  soup = BeautifulSoup(reponse.text, "html.parser")

  # Pinterest intègre les données JSON des épingles dans une balise script __PWS_DATA__
  script_data = soup.find("script", id="__PWS_DATA__")
  if script_data and script_data.string:
    # Recherche directe des URLs d'images Pinterest (pinimg.com) dans le JSON
    liens_bruts = re.findall(
        r"https://i\.pinimg\.com/(?:236x|474x|736x|originals)/[a-zA-Z0-9/_-]+\.(?:jpg|png|webp)",
        script_data.string,
    )
    for lien in liens_bruts:
      lien_hd = lien.replace("/236x/", "/736x/").replace("/474x/", "/736x/")
      if lien_hd not in urls_trouvees:
        urls_trouvees.append(lien_hd)
        if len(urls_trouvees) >= limite:
          break

  return {"nombre": len(urls_trouvees), "images": urls_trouvees}
