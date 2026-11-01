# Manga-get — depot de sources MangaLix Reader

Chaque site est decrit par **un fichier `source.json`** (selecteurs CSS + URLs),
dans son propre dossier `sources/<id>/`. L'application lit `repository.json`
(l'index, façon Mihon), telecharge les `source.json` listes, et sait alors
lister, rechercher, ouvrir les details, les chapitres et les images.
Ajouter un site = ajouter un dossier + une ligne dans `repository.json`, sans toucher a l'appli.

```
repository.json              index des sources (URL raw GitHub a donner a l'appli)
sources/mangalek/source.json source du site https://mangalik.net
schema/source.schema.json    format d'une source
tools/source_engine.py       moteur de reference (specification executable pour l'appli)
tools/test_source.py         tests hors ligne sur tests/fixtures/
tests/fixtures/              pages HTML reelles du site
.github/workflows/           validation automatique a chaque push
```

## Source `mangalek` (site WordPress, theme Madara)

| Etape | Etat | Detail |
|---|---|---|
| Liste / cartes + page suivante | verifie sur fichier reel | `/page/{page}/`, 30 mangas par page, lien `a.nextpostslink` |
| Details | verifie sur fichier reel | titre, couverture, genres, description, statut |
| Images d'un chapitre | verifie sur fichier reel | `.reading-content img.wp-manga-chapter-img` (Referer requis) |
| Liste des chapitres | **non verifie** | chargee par AJAX ; URL/selecteurs standard Madara |
| Recherche (liste complete) | **non verifie** | selecteurs standard Madara |
| Recherche rapide (titre + url) | verifie dans le script de la page | `admin-ajax.php`, action `wp-manga-search-manga` |

Les deux lignes « non verifie » se confirment avec deux captures (voir `tests/fixtures/README.md`).

## Tester

```bash
pip install beautifulsoup4
python3 -I tools/test_source.py
```

## Format d'un selecteur

```json
{ "selector": ".post-title h3 a", "attr": "href" }
```
`attr` : `"text"`, un nom d'attribut, ou une liste essayee dans l'ordre
(`["data-src","src"]`). `multiple: true` renvoie une liste. `optional: true`
autorise l'absence.

## Utiliser dans l'appli

Publier ce depot sur GitHub, puis donner a l'appli l'URL :
`https://raw.githubusercontent.com/<utilisateur>/Manga-get/main/repository.json`
