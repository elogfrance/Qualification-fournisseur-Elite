import streamlit as st
import pandas as pd
import json
import os
import shutil

BASE_DIR = os.path.dirname(__file__)
QUAL_JSON_PATH = os.path.join(BASE_DIR, "data", "qualifications.json")
FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data_current.json")
OLD_FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data.json")

def charger_qualifications():
    if os.path.exists(QUAL_JSON_PATH):
        with open(QUAL_JSON_PATH, "r") as f:
            return json.load(f)
    return []

def sauvegarder_qualifications(data):
    os.makedirs(os.path.dirname(QUAL_JSON_PATH), exist_ok=True)
    with open(QUAL_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

def charger_fournisseurs():
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    if not os.path.exists(FOURN_JSON_PATH) and os.path.exists(OLD_FOURN_JSON_PATH):
        shutil.copy(OLD_FOURN_JSON_PATH, FOURN_JSON_PATH)
    if os.path.exists(FOURN_JSON_PATH):
        return pd.read_json(FOURN_JSON_PATH)
    return None

def sauvegarder_fournisseurs(df: pd.DataFrame):
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", force_ascii=False, indent=2)

if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()

if "fournisseurs_df" not in st.session_state:
    df_init = charger_fournisseurs()
    if df_init is not None:
        st.session_state.fournisseurs_df = df_init

st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)

st.image("assets/logo_marketparts.png", width=200)

st.title("Projet : Qualification Fournisseur Express")

st.markdown("""
Bienvenue dans l’outil de qualification des fournisseurs MKP.

**Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables sur leurs stocks et processus logistiques.

Chaque qualification prend moins de 10 minutes.
""")

if "page" not in st.session_state:
    st.session_state.page = "home"

def clean(nom):
    return str(nom).strip().lower()

def afficher_dashboard_fournisseurs():
    st.title("📊 Tableau des fournisseurs à qualifier")
    fichier = st.file_uploader("📁 Importer le fichier des commandes", type=["xlsx"])

    if fichier:
        try:
            df = pd.read_excel(fichier)
            df = df.rename(columns={
                "Supplier name": "Fournisseur",
                "Date ARC fournisseur reçu": "Date ARC",
                "Date ready for pickup": "Date Ready"
            })

            df["Date ARC"] = pd.to_datetime(df["Date ARC"], errors="coerce")
            df["Date Ready"] = pd.to_datetime(df["Date Ready"], errors="coerce")
            df = df.dropna(subset=["Date ARC", "Date Ready", "Fournisseur"])

            df["Délai (jours)"] = (df["Date Ready"] - df["Date ARC"]).dt.days
            df["Délai (jours)"] = pd.to_numeric(df["Délai (jours)"], errors="coerce")

            result = df.groupby("Fournisseur").agg(
                Nombre_commandes=("Fournisseur", "count"),
                Délai_moyen=("Délai (jours)", lambda x: round(x.dropna().mean(), 1))
            ).reset_index()

            result = result.sort_values(by="Nombre_commandes", ascending=False)

            st.session_state.fournisseurs_df = result
            sauvegarder_fournisseurs(result)

            st.success("✅ Données traitées avec succès.")
            st.dataframe(result)

        except Exception as e:
            st.error(f"Erreur pendant le traitement du fichier : {e}")
    else:
        st.info("📥 Veuillez importer un fichier contenant les colonnes : Supplier name, Date ARC fournisseur reçu, Date ready for pickup.")

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
