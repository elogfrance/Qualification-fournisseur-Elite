import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Qualification Fournisseur Express",
    page_icon="📦",
    layout="centered"
)

# Logo (à adapter selon le nom du fichier)
# st.image("logo_mkp.png", width=200)
st.image("assets/logo_mkp.png", width=200)


# Titre principal
st.title("Projet : Qualification Fournisseur Express")

# Introduction
st.markdown("""
Bienvenue dans l’outil de qualification des fournisseurs MKP.

**Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables sur leurs stocks et processus logistiques.

Chaque qualification prend moins de 10 minutes.

""")

# Boutons de navigation (stockage état)
if "page" not in st.session_state:
    st.session_state.page = "home"

col1, col2 = st.columns(2)
with col1:
    if st.button("🗂️ Accéder aux fournisseurs"):
        st.session_state.page = "fournisseurs"
        st.experimental_rerun()

with col2:
    if st.button("📘 Aide & méthode"):
        st.session_state.page = "aide"
        st.experimental_rerun()
