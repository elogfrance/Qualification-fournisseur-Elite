import streamlit as st
import pandas as pd
import json
import os

# 📍 Répertoires et chemins ABSOLUS
BASE_DIR = os.path.dirname(__file__)
QUAL_JSON_PATH = os.path.join(BASE_DIR, "data", "qualifications.json")
FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data_current.json")

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

# -- Dashboard fournisseurs --
def afficher_dashboard_fournisseurs():
    st.title("📊 Dashboard des fournisseurs")
    fichier = st.file_uploader(
        "📁 Importer le fichier Excel de suivi des délais", type=["xlsx"]
    )

    if fichier:
        try:
            df = pd.read_excel(fichier, skiprows=2)
            df = df.rename(columns={
                df.columns[0]: "Fournisseur",
                df.columns[1]: "Nb Commandes",
                df.columns[2]: "Délai moyen (jours)"
            })

            def urgence(delai):
                if pd.isna(delai):
                    return ""
                elif delai <= 3:
                    return "🟢 Faible"
                elif delai <= 7:
                    return "🟠 Moyen"
                else:
                    return "🔴 Urgent"

            df["Niveau d'urgence"] = df["Délai moyen (jours)"].apply(urgence)

            def statut_depuis_qualifications(nom_frs):
                for fiche in st.session_state.qualifications:
                    if clean(fiche["Fournisseur"]) == clean(nom_frs):
                        return fiche["Statut final"]
                return "⏳ À traiter"

            df["Statut qualification"] = df["Fournisseur"].apply(statut_depuis_qualifications)

            # Mise à jour de la session et sauvegarde persistante
            st.session_state.fournisseurs_df = df.copy()
            sauvegarder_fournisseurs(st.session_state.fournisseurs_df)
            st.success(
                "✅ Liste enregistrée et sauvegardée sur disco (data/fournisseurs_data_current.json)."
            )
        except Exception as e:
            st.error(f"Erreur lors de l’import du fichier : {e}")

    if "fournisseurs_df" in st.session_state:
        df = st.session_state.fournisseurs_df
        st.markdown("### Liste des fournisseurs à qualifier")
        for index, row in df.iterrows():
            with st.expander(f"➡️ {row['Fournisseur']}"):
                col1, col2, col3 = st.columns([2, 2, 2])
                col1.metric("📦 Commandes", row["Nb Commandes"])
                col2.metric("⏱️ Délai moyen", f"{row['Délai moyen (jours)']} j")
                col3.metric("🚨 Urgence", row["Niveau d'urgence"])

                st.write("🗂️ **Statut actuel** :", row["Statut qualification"])

                if st.button(
                    "📝 Ouvrir la grille de qualification", key=f"qualif_{index}"
                ):
                    st.session_state.fournisseur_en_cours = row["Fournisseur"]
                    st.session_state.page = "qualification"
                    st.rerun()
    else:
        st.info("📥 Veuillez importer un fichier Excel pour commencer.")

# -- Fiche qualification --
def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    fiche_existante = next(
        (f for f in st.session_state.qualifications if clean(f["Fournisseur"]) == clean(fournisseur)),
        None
    )

    st.title(f"📝 Qualification : {fournisseur}")
    contact = st.text_input(
        "👤 Contact principal",
        value=fiche_existante.get("Contact", "") if fiche_existante else ""
    )
    pays = st.text_input(
        "🌍 Pays",
        value=fiche_existante.get("Pays", "") if fiche_existante else ""
    )
    stock_identifiable = st.selectbox(
        "📦 Stock réel identifiable ?", ["Oui", "Non"],
        index=["Oui", "Non"].index(fiche_existante.get("Stock réel", "Oui"))
        if fiche_existante else 0
    )
    xdock_present = st.selectbox(
        "🔁 Présence de xdock ?", ["Oui", "Non"],
        index=["Oui", "Non"].index(fiche_existante.get("Xdock", "Non"))
        if fiche_existante else 0
    )
    delai_stock = st.number_input(
        "⏱️ Délai annoncé (stock)", min_value=0,
        value=fiche_existante.get("Délai stock", 0) if fiche_existante else 0
    )
    delai_xdock = st.number_input(
        "⏱️ Délai annoncé (xdock)", min_value=0,
        value=fiche_existante.get("Délai xdock", 0) if fiche_existante else 0
    )
    processus_commande = st.selectbox(
        "📋 Processus de commande clair ?", ["Oui", "Partiel", "Non"],
        index=["Oui", "Partiel", "Non"].index(fiche_existante.get("Processus commande", "Oui"))
        if fiche_existante else 0
    )
    transport = st.selectbox(
        "🚚 Qui gère le transport ?", ["MKP", "Fournisseur"],
        index=["MKP", "Fournisseur"].index(fiche_existante.get("Transport", "MKP"))
        if fiche_existante else 0
    )
    tracking = st.selectbox(
        "📦 Tracking fourni ?", ["Oui", "Non"],
        index=["Oui", "Non"].index(fiche_existante.get("Tracking", "Non"))
        if fiche_existante else 0
    )
    poids_volume = st.selectbox(
        "📏 Poids/volume communiqués ?", ["Oui", "Non"],
        index=["Oui", "Non"].index(fiche_existante.get("Poids/volume", "Oui"))
        if fiche_existante else 0
    )
    statut_final = st.selectbox(
        "📌 Statut final", ["✅", "⚠️", "❌"],
        index=["✅", "⚠️", "❌"].index(fiche_existante.get("Statut final", "✅"))
        if fiche_existante else 0
    )
    commentaire = st.text_area(
        "📝 Commentaire",
        value=fiche_existante.get("Commentaire", "") if fiche_existante else ""
    )

    if st.button("📂 Enregistrer"):
        nouvelle_fiche = {
            "Fournisseur": fournisseur,
            "Contact": contact,
            "Pays": pays,
            "Stock réel": stock_identifiable,
            "Xdock": xdock_present,
            "Délai stock": delai_stock,
            "Délai xdock": delai_xdock,
            "Processus commande": processus_commande,
            "Transport": transport,
            "Tracking": tracking,
            "Poids/volume": poids_volume,
            "Statut final": statut_final,
            "Commentaire": commentaire
        }

        # Remplacement ou ajout dans la session
        st.session_state.qualifications = [
            f for f in st.session_state.qualifications
            if clean(f["Fournisseur"]) != clean(fournisseur)
        ]
        st.session_state.qualifications.append(nouvelle_fiche)
        sauvegarder_qualifications(st.session_state.qualifications)

        st.success("✅ Données sauvegardées.")
        st.write("📁 Aperçu du fichier qualifications.json :")
        st.json(st.session_state.qualifications)

        st.session_state.page = "fournisseurs"
        st.rerun()

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
