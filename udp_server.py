import socket
import os

def charger_dictionnaires(repertoire="dictionaries"):
    """Charge tous les fichiers .txt du dossier en mémoire."""
    dictionnaires = {}
    for nom_fichier in os.listdir(repertoire):
        if nom_fichier.endswith(".txt"):
            langue = nom_fichier[:-4]
            chemin = os.path.join(repertoire, nom_fichier)
            with open(chemin, "r", encoding="utf-8") as f:
                mots = set(ligne.strip().lower() for ligne in f if ligne.strip())
            dictionnaires[langue] = mots
            print(f"Dictionnaire '{langue}' chargé : {len(mots)} mots.")
    return dictionnaires

def detecter_langue(texte, dictionnaires):
    """Retourne la langue dont le dictionnaire partage le plus de mots avec le texte."""
    mots = set(texte.lower().split())
    meilleure_langue = None
    meilleur_score = -1
    for langue, ensemble_mots in dictionnaires.items():
        mots_communs = len(mots & ensemble_mots)
        if mots_communs > meilleur_score:
            meilleur_score = mots_communs
            meilleure_langue = langue
    return meilleure_langue

def levenshtein(chaine1, chaine2):
    """Calcule la distance d'édition entre deux chaînes sans bibliothèque externe."""
    longueur1, longueur2 = len(chaine1), len(chaine2)
    matrice = [[0] * (longueur2 + 1) for _ in range(longueur1 + 1)]
    for i in range(longueur1 + 1):
        matrice[i][0] = i
    for j in range(longueur2 + 1):
        matrice[0][j] = j
    for i in range(1, longueur1 + 1):
        for j in range(1, longueur2 + 1):
            if chaine1[i-1] == chaine2[j-1]:
                matrice[i][j] = matrice[i-1][j-1]
            else:
                matrice[i][j] = 1 + min(
                    matrice[i-1][j],    # suppression
                    matrice[i][j-1],    # insertion
                    matrice[i-1][j-1]   # substitution
                )
    return matrice[longueur1][longueur2]

def longueur_prefixe_commun(chaine1, chaine2):
    """Retourne la longueur du préfixe commun entre deux chaînes."""
    compteur = 0
    for a, b in zip(chaine1, chaine2):
        if a == b:
            compteur += 1
        else:
            break
    return compteur

def longueur_suffixe_commun(chaine1, chaine2):
    """Retourne la longueur du suffixe commun entre deux chaînes."""
    return longueur_prefixe_commun(chaine1[::-1], chaine2[::-1])

def score_prefsuff(mot, candidat):
    """
    Formule exacte du sujet :
    ps(x, y) = min(pc(x,y), sc(x,y)) / min(|x|, |y|)
    - pc = taille du préfixe commun
    - sc = taille du suffixe commun
    - |x| et |y| = tailles des mots
    Score entre 0.0 et 1.0. Deux mots identiques = 1.0
    """
    if mot == candidat:
        return 1.0
    if len(mot) == 0 or len(candidat) == 0:
        return 0.0
    prefixe = longueur_prefixe_commun(mot, candidat)
    suffixe = longueur_suffixe_commun(mot, candidat)
    return min(prefixe, suffixe) / min(len(mot), len(candidat))

NOMBRE_MAX_PROPOSITIONS = 5  # paramétrable

def obtenir_propositions(mot, dictionnaire, technique):
    """Retourne une liste triée de propositions pour un mot inconnu."""
    mot = mot.lower()
    if technique == "levenshtein":
        resultats = [(levenshtein(mot, m), m) for m in dictionnaire if m != mot]
        resultats.sort(key=lambda x: (x[0], x[1]))
    elif technique == "prefsuff":
        resultats = [(-score_prefsuff(mot, m), m) for m in dictionnaire if m != mot]
        resultats.sort(key=lambda x: x[0])
    else:
        return []
    return [m for _, m in resultats[:NOMBRE_MAX_PROPOSITIONS]]

def traiter_requete(donnees, dictionnaires):
    """
    Format d'entrée  : langue:mot:technique
    Format de sortie : mot:OK
                  ou : mot:KO:proposition0:proposition1:...
    """
    try:
        parties = donnees.strip().split(":")
        if len(parties) != 3:
            return "ERREUR:format invalide (attendu langue:mot:technique)"

        langue, mot, technique = parties
        langue = langue.lower()
        mot_minuscule = mot.lower()

        if langue not in dictionnaires:
            return f"ERREUR:langue inconnue '{langue}'"

        dictionnaire = dictionnaires[langue]

        if mot_minuscule in dictionnaire:
            return f"{mot}:OK"
        else:
            propositions = obtenir_propositions(mot_minuscule, dictionnaire, technique)
            return f"{mot}:KO:" + ":".join(propositions)

    except Exception as erreur:
        return f"ERREUR:{str(erreur)}"

def demarrer_serveur(hote="0.0.0.0", port=9000):
    """Démarre le serveur UDP et attend les requêtes."""
    dictionnaires = charger_dictionnaires()

    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.bind((hote, port))
    print(f"Serveur UDP démarré sur {hote}:{port}")
    print("En attente de requêtes...")

    while True:
        donnees, adresse = socket_udp.recvfrom(4096)
        message = donnees.decode("utf-8")
        print(f"Requête reçue de {adresse} : {message}")

        reponse = traiter_requete(message, dictionnaires)
        socket_udp.sendto(reponse.encode("utf-8"), adresse)
        print(f"Réponse envoyée : {reponse}")

if __name__ == "__main__":
    demarrer_serveur()