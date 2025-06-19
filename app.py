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

    # Récupère ou initialise la fiche
    fiche = next(
        (q for q in st.session_state.qualifications if clean(q["Fournisseur"]) == clean(fournisseur)),
        {"Fournisseur": fournisseur}
    )

    st.title(f"📝 Qualification : {fournisseur}")
    st.markdown("---")

    # Définition des champs
    champs = [
        ("Contact principal",       "text"),
        ("Pays",                    "text"),
        ("Nb de commandes MKP",     "number_static"),
        ("Délai moyen observé",     "number_static"),
        ("Stock réel identifiable ?", "select", ["Oui", "Non"]),
        ("Présence de xdock ?",       "select", ["Oui", "Non"]),
        ("Délai annoncé en stock",    "number"),
        ("Délai annoncé xdock",       "number"),
        ("Processus de commande clair ?", "select", ["Oui", "Partiel", "Non"]),
        ("Qui gère le transport ?",       "select", ["MKP", "Fournisseur"]),
        ("Tracking fourni ?",             "select", ["Oui", "Non"]),
        ("Poids/volume communiqués ?",    "select", ["Oui", "Non"]),
        ("✅ Statut final",                "select", ["Eligible", "En cours", "Non eligible"]),
        ("Commentaire global",            "textarea")
    ]

    with st.form("form_qualification", clear_on_submit=False):
        # En-tête du tableau
        col1, col2, col3 = st.columns([2, 4, 4])
        col1.markdown("**Champ**")
        col2.markdown("**Réponse**")
        col3.markdown("**Commentaire**")
        st.markdown("")  # petit espacement

        # Boucle de création des lignes
        for label, typ, *opts in champs:
            key = label.replace(" ", "_")
            val = fiche.get(label, "")
            com = fiche.get(f"{label}__com", "")

            c1, c2, c3 = st.columns([2,4,4])
            c1.write(label)

            # réponse
            if typ == "text":
                fiche[label] = c2.text_input("", val, key=key)
            elif typ == "number":
                fiche[label] = c2.number_input("", value=val if isinstance(val, (int,float)) else 0, min_value=0, key=key)
            elif typ == "number_static":
                c2.number_input("", value=val if isinstance(val, (int,float)) else 0, disabled=True, key=f"{key}_stat")
            elif typ == "select":
                fiche[label] = c2.selectbox("", options=opts[0], index=opts[0].index(val) if val in opts[0] else 0, key=key)
            elif typ == "textarea":
                fiche[label] = c2.text_area("", val, key=key, height=50)

            # commentaire
            fiche[f"{label}__com"] = c3.text_area("", com, key=f"{key}_com", height=50)

        # bouton submit
        submitted = st.form_submit_button("🔖 Enregistrer la fiche")
        if submitted:
            # remplace l’ancienne fiche
            st.session_state.qualifications = [
                q for q in st.session_state.qualifications
                if clean(q["Fournisseur"]) != clean(fournisseur)
            ]
            st.session_state.qualifications.append(fiche)
            sauvegarder_qualifications(st.session_state.qualifications)
            st.success("✅ Fiche enregistrée !")
            st.session_state.page = "fournisseurs"
            st.experimental_rerun()


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

