from flask import Flask, request, render_template, jsonify
import socket
import re
import os

application = Flask(__name__)

HOTE_UDP = "127.0.0.1"
PORT_UDP = 9000

def obtenir_langues_disponibles():
    """Retourne la liste des langues disponibles selon les dictionnaires présents."""
    langues = []
    if os.path.exists("dictionaries"):
        for fichier in os.listdir("dictionaries"):
            if fichier.endswith(".txt"):
                langues.append(fichier[:-4])
    return sorted(langues)

def appeler_serveur_udp(langue, mot, technique):
    """Envoie une requête au serveur UDP et retourne la réponse sous forme de liste."""
    message = f"{langue}:{mot}:{technique}"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(60)
    try:
        sock.sendto(message.encode("utf-8"), (HOTE_UDP, PORT_UDP))
        donnees, _ = sock.recvfrom(65535)
        reponse = donnees.decode("utf-8")
        parties = reponse.split(":")
        return parties
    except socket.timeout:
        print(f"Timeout pour le mot : {mot}")
        return [mot, "OK"]
    finally:
        sock.close()

def detecter_langue_automatique(mots, technique):
    """Essaie chaque langue et retourne celle avec le plus de mots reconnus."""
    langues = obtenir_langues_disponibles()
    scores = {langue: 0 for langue in langues}
    for mot in mots:
        for langue in langues:
            resultat = appeler_serveur_udp(langue, mot, technique)
            if len(resultat) >= 2 and resultat[1] == "OK":
                scores[langue] += 1
    return max(scores, key=scores.get)

def tokeniser(texte):
    """Découpe le texte en tokens (mot ou non-mot)."""
    morceaux = re.split(r'(\W+)', texte)
    resultat = []
    for morceau in morceaux:
        if morceau:
            est_un_mot = bool(re.match(r'\w+', morceau))
            resultat.append((morceau, est_un_mot))
    return resultat

@application.route("/", methods=["GET"])
def accueil():
    langues = obtenir_langues_disponibles()
    return render_template("index.html", langues=langues)

@application.route("/corriger", methods=["POST"])
def corriger():
    texte = request.form.get("texte", "")
    langue = request.form.get("langue", "auto")
    technique = request.form.get("technique", "levenshtein")

    tokens = tokeniser(texte)
    mots = [t for t, est_mot in tokens if est_mot]

    if langue == "auto":
        langue = detecter_langue_automatique(mots, technique)

    resultats = []
    for token, est_mot in tokens:
        if est_mot:
            reponse = appeler_serveur_udp(langue, token, technique)
            if len(reponse) >= 2 and reponse[1] == "OK":
                resultats.append((token, True, "ok", []))
            else:
                propositions = reponse[2:] if len(reponse) > 2 else []
                resultats.append((token, True, "ko", propositions))
        else:
            resultats.append((token, False, None, []))

    return render_template("result.html", resultats=resultats, langue=langue, technique=technique)

@application.route("/spellcheck", methods=["POST"])
def api_correction():
    """
    Corps JSON : { "texte": "...", "langue": "french", "technique": "levenshtein" }
    Réponse JSON : { "langue": "french", "erreurs": [...] }
    """
    corps = request.get_json()
    if not corps:
        return jsonify({"erreur": "corps JSON attendu"}), 400

    texte = corps.get("texte", "")
    langue = corps.get("langue", "auto")
    technique = corps.get("technique", "levenshtein")

    tokens = tokeniser(texte)
    mots = [t for t, est_mot in tokens if est_mot]

    if langue == "auto":
        langue = detecter_langue_automatique(mots, technique)

    erreurs = []
    position = 0
    for token, est_mot in tokens:
        if est_mot:
            reponse = appeler_serveur_udp(langue, token, technique)
            print(f"DEBUG reponse pour '{token}': {reponse}")
            statut = reponse[1] if len(reponse) >= 2 else "ERREUR"
            if statut != "OK":
                propositions = reponse[2:] if len(reponse) > 2 else []
                # Nettoyer les propositions vides
                propositions = [p for p in propositions if p.strip()]
                erreurs.append({
                    "position": position,
                    "mot": token,
                    "propositions": propositions
                })
            position += 1

    return jsonify({"langue": langue, "erreurs": erreurs})

if __name__ == "__main__":
    application.run(debug=True, port=5000)