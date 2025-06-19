import streamlit as st
import pandas as pd
import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
    return pd.DataFrame()

def sauvegarder_fournisseurs(df: pd.DataFrame):
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", force_ascii=False, indent=2)

if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()

# ⚠️ Toujours recharger la dernière version des fournisseurs
st.session_state.fournisseurs_df = charger_fournisseurs()

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

            sauvegarder_fournisseurs(result)
            st.session_state.fournisseurs_df = result

            st.success("✅ Données importées et sauvegardées.")
        except Exception as e:
            st.error(f"Erreur pendant le traitement du fichier : {e}")

    if not st.session_state.fournisseurs_df.empty:
        st.markdown("### Données fournisseurs en mémoire")

        for index, row in st.session_state.fournisseurs_df.iterrows():
            with st.expander(f"➡️ {row['Fournisseur']}"):
                col1, col2 = st.columns(2)
                col1.metric("📦 Commandes", row["Nombre_commandes"])
                col2.metric("⏱️ Délai moyen", f"{row['Délai_moyen']} j")

                if st.button("📝 Accéder à la qualification", key=f"btn_qualif_{index}"):
                    st.session_state.fournisseur_en_cours = row["Fournisseur"]
                    st.session_state.page = "qualification"
                    st.rerun()
    else:
        st.info("📥 Veuillez importer un fichier pour voir le tableau.")

def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    # Charge la fiche existante ou initialise-la
    fiche_existante = next(
        (f for f in st.session_state.qualifications
         if clean(f.get("Fournisseur")) == clean(fournisseur)),
        {}
    )
    st.title(f"📝 Qualification : {fournisseur}")

    # Définition des champs selon la mise en page souhaitée
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

    # Affichage en 3 colonnes
    for champ in champs:
        col1, col2, col3 = st.columns([3, 3, 4])
        label = champ["label"]

        # Colonne Champ
        col1.markdown(f"**{label}**")
        val = fiche_existante.get(label, "")
        com = fiche_existante.get(f"{label}__com", "")
        key = label.replace(" ", "_")

        # Colonne Réponse
        if champ["type"] == "text_static":
            col2.text_input("", value=val, disabled=True, key=f"{key}_stat")
        elif champ["type"] == "text":
            fiche_existante[label] = col2.text_input("", value=val, key=key)
        elif champ["type"] == "number_static":
            col2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                              disabled=True, key=f"{key}_stat")
        elif champ["type"] == "number":
            fiche_existante[label] = col2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                                                       key=key)
        elif champ["type"] == "select":
            options = champ["options"]
            idx = options.index(val) if val in options else 0
            fiche_existante[label] = col2.selectbox("", options, index=idx, key=key)
        elif champ["type"] == "textarea":
            fiche_existante[label] = col2.text_area("", value=val, key=key)

        # Colonne Commentaire libre
        fiche_existante[f"{label}__com"] = col3.text_area("", value=com, key=f"{key}_com", height=80)

    # Bouton Enregistrer
    if st.button("🔖 Enregistrer la fiche"):
        st.session_state.qualifications = [
            f for f in st.session_state.qualifications
            if clean(f.get("Fournisseur")) != clean(fournisseur)
        ]
        st.session_state.qualifications.append(fiche_existante)
        sauvegarder_qualifications(st.session_state.qualifications)
        st.success("✅ Fiche enregistrée avec succès !")
        st.session_state.page = "fournisseurs"
        st.rerun()


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
