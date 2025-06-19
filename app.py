import streamlit as st
import pandas as pd
import json
import os
import shutil  # Pour la copie de fichiers

# 📍 Répertoires et chemins ABSOLUS
BASE_DIR = os.path.dirname(__file__)
QUAL_JSON_PATH = os.path.join(BASE_DIR, "data", "qualifications.json")
FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data_current.json")
OLD_FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data.json")  # Ancien chemin pour migration

# 🧠 Charger les qualifications depuis le JSON
def charger_qualifications():
    if os.path.exists(QUAL_JSON_PATH):
        with open(QUAL_JSON_PATH, "r") as f:
            return json.load(f)
    return []

# 💾 Sauvegarder les qualifications dans le JSON
def sauvegarder_qualifications(data):
    os.makedirs(os.path.dirname(QUAL_JSON_PATH), exist_ok=True)
    with open(QUAL_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

# 🧠 Charger les fournisseurs depuis le JSON (dernier import)
def charger_fournisseurs():
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    # Migration si ancien fichier existe
    if not os.path.exists(FOURN_JSON_PATH) and os.path.exists(OLD_FOURN_JSON_PATH):
        shutil.copy(OLD_FOURN_JSON_PATH, FOURN_JSON_PATH)
    if os.path.exists(FOURN_JSON_PATH):
        return pd.read_json(FOURN_JSON_PATH)
    return None

# 💾 Sauvegarder les fournisseurs dans le JSON (écrasement)
def sauvegarder_fournisseurs(df: pd.DataFrame):
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", force_ascii=False, indent=2)

# ⚙️ Session State – qualifications
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()

# ⚙️ Session State – fournisseurs (chargé si existant)
if "fournisseurs_df" not in st.session_state:
    df_init = charger_fournisseurs()
    if df_init is not None:
        st.session_state.fournisseurs_df = df_init

# Configuration de la page
st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)

# Logo
st.image("assets/logo_marketparts.png", width=200)

st.title("Projet : Qualification Fournisseur Express")

st.markdown("""
Bienvenue dans l’outil de qualification des fournisseurs MKP.

**Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables sur leurs stocks et processus logistiques.

Chaque qualification prend moins de 10 minutes.
""")

if "page" not in st.session_state:
    st.session_state.page = "home"

# Routine de nettoyage des noms
def clean(nom):
    return str(nom).strip().lower()

# -- Affichage du Dashboard fournisseurs --
def afficher_dashboard_fournisseurs():
    st.title("📊 Dashboard des fournisseurs")
    fichier = st.file_uploader(
        "📁 Importer le fichier Excel de suivi des délais", type=["xlsx"]
    )

    if fichier:
        try:
            # Lecture et renommage des colonnes
            df = pd.read_excel(fichier, skiprows=2)
            df = df.rename(columns={
                df.columns[0]: "Fournisseur",
                df.columns[1]: "Nb Commandes",
                df.columns[2]: "ARC reçu",
                df.columns[3]: "Ready for pick up"
            })
            # Conversion des dates
            df["ARC reçu"] = pd.to_datetime(df["ARC reçu"], errors='coerce')
            df["Ready for pick up"] = pd.to_datetime(df["Ready for pick up"], errors='coerce')
            # Calcul du délai entre ARC reçu et Ready for pick up (en jours)
            df["Délai ARC->Ready (j)"] = (df["Ready for pick up"] - df["ARC reçu"]).dt.days

            # Agrégation par fournisseur
            df_group = df.groupby("Fournisseur").agg(
                Nb_Commandes=("Nb Commandes", "count"),
                Moyenne_delai_ARC_Ready=("Délai ARC->Ready (j)", lambda x: round(x.mean(), 1))
            ).reset_index()

            # Mise à jour de la session et sauvegarde
            st.session_state.fournisseurs_df = df_group.copy()
            sauvegarder_fournisseurs(st.session_state.fournisseurs_df)
            st.success(
                "✅ Liste agrégée enregistrée et sauvegardée (data/fournisseurs_data_current.json)."
            )
        except Exception as e:
            st.error(f"Erreur lors de l’import du fichier : {e}")

    # Affichage du tableau agrégé
    if "fournisseurs_df" in st.session_state:
        st.markdown("### Synthèse par fournisseur")
        st.dataframe(st.session_state.fournisseurs_df)
    else:
        st.info("📥 Veuillez importer un fichier Excel pour commencer.")

# -- Affichage de la fiche de qualification --
def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    fiche_existante = next(
        (
            f for f in st.session_state.qualifications
            if clean(f.get("Fournisseur")) == clean(fournisseur)
        ),
        None
    )

    st.title(f"📝 Qualification : {fournisseur}")
    # ... reste inchangé ...

# -- Navigation générale --
if st.session_state.page == "home":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂️ Accéder aux fournisseurs"):
            st.session_state.page = "fournisseurs"
            st.rerun()
    with col2:
        if st.button("📘 Aide & méthode"):
            st.info("Méthode en cours de rédaction.")
elif st.session_state.page == "fournisseurs":
    afficher_dashboard_fournisseurs()
elif st.session_state.page == "qualification":
    afficher_fiche_qualification()
