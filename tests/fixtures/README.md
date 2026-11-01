# Fixtures

Pages HTML reelles enregistrees depuis https://mangalik.net (31 oct. 2026) :

| Fichier | Page |
|---|---|
| `latest_page1.html` | accueil (liste des derniers mangas + pagination) |
| `details.html` | page d'un manga (I Bought the Villains With Money) |
| `chapter_pages.html` | page d'un chapitre (chapitre 20, 8 images) |

## A ajouter pour tester le reste (le test les detecte automatiquement)

- `chapters_ajax.html` : la reponse brute de la requete qui charge la liste des chapitres.
  Dans le navigateur : ouvrir la page d'un manga, F12 > Reseau (XHR), recharger,
  reperer la requete `ajax/chapters/` (POST) et copier sa reponse.
- `search_results.html` : le HTML de `https://mangalik.net/?s=villains&post_type=wp-manga`.

Aucune de ces deux pages n'est inventee ici : tant qu'elles manquent, les
sections `chapters` et `search` de `source.json` restent marquees `"verified": false`.
