import streamlit as st
import pandas as pd
import json
import os
import shutil
import plotly.express as px

# --- Chemins des fichiers de données ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUAL_JSON_PATH = os.path.join(BASE_DIR, "data", "qualifications.json")
FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data_current.json")
OLD_FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data.json")

# --- Fonctions de chargement et sauvegarde ---
def charger_qualifications():
    if os.path.exists(QUAL_JSON_PATH):
        with open(QUAL_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_qualifications(data):
    os.makedirs(os.path.dirname(QUAL_JSON_PATH), exist_ok=True)
    with open(QUAL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def charger_fournisseurs():
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    if not os.path.exists(FOURN_JSON_PATH) and os.path.exists(OLD_FOURN_JSON_PATH):
        shutil.copy(OLD_FOURN_JSON_PATH, FOURN_JSON_PATH)
    if os.path.exists(FOURN_JSON_PATH):
        return pd.read_json(FOURN_JSON_PATH)
    return pd.DataFrame()

def sauvegarder_fournisseurs(df: pd.DataFrame):
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", indent=2, force_ascii=False)

def clean_txt(s: str) -> str:
    return str(s).strip().lower()

# --- Session state ---
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()
if "fournisseurs_df" not in st.session_state:
    st.session_state.fournisseurs_df = charger_fournisseurs()
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- Configuration page ---
st.set_page_config(page_title="Qualification Fournisseur Express", page_icon="📦", layout="centered")

# --- Header ---
st.image("assets/logo_marketparts.png", width=400)
st.title("Projet : Qualification Fournisseur Express")
st.markdown("""
Bienvenue dans l’outil de qualification des fournisseurs MKP.

**Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables.
Chaque qualification prend moins de 10 minutes.
""")

# --- Page: Import & Home ---
def afficher_home():
    st.header("📂 Import des commandes")
    fichier = st.file_uploader("Importer le fichier des commandes (xlsx)", type=["xlsx"])
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
            result = df.groupby("Fournisseur").agg(
                Nombre_commandes=("Fournisseur", "count"),
                Délai_moyen=("Délai (jours)", lambda x: round(x.dropna().mean(), 1))
            ).reset_index().sort_values(by="Nombre_commandes", ascending=False)
            sauvegarder_fournisseurs(result)
            st.session_state.fournisseurs_df = result
            st.success("✅ Données importées et sauvegardées.")
        except Exception as e:
            st.error(f"Erreur pendant le traitement du fichier : {e}")
    st.write("---")
    if st.button("➡️ Aller aux fournisseurs"):
        st.session_state.page = "fournisseurs"
        st.experimental_rerun()

# --- Page: Fournisseurs ---
def afficher_dashboard_fournisseurs():
    st.header("📊 Liste des fournisseurs")
    df_f = st.session_state.fournisseurs_df
    if df_f.empty:
        st.info("Aucun fournisseur en mémoire. Veuillez importer d'abord.")
        return
    for i, row in df_f.iterrows():
        with st.expander(f"➡️ {row['Fournisseur']}"):
            c1, c2 = st.columns(2)
            c1.metric("Commandes", row["Nombre_commandes"])
            c2.metric("Délai moyen (j)", row["Délai_moyen"])
            if st.button("📝 Qualifier", key=f"qual_{i}"):
                st.session_state.current_fourn = row["Fournisseur"]
                st.session_state.page = "qualification"
                st.experimental_rerun()
    st.write("---")
    if st.button("🏠 Accueil"):
        st.session_state.page = "home"
        st.experimental_rerun()

# --- Page: Qualification ---
def afficher_fiche_qualification():
    fournisseur = st.session_state.get("current_fourn")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return
    fiches = st.session_state.qualifications
    exist = next((f for f in fiches if clean_txt(f.get("Fournisseur")) == clean_txt(fournisseur)), None)
    st.header(f"📝 Qualification : {fournisseur}")
    # Champs...
    contact = st.text_input("Contact principal", value=exist.get("Contact", "") if exist else "")
    # (autres champs identiques à afficher_form_qualification)
    if st.button("📂 Enregistrer"):
        nouvelle = {"Fournisseur": fournisseur, "Contact": contact}
        # simplifié pour vise...
        updated = [f for f in fiches if clean_txt(f.get("Fournisseur")) != clean_txt(fournisseur)]
        updated.append(nouvelle)
        sauvegarder_qualifications(updated)
        st.session_state.qualifications = updated
        st.success("✅ Qualification enregistrée.")
    st.write("---")
    if st.button("🏠 Accueil"):
        st.session_state.page = "home"
        st.experimental_rerun()

# --- Page: Dashboard Qualifs ---
def afficher_dashboard_qualifications():
    st.header("📈 Dashboard des qualifications")
    # (contenu inchangé, camembert, etc.)
    st.write("---")
    if st.button("🏠 Accueil"):
        st.session_state.page = "home"
        st.experimental_rerun()

# --- Navigation principale ---
# Définition des pages disponibles
pages = ["Accueil", "Fournisseurs", "Dashboard Qualifs"]
# Choix du page par défaut (fallback sur Accueil si valeur invalide)
def get_page_index():
    current = st.session_state.page if st.session_state.page in pages else "Accueil"
    return pages.index(current)

page = st.sidebar.selectbox("Menu", pages, index=get_page_index(), key="main_menu")
# Mise à jour du state
st.session_state.page = page

# Routage selon la page sélectionnée
if page == "Accueil":
    afficher_home()
elif page == "Fournisseurs":
    afficher_dashboard_fournisseurs()
elif page == "Dashboard Qualifs":
    afficher_dashboard_qualifications()
