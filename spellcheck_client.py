#!/usr/bin/env python3
"""
Client en ligne de commande pour le correcteur orthographique.

Utilisation :
  echo "texte à corriger" | python3 spellcheck_client.py --langue french --technique levenshtein
  echo "texte à corriger" | python3 spellcheck_client.py --langue auto --technique prefsuff
"""

import argparse
import sys
import requests
import re

def main():
    # ─────────────────────────────────────
    # LECTURE DES ARGUMENTS
    # ─────────────────────────────────────
    analyseur = argparse.ArgumentParser(
        description="Client en ligne de commande pour le correcteur orthographique"
    )
    analyseur.add_argument(
        "--langue",
        default="auto",
        help="Langue du texte (ex: french, english, auto pour détection automatique)"
    )
    analyseur.add_argument(
        "--technique",
        default="levenshtein",
        choices=["levenshtein", "prefsuff"],
        help="Technique de correction à utiliser"
    )
    analyseur.add_argument(
        "--url",
        default="http://127.0.0.1:5000/spellcheck",
        help="URL de l'API de correction"
    )
    arguments = analyseur.parse_args()

    # ─────────────────────────────────────
    # LECTURE DU TEXTE DEPUIS L'ENTRÉE STANDARD
    # ─────────────────────────────────────
    texte = sys.stdin.read()

    if not texte.strip():
        print("Erreur : aucun texte fourni sur l'entrée standard.", file=sys.stderr)
        sys.exit(1)

    # ─────────────────────────────────────
    # APPEL À L'API HTTP
    # ─────────────────────────────────────
    donnees = {
        "texte": texte,
        "langue": arguments.langue,
        "technique": arguments.technique
    }

    try:
        reponse = requests.post(arguments.url, json=donnees)
        reponse.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Erreur : impossible de se connecter au serveur HTTP.", file=sys.stderr)
        print("Vérifiez que http_server.py est bien lancé.", file=sys.stderr)
        sys.exit(1)

    resultat = reponse.json()

    if "erreur" in resultat:
        print(f"Erreur reçue : {resultat['erreur']}", file=sys.stderr)
        sys.exit(1)

    # ─────────────────────────────────────
    # CONSTRUCTION DU TEXTE CORRIGÉ
    # ─────────────────────────────────────
    # On crée un dictionnaire : position -> première proposition
    corrections = {}
    for erreur in resultat["erreurs"]:
        if erreur["propositions"]:
            corrections[erreur["position"]] = erreur["propositions"][0]

    # On retokenise le texte pour reconstruire avec les corrections
    morceaux = re.split(r'(\W+)', texte)
    morceaux_corriges = []
    position_mot = 0

    for morceau in morceaux:
        if morceau and re.match(r'\w+', morceau):
            if position_mot in corrections:
                morceaux_corriges.append(corrections[position_mot])
            else:
                morceaux_corriges.append(morceau)
            position_mot += 1
        else:
            morceaux_corriges.append(morceau)

    texte_corrige = "".join(morceaux_corriges)

    # ─────────────────────────────────────
    # AFFICHAGE DU RÉSULTAT
    # ─────────────────────────────────────
    print(f"Langue détectée : {resultat['langue']}", file=sys.stderr)
    print(texte_corrige)

if __name__ == "__main__":
    main()