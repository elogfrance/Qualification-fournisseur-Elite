import streamlit as st
import pandas as pd
import json
import os

# 📍 Chemin du fichier de sauvegarde
JSON_PATH = "data/qualifications.json"

# 🧠 Fonction : charger les qualifications depuis le fichier JSON
def charger_qualifications():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            return json.load(f)
    return []

# 💾 Fonction : sauvegarder les qualifications dans le fichier JSON
def sauvegarder_qualifications(data):
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

# 🔄 Fonction de nettoyage de nom de fournisseur
def clean(nom):
    return str(nom).strip().lower()

# 🧠 Initialisation de session_state au démarrage de l'app
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()

if "page" not in st.session_state:
    st.session_state.page = "home"

if "fournisseur_en_cours" not in st.session_state:
    st.session_state.fournisseur_en_cours = None

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

def afficher_dashboard_fournisseurs():
    st.title("\U0001F4CA Dashboard des fournisseurs")
    fichier = st.file_uploader("\U0001F4C1 Importer le fichier Excel de suivi des délais", type=["xlsx"])

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
                    return "\U0001F7E2 Faible"
                elif delai <= 7:
                    return "\U0001F7E0 Moyen"
                else:
                    return "\U0001F534 Urgent"

            df["Niveau d'urgence"] = df["Délai moyen (jours)"].apply(urgence)

            def statut_depuis_qualifications(nom_frs):
                for fiche in st.session_state.qualifications:
                    if clean(fiche["Fournisseur"]) == clean(nom_frs):
                        return fiche.get("Statut final", "")
                return "\u23F3 À traiter"

            df["Statut qualification"] = df["Fournisseur"].apply(statut_depuis_qualifications)

            st.session_state.fournisseurs_df = df.copy()
            st.success("\u2705 Liste de fournisseurs enregistrée dans l’application.")

        except Exception as e:
            st.error(f"Erreur lors de l’import du fichier : {e}")

    if "fournisseurs_df" in st.session_state:
        df = st.session_state.fournisseurs_df
        st.markdown("### Liste des fournisseurs à qualifier")

        for index, row in df.iterrows():
            with st.expander(f"➡️ {row['Fournisseur']}"):
                col1, col2, col3 = st.columns([2, 2, 2])
                col1.metric("\U0001F4E6 Commandes", row["Nb Commandes"])
                col2.metric("⏱️ Délai moyen", f"{row['Délai moyen (jours)']} j")
                col3.metric("\U0001F6A8 Urgence", row["Niveau d'urgence"])

                st.write("\U0001F5C2️ **Statut actuel** :", row["Statut qualification"])

                if st.button("\U0001F4DD Ouvrir la grille de qualification", key=f"qualif_{index}"):
                    st.session_state.fournisseur_en_cours = row["Fournisseur"]
                    st.session_state.page = "qualification"
                    st.rerun()
    else:
        st.info("\U0001F4E5 Veuillez importer un fichier Excel pour commencer.")

def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours", None)
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    fiche_existante = next((fiche for fiche in st.session_state.qualifications if clean(fiche["Fournisseur"]) == clean(fournisseur)), None)

    st.title(f"\U0001F4DD Qualification : {fournisseur}")

    contact = st.text_input("\U0001F464 Contact principal", value=fiche_existante.get("Contact") if fiche_existante else "")
    pays = st.text_input("\U0001F30D Pays", value=fiche_existante.get("Pays") if fiche_existante else "")
    stock_identifiable = st.selectbox("\U0001F4E6 Stock réel identifiable ?", ["Oui", "Non"], index=["Oui", "Non"].index(fiche_existante.get("Stock réel", "Oui")) if fiche_existante else 0)
    xdock_present = st.selectbox("\U0001F501 Présence de xdock ?", ["Oui", "Non"], index=["Oui", "Non"].index(fiche_existante.get("Xdock", "Non")) if fiche_existante else 0)
    delai_stock = st.number_input("⏱️ Délai annoncé (stock)", min_value=0, value=fiche_existante.get("Délai stock", 0) if fiche_existante else 0)
    delai_xdock = st.number_input("⏱️ Délai annoncé (xdock)", min_value=0, value=fiche_existante.get("Délai xdock", 0) if fiche_existante else 0)
    processus_commande = st.selectbox("📋 Processus de commande clair ?", ["Oui", "Partiel", "Non"], index=["Oui", "Partiel", "Non"].index(fiche_existante.get("Processus commande", "Oui")) if fiche_existante else 0)
    transport = st.selectbox("\U0001F69A Qui gère le transport ?", ["MKP", "Fournisseur"], index=["MKP", "Fournisseur"].index(fiche_existante.get("Transport", "MKP")) if fiche_existante else 0)
    tracking = st.selectbox("\U0001F4E6 Tracking fourni ?", ["Oui", "Non"], index=["Oui", "Non"].index(fiche_existante.get("Tracking", "Oui")) if fiche_existante else 0)
    poids_volume = st.selectbox("\U0001F4CF Poids/volume communiqués ?", ["Oui", "Non"], index=["Oui", "Non"].index(fiche_existante.get("Poids/volume", "Oui")) if fiche_existante else 0)
    statut_final = st.selectbox("\U0001F4CC Statut final", ["✅", "⚠️", "❌"], index=["✅", "⚠️", "❌"].index(fiche_existante.get("Statut final", "✅")) if fiche_existante else 0)
    commentaire = st.text_area("\U0001F4DD Commentaire", value=fiche_existante.get("Commentaire", "") if fiche_existante else "")

    if st.button("💾 Enregistrer"):
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

        st.session_state.qualifications = [
            f for f in st.session_state.qualifications if clean(f["Fournisseur"]) != clean(fournisseur)
        ]

        st.session_state.qualifications.append(nouvelle_fiche)
        sauvegarder_qualifications(st.session_state.qualifications)

        st.success("✅ Fiche enregistrée.")
        st.session_state.page = "fournisseurs"
        st.rerun()

# Navigation
if st.session_state.page == "home":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗂️ Accéder aux fournisseurs"):
            st.session_state.page = "fournisseurs"
            st.rerun()
    with col2:
        if st.button("📘 Aide & méthode"):
            st.info("Méthode en cours de rédaction.")

elif st.session_state.page == "fournisseurs":
    afficher_dashboard_fournisseurs()

elif st.session_state.page == "qualification":
    afficher_fiche_qualification()
