import streamlit as st
import pandas as pd
import json
import os
import shutil
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 📁 Définitions des chemins
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
QUAL_JSON_PATH       = DATA_DIR / "qualifications.json"
FOURN_JSON_PATH      = DATA_DIR / "fournisseurs_data_current.json"
OLD_FOURN_JSON_PATH  = DATA_DIR / "fournisseurs_data.json"

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ Fonctions de chargement / sauvegarde
# ─────────────────────────────────────────────────────────────────────────────
def charger_qualifications():
    if QUAL_JSON_PATH.exists():
        with open(QUAL_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_qualifications(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(QUAL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def charger_fournisseurs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FOURN_JSON_PATH.exists() and OLD_FOURN_JSON_PATH.exists():
        shutil.copy(OLD_FOURN_JSON_PATH, FOURN_JSON_PATH)
    if FOURN_JSON_PATH.exists():
        return pd.read_json(FOURN_JSON_PATH)
    return pd.DataFrame()

def sauvegarder_fournisseurs(df: pd.DataFrame):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", force_ascii=False, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# 🔨 Initialisation du session_state
# ─────────────────────────────────────────────────────────────────────────────
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()
st.session_state.fournisseurs_df = charger_fournisseurs()

# ─────────────────────────────────────────────────────────────────────────────
# 🖥️ Configuration générale de l’app
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)
st.image("assets/logo_marketparts.png", width=200)
st.title("Projet : Qualification Fournisseur Express")
st.markdown("""
Bienvenue dans l’outil de qualification des fournisseurs MKP.

**Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement,  
et à communiquer des données fiables sur leurs stocks et processus logistiques.

Chaque qualification prend moins de 10 minutes.
""")

if "page" not in st.session_state:
    st.session_state.page = "home"

# ─────────────────────────────────────────────────────────────────────────────
# 🧹 Fonction utilitaire pour normaliser les noms
# ─────────────────────────────────────────────────────────────────────────────
def clean(text):
    return str(text).strip().lower()

# ─────────────────────────────────────────────────────────────────────────────
# 📊 Fonction : tableau de bord des fournisseurs
# ─────────────────────────────────────────────────────────────────────────────
def afficher_dashboard_fournisseurs():
    st.title("📊 Tableau des fournisseurs à qualifier")

    # Import du fichier Excel
    fichier = st.file_uploader("📁 Importer le fichier des commandes", type=["xlsx"])
    if fichier:
        try:
            df = pd.read_excel(fichier)
            df = df.rename(columns={
                "Supplier name":                  "Fournisseur",
                "Date ARC fournisseur reçu":      "Date ARC",
                "Date ready for pickup":          "Date Ready"
            })
            df["Date ARC"]   = pd.to_datetime(df["Date ARC"], errors="coerce")
            df["Date Ready"] = pd.to_datetime(df["Date Ready"], errors="coerce")
            df = df.dropna(subset=["Fournisseur", "Date ARC", "Date Ready"])
            df["Délai (jours)"] = (df["Date Ready"] - df["Date ARC"]).dt.days
            df["Délai (jours)"] = pd.to_numeric(df["Délai (jours)"], errors="coerce")

            result = (
                df.groupby("Fournisseur")
                  .agg(
                    Nombre_commandes=("Fournisseur", "count"),
                    Délai_moyen=("Délai (jours)", lambda x: round(x.mean(skipna=True),1))
                  )
                  .reset_index()
                  .sort_values("Nombre_commandes", ascending=False)
            )

            sauvegarder_fournisseurs(result)
            st.session_state.fournisseurs_df = result
            st.success("✅ Données importées et sauvegardées.")
        except Exception as e:
            st.error(f"Erreur pendant le traitement du fichier : {e}")

    # Affichage de la liste en mémoire
    if not st.session_state.fournisseurs_df.empty:
        st.markdown("### Données fournisseurs en mémoire")

        for idx, row in st.session_state.fournisseurs_df.iterrows():
            fournisseur    = row["Fournisseur"]
            nb_commandes   = int(row["Nombre_commandes"])
            delai_moyen    = row["Délai_moyen"]

            # Nombre de qualifications déjà saisies pour ce fournisseur
            nb_traitements = sum(
                1 for q in st.session_state.qualifications
                if clean(q.get("Fournisseur")) == clean(fournisseur)
            )

            col1, col2, col3 = st.columns([4, 2, 2])
            col1.markdown(
                f"**{fournisseur}**  \n"
                f"• Commandes : {nb_commandes}  \n"
                f"• Traitements : {nb_traitements}"
            )
            col2.metric("⏱️ Délai moyen (j)", f"{delai_moyen}")
            if col3.button("📝 Qualifier", key=f"qualif_{idx}"):
                st.session_state.fournisseur_en_cours = fournisseur
                st.session_state.page = "qualification"
                st.rerun()
    else:
        st.info("📥 Veuillez importer un fichier pour voir le tableau.")

# ─────────────────────────────────────────────────────────────────────────────
# 📝 Fonction : formulaire de qualification
# ─────────────────────────────────────────────────────────────────────────────
def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    # Récupère la fiche existante ou initialise-en une nouvelle
    fiche = next(
        (q for q in st.session_state.qualifications if clean(q.get("Fournisseur")) == clean(fournisseur)),
        {"Fournisseur": fournisseur}
    )
    st.title(f"📝 Qualification : {fournisseur}")

    # Configuration des champs
    champs = [
        {"label": "Fournisseur",                   "type": "text_static"},
        {"label": "Contact principal",             "type": "text"},
        {"label": "Pays",                          "type": "text"},
        {"label": "Nb de commandes MKP",           "type": "number_static"},
        {"label": "Délai moyen observé",           "type": "number_static"},
        {"label": "Stock réel identifiable ?",     "type": "select", "options": ["Oui", "Non"]},
        {"label": "Présence de xdock ?",           "type": "select", "options": ["Oui", "Non"]},
        {"label": "Délai annoncé en stock",        "type": "number"},
        {"label": "Délai annoncé xdock",           "type": "number"},
        {"label": "Processus de commande clair ?", "type": "select", "options": ["Oui", "Partiel", "Non"]},
        {"label": "Qui gère le transport ?",       "type": "select", "options": ["MKP", "Fournisseur"]},
        {"label": "Tracking fourni ?",             "type": "select", "options": ["Oui", "Non"]},
        {"label": "Poids/volume communiqués ?",    "type": "select", "options": ["Oui", "Non"]},
        {"label": "✅ Statut final",                "type": "select", "options": ["Eligible", "En cours", "Non eligible"]},
        {"label": "Commentaire global",            "type": "textarea"}
    ]

    # Affichage en trois colonnes
    for champ in champs:
        col1, col2, col3 = st.columns([3, 3, 4])
        label = champ["label"]
        col1.markdown(f"**{label}**")

        # Clés et valeurs antérieures
        key = label.replace(" ", "_")
        val = fiche.get(label, "")
        com = fiche.get(f"{label}__com", "")

        # Widget adapté
        if champ["type"] == "text_static":
            col2.text_input("", value=val, disabled=True, key=f"{key}_stat")
        elif champ["type"] == "text":
            fiche[label] = col2.text_input("", value=val, key=key)
        elif champ["type"] == "number_static":
            col2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                              disabled=True, key=f"{key}_stat")
        elif champ["type"] == "number":
            fiche[label] = col2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                                             min_value=0, key=key)
        elif champ["type"] == "select":
            options = champ["options"]
            idx_opt = options.index(val) if val in options else 0
            fiche[label] = col2.selectbox("", options, index=idx_opt, key=key)
        elif champ["type"] == "textarea":
            fiche[label] = col2.text_area("", value=val, key=key)

        # Commentaire libre
        fiche[f"{label}__com"] = col3.text_area("", value=com, key=f"{key}_com", height=80)

    # Bouton d’enregistrement
    if st.button("🔖 Enregistrer la fiche"):
        # On remplace l’ancienne fiche par la nouvelle
        st.session_state.qualifications = [
            q for q in st.session_state.qualifications
            if clean(q.get("Fournisseur")) != clean(fournisseur)
        ]
        st.session_state.qualifications.append(fiche)
        sauvegarder_qualifications(st.session_state.qualifications)
        st.success("✅ Fiche enregistrée !")
        st.session_state.page = "fournisseurs"
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 🔀 Navigation principale selon la page
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Accéder aux fournisseurs"):
            st.session_state.page = "fournisseurs"
            st.rerun()
    with col2:
        if st.button("📘 Aide & méthode"):
            st.info("Méthode en cours de rédaction.")
elif st.session_state.page == "fournisseurs":
    afficher_dashboard_fournisseurs()
elif st.session_state.page == "qualification":
    afficher_fiche_qualification()

