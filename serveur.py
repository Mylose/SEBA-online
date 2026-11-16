import json
import os
import re
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()


@app.get("/")
def accueil():
  return {"statut": "Serveur SEBA en ligne"}


@app.get("/images")
def recuperer_images(url_tableau: str, limite: int = 3):
  cookie_pinterest = os.environ.get("PINTEREST_COOKIE", "")

  # Extraction du chemin du tableau (ex: /mtovenaar24/outfit/)
  chemin = urlparse(url_tableau).path
  if not chemin.endswith("/"):
    chemin += "/"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/javascript, */*; q=0.01",
      "X-Requested-With": "XMLHttpRequest",
      "X-Pinterest-AppState": "active",
      "X-Pinterest-Source-Url": chemin,
      "Referer": f"https://pinterest.com{chemin}",
  }

  if cookie_pinterest:
    headers["Cookie"] = cookie_pinterest
    # Extraction du csrftoken s'il est présent dans le cookie
    match_csrf = re.search(r"csrftoken=([^;]+)", cookie_pinterest)
    if match_csrf:
      headers["X-CSRFToken"] = match_csrf.group(1)

  # Appel direct à l'endpoint interne des tableaux Pinterest
  api_url = "https://pinterest.com/resource/BoardFeedResource/get/"
  options = {
      "options": {
          "board_url": chemin,
          "page_size": limite * 2,
          "add_vase": True,
      },
      "context": {},
  }

  try:
    reponse = requests.get(
        api_url,
        headers=headers,
        params={"source_url": chemin, "data": json.dumps(options)},
        timeout=15,
    )
    reponse.raise_for_status()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Erreur API Pinterest : {e}")

  urls_trouvees = []

  # Recherche des URLs haute résolution dans la réponse JSON de l'API interne
  liens_bruts = re.findall(
      r"https://i\.pinimg\.com/(?:736x|474x|236x)/[a-zA-Z0-9/_-]+\.(?:jpg|webp)",
      reponse.text,
  )

  for lien in liens_bruts:
    lien_hd = lien.replace("/236x/", "/736x/").replace("/474x/", "/736x/")
    if lien_hd not in urls_trouvees:
      urls_trouvees.append(lien_hd)
      if len(urls_trouvees) >= limite:
        break

  return {
      "nombre": len(urls_trouvees),
      "cookie_present": bool(cookie_pinterest),
      "images": urls_trouvees,
  }
