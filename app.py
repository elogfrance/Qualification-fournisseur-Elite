import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)

# --------------------------
# PAGE : Suivi des délais
# --------------------------
def afficher_suivi_delais():
    st.title("📦 Suivi des délais d'expédition")

    fichier = st.file_uploader("📁 Importer le fichier Excel (type ARC → Ready)", type=["xlsx"])

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

            st.success("✅ Données traitées avec succès")
            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur de traitement : {e}")

# --------------------------
# PAGE PRINCIPALE
# --------------------------
def main():
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

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗂️ Accéder aux fournisseurs"):
            st.session_state.page = "fournisseurs"
            st.rerun()

    with col2:
        if st.button("📘 Aide & méthode"):
            st.session_state.page = "aide"
            st.rerun()

    with col3:
        if st.button("📦 Suivi délais réels"):
            st.session_state.page = "delais"
            st.rerun()

    # Navigation
    if st.session_state.page == "home":
        st.info("👈 Sélectionne une section pour commencer.")
    elif st.session_state.page == "fournisseurs":
        st.warning("📌 La section 'fournisseurs' est en cours de développement.")
    elif st.session_state.page == "aide":
        st.info("📘 Une documentation simple sera ajoutée ici.")
    elif st.session_state.page == "delais":
        afficher_suivi_delais()

# Lancement principal
if __name__ == "__main__":
    main()
