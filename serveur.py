from io import BytesIO
from PIL import Image
import requests

# L'adresse de votre serveur Render avec /images à la fin
URL_MON_SERVEUR = "https://onrender.com"


def afficher_images_depuis_mon_serveur(url_tableau: str, limite: int = 3):
  print("Connexion à votre serveur en ligne...")
  parametres = {"url_tableau": url_tableau, "limite": limite}

  try:
    reponse = requests.get(URL_MON_SERVEUR, params=parametres, timeout=60)
    reponse.raise_for_status()

    donnees = reponse.json()
    liste_images = donnees.get("images", [])

    if not liste_images:
      print("Aucune image trouvée. Vérifiez que le cookie est bien sur Render.")
      return

    print(f"{len(liste_images)} image(s) reçue(s) ! Affichage en cours...")

    for index, img_url in enumerate(liste_images, start=1):
      print(f"Ouverture image {index} : {img_url}")
      img_data = requests.get(img_url).content
      Image.open(BytesIO(img_data)).show()

  except Exception as e:
    print(f"Erreur : {e}")


if __name__ == "__main__":
  mon_tableau = "https://pinterest.com"
  afficher_images_depuis_mon_serveur(mon_tableau, limite=3)
