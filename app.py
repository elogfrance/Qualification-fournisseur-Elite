import streamlit as st
import pandas as pd

# Configuration initiale de la page
st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)

# Initialisation de l’état de session
if "page" not in st.session_state:
    st.session_state.page = "home"

if "qualifications" not in st.session_state:
    st.session_state.qualifications = []

# --- FONCTIONS ---

def afficher_dashboard_fournisseurs():
    st.title("📊 Dashboard des fournisseurs")

    fichier = st.file_uploader("📁 Importer le fichier Excel de suivi des délais", type=["xlsx"])

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
            df["Statut qualification"] = "⏳ À traiter"

            st.session_state.fournisseurs_df = df.copy()
            st.success("✅ Liste de fournisseurs enregistrée dans l’application.")

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

                if st.button("📝 Ouvrir la grille de qualification", key=f"qualif_{index}"):
                    st.session_state.fournisseur_en_cours = row["Fournisseur"]
                    st.session_state.page = "qualification"
                    st.rerun()
    else:
        st.info("📥 Veuillez importer un fichier Excel pour commencer.")


def afficher_fiche_qualification():
    st.title("📋 Fiche de qualification fournisseur")

    fournisseur = st.session_state.get("fournisseur_en_cours", None)

    if fournisseur is None:
        st.warning("Aucun fournisseur sélectionné.")
        return

    st.subheader(f"🔎 Qualification : {fournisseur}")

    # Formulaire de qualification
    contact = st.text_input("👤 Contact principal")
    pays = st.text_input("🌍 Pays")
    stock_identifiable = st.selectbox("📦 Stock réel identifiable ?", ["Oui", "Non"])
    xdock_present = st.selectbox("🔁 Présence de xdock ?", ["Oui", "Non"])
    delai_stock = st.number_input("⏱️ Délai annoncé (stock)", min_value=0)
    delai_xdock = st.number_input("⏱️ Délai annoncé (xdock)", min_value=0)
    processus_commande = st.selectbox("📋 Processus de commande clair ?", ["Oui", "Partiel", "Non"])
    transport = st.selectbox("🚚 Qui gère le transport ?", ["MKP", "Fournisseur"])
    tracking = st.selectbox("📦 Tracking fourni ?", ["Oui", "Non"])
    poids_volume = st.selectbox("📏 Poids/volume communiqués ?", ["Oui", "Non"])
    statut_final = st.selectbox("📌 Statut final", ["✅", "⚠️", "❌"])
    commentaire = st.text_area("📝 Commentaire")

    if st.button("💾 Enregistrer la qualification"):
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
            fiche for fiche in st.session_state.qualifications
            if fiche["Fournisseur"] != fournisseur
        ]
        st.session_state.qualifications.append(nouvelle_fiche)
        st.success("✅ Fiche enregistrée avec succès !")

    if st.button("⬅️ Retour au dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


# --- ROUTEUR PRINCIPAL ---

if st.session_state.page == "home":
    st.image("assets/logo_marketparts.png", width=200)
    st.title("Projet : Qualification Fournisseur Express")

    st.markdown("""
    Bienvenue dans l’outil de qualification des fournisseurs MKP.

    **Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables sur leurs stocks et processus logistiques.

    Chaque qualification prend moins de 10 minutes.
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Dashboard fournisseurs"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("📘 Aide & méthode"):
            st.info("👉 À venir : guide d'utilisation et critères de qualification.")

elif st.session_state.page == "dashboard":
    afficher_dashboard_fournisseurs()

elif st.session_state.page == "qualification":
    afficher_fiche_qualification()
