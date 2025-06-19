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

    fiche = next(
        (q for q in st.session_state.qualifications if clean(q["Fournisseur"]) == clean(fournisseur)),
        {"Fournisseur": fournisseur}
    )

    st.title(f"📝 Qualification : {fournisseur}")
    st.markdown("---")

    # (label, type, options)
    champs = [
        ("Contact principal",           "text",    None),
        ("Pays",                        "text",    None),
        ("Condition de paiement",       "select",  ["", "Oui", "Non"]),  # <--- ajouté
        ("Nb de commandes MKP",         "number_static", None),
        ("Délai moyen observé",         "number_static", None),
        ("Stock réel identifiable ?",   "select",  ["Oui","Non"]),
        ("Présence de xdock ?",         "select",  ["Oui","Non"]),
        ("Délai annoncé en stock",      "number",  None),
        ("Délai annoncé xdock",         "number",  None),
        ("Processus de commande clair ?", "select", ["Oui","Partiel","Non"]),
        ("Qui gère le transport ?",       "select", ["MKP","Fournisseur"]),
        ("Tracking fourni ?",             "select", ["Oui","Non"]),
        ("Poids/volume communiqués ?",    "select", ["Oui","Non"]),
        ("✅ Statut final",                "select", ["Eligible","En cours","Non eligible"]),
        ("Commentaire global",            "textarea", None),
    ]

    col_widths = [2, 4, 4]

    with st.form("form_qualif", clear_on_submit=False):
        # En-tête
        h1, h2, h3 = st.columns(col_widths)
        h1.markdown("**Champ**")
        h2.markdown("**Réponse**")
        h3.markdown("**Commentaire**")
        st.markdown("")

        # Lignes
        for label, typ, options in champs:
            val = fiche.get(label, "")
            com = fiche.get(f"{label}__com", "")

            c1, c2, c3 = st.columns(col_widths)
            c1.write(label)
            key = label.replace(" ", "_")

            # réponse
            if typ == "text":
                fiche[label] = c2.text_input("", val, key=key)
            elif typ == "number":
                fiche[label] = c2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                                                min_value=0, key=key)
            elif typ == "number_static":
                c2.number_input("", value=val if isinstance(val, (int, float)) else 0,
                                disabled=True, key=f"{key}_stat")
            elif typ == "select":
                fiche[label] = c2.selectbox("", options, index=options.index(val) if val in options else 0, key=key)
            elif typ == "textarea":
                fiche[label] = c2.text_area("", val, height=80, key=key)

            # commentaire
            fiche[f"{label}__com"] = c3.text_area("", com, height=80, key=f"{key}_com")

        submitted = st.form_submit_button("🔖 Enregistrer la fiche")

    if submitted:
        st.session_state.qualifications = [
            q for q in st.session_state.qualifications
            if clean(q["Fournisseur"]) != clean(fournisseur)
        ]
        st.session_state.qualifications.append(fiche)
        sauvegarder_qualifications(st.session_state.qualifications)
        st.success("✅ Fiche enregistrée !")
        st.session_state.page = "fournisseurs"
        st.experimental_rerun()


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
