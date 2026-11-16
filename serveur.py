import json
import os
import re
from urllib.parse import urlparse
from fastapi import FastAPI
import requests

app = FastAPI()


@app.get("/")
def accueil():
  return {"statut": "Serveur SEBA en ligne"}


@app.get("/images")
def recuperer_images(url_tableau: str, limite: int = 3):
  cookie_pinterest = os.environ.get("PINTEREST_COOKIE", "")

  chemin = urlparse(url_tableau).path
  if not chemin.endswith("/"):
    chemin += "/"

  # Récupération ou génération d'un jeton CSRF requis par Pinterest
  match_csrf = re.search(r"csrftoken=([^;]+)", cookie_pinterest)
  csrf_token = match_csrf.group(1) if match_csrf else "1234567890abcdef"

  cookie_complet = cookie_pinterest
  if cookie_pinterest and "csrftoken=" not in cookie_pinterest:
    cookie_complet = f"{cookie_pinterest}; csrftoken={csrf_token}"

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
      "X-CSRFToken": csrf_token,
      "Referer": f"https://pinterest.com{chemin}",
  }

  if cookie_complet:
    headers["Cookie"] = cookie_complet

  # Utilisation obligatoire de ://pinterest.com
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
  except Exception as e:
    return {"erreur": f"Échec réseau : {str(e)}", "images": []}

  # Si Pinterest bloque encore, on renvoie le code et le message exact sans planter (plus d'erreur 500)
  if reponse.status_code != 200:
    return {
        "erreur": f"Pinterest a répondu avec le code {reponse.status_code}",
        "detail": reponse.text[:300],
        "images": [],
    }

  urls_trouvees = []
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
      "images": urls_trouvees,
  }
