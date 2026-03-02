# Correcteur Orthographique

## Description
Ce projet est un correcteur orthographique interrogeable à distance
utilisant des sockets UDP et des requêtes HTTP.
Il est composé de trois parties principales :
- Un serveur UDP qui gère la correction des mots
- Un serveur HTTP (Flask) avec interface web et API REST
- Un client en ligne de commande

## Architecture

### Serveur UDP (`udp_server.py`)
Le serveur UDP écoute sur le port 9000 et traite les requêtes
au format `langue:mot:technique`. Il retourne `mot:OK` si le mot
est correct, ou `mot:KO:proposition0:proposition1:...` sinon.

### Serveur HTTP (`http_server.py`)
Le serveur HTTP tourne sur le port 5000 avec Flask. Il propose :
- Une interface web avec formulaire sur la route `/`
- Une API REST sur la route `/spellcheck`
Pour chaque mot, il interroge le serveur UDP.

### Client ligne de commande (`spellcheck_client.py`)
Le client lit le texte depuis l'entrée standard, appelle l'API
HTTP et retourne le texte corrigé sur la sortie standard.

## Algorithmes de correction

### Levenshtein
La distance de Levenshtein calcule le nombre minimal d'opérations
élémentaires (insertion, suppression, substitution) pour transformer
un mot en un autre. Nous l'avons implémentée avec une matrice de
programmation dynamique de taille (m+1) x (n+1) sans bibliothèque
externe.

### Préfixe/Suffixe (prefsuff)
La fonction ps(x, y) = min(pc(x,y), sc(x,y)) / min(|x|, |y|)
où pc est la taille du préfixe commun et sc la taille du suffixe
commun. Un score de 1.0 signifie que les mots sont identiques,
0.0 signifie aucun préfixe ni suffixe commun.

## Détection automatique de la langue
Nous comparons les mots du texte avec chaque dictionnaire disponible.
La langue dont le dictionnaire contient le plus de mots en commun
avec le texte est retenue.

## Installation

### Prérequis
- Python 3.8 ou supérieur
- Flask

### Installation des dépendances
```bash
pip3 install flask requests
```

### Téléchargement des dictionnaires
```bash
cd dictionaries
wget https://raw.githubusercontent.com/chrplr/openlexicon/master/datasets-info/Liste-de-mots-francais-Gutenberg/liste.de.mots.francais.frgut.txt -O french.txt
wget https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt -O english.txt
```

## Utilisation

### Démarrage des serveurs
Ouvrir deux terminaux :

Terminal 1 — Serveur UDP :
```bash
python3 udp_server.py
```

Terminal 2 — Serveur HTTP :
```bash
python3 http_server.py
```

### Interface web
Ouvrir Firefox et aller sur : http://127.0.0.1:5000

### Client ligne de commande
```bash
echo "texte à corriger" | python3 spellcheck_client.py --langue french --technique levenshtein
echo "texte à corriger" | python3 spellcheck_client.py --langue auto --technique prefsuff
```

### API REST
```bash
curl -X POST http://127.0.0.1:5000/spellcheck \
  -H "Content-Type: application/json" \
  -d '{"texte": "je vodrais manjer", "langue": "french", "technique": "levenshtein"}'
```

## Difficultés rencontrées

### Timeout UDP
Le calcul de Levenshtein sur 336 000 mots prend du temps.
Nous avons augmenté le timeout UDP à 60 secondes pour résoudre
ce problème.

### Gestion de la casse
Les mots sont convertis en minuscules avant comparaison pour
ne pas prendre en compte la casse.

### Tokenisation
Nous utilisons une expression régulière pour découper le texte
en mots et non-mots afin de conserver la ponctuation originale.

## Utilisation d'intelligence artificielle
Nous avons utilisé Claude (Anthropic) pour nous aider durant
le développement du projet, notamment pour :
- La structure générale du projet
- Le débogage des problèmes de communication UDP/HTTP
- La rédaction de cette documentation
Conformément aux instructions, nous n'utiliserons pas d'IA
lors de la séance d'examen.

## Documentation individuelle

### Membre 1 : MOUHAMMADOU DIALLO
- Tâches réalisées : Mise en place de la structure du projet
Chargement des dictionnaires en mémoire
Implémentation de la détection automatique de la langue
Implémentation de l'algorithme de Levenshtein
Serveur UDP (fichier udp_server.py)

### Membre 2 : ALHASSANE DIABY
- Tâches réalisées : Implémentation de l'algorithme Préfixe/Suffixe
Serveur HTTP avec Flask (fichier http_server.py)
Interface web avec les templates HTML (index.html, result.html)
Feuille de style CSS (style.css)

### Membre 3 : BAYNA SADY
- Tâches réalisées : API REST /spellcheck
Client en ligne de commande (spellcheck_client.py)
Téléchargement et intégration des dictionnaires
Rédaction de la documentation (README.md)