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
    """Charge le JSON des qualifications ou retourne une liste vide."""
    if os.path.exists(QUAL_JSON_PATH):
        with open(QUAL_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_qualifications(data):
    """Écrit la liste de qualifications dans le JSON."""
    os.makedirs(os.path.dirname(QUAL_JSON_PATH), exist_ok=True)
    with open(QUAL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def charger_fournisseurs():
    """Charge le JSON des fournisseurs, ou migre l'ancien si nécessaire."""
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    if not os.path.exists(FOURN_JSON_PATH) and os.path.exists(OLD_FOURN_JSON_PATH):
        shutil.copy(OLD_FOURN_JSON_PATH, FOURN_JSON_PATH)
    if os.path.exists(FOURN_JSON_PATH):
        return pd.read_json(FOURN_JSON_PATH)
    return pd.DataFrame()

def sauvegarder_fournisseurs(df: pd.DataFrame):
    """Sauvegarde le DataFrame des fournisseurs en JSON."""
    os.makedirs(os.path.dirname(FOURN_JSON_PATH), exist_ok=True)
    df.to_json(FOURN_JSON_PATH, orient="records", indent=2, force_ascii=False)

def clean_txt(s: str) -> str:
    """Normalise une chaîne pour comparaison insensible."""
    return str(s).strip().lower()

# --- Initialisation du session state ---
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()
if "fournisseurs_df" not in st.session_state:
    st.session_state.fournisseurs_df = charger_fournisseurs()

# --- Configuration de la page ---
st.set_page_config(page_title="Qualification Fournisseur Express", page_icon="📦", layout="centered")

# --- En-tête commun ---
st.image("assets/logo_marketparts.png", width=400)
st.title("Projet : Qualification Fournisseur Express")
st.markdown(
    """
    Bienvenue dans l’outil de qualification des fournisseurs MKP.

    **Objectif :** vérifier la fiabilité des fournisseurs, leur capacité à expédier rapidement, et à communiquer des données fiables sur leurs stocks et processus logistiques.

    Chaque qualification prend moins de 10 minutes.
    """
)

# --- Fonctions d'affichage des pages ---

def afficher_dashboard_fournisseurs():
    st.header("📊 Tableau des fournisseurs à qualifier")
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
            st.error(f"Erreur de traitement : {e}")
    df_f = st.session_state.fournisseurs_df
    if not df_f.empty:
        st.subheader("Données fournisseurs en mémoire")
        for i, row in df_f.iterrows():
            with st.expander(f"➡️ {row['Fournisseur']}"):
                c1, c2 = st.columns(2)
                c1.metric("Commandes", row["Nombre_commandes"])
                c2.metric("Délai moyen (j)", row["Délai_moyen"])
                if st.button("Qualifier", key=f"qualif_{i}"):
                    st.session_state.current_fourn = row["Fournisseur"]
                    st.session_state.qualifications = charger_qualifications()
                    st.session_state.page = "Qualification"
                    st.experimental_rerun()
    else:
        st.info("Aucun fournisseur en mémoire. Importez un fichier.")


def afficher_fiche_qualification():
    fournisseur = st.session_state.get("current_fourn")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return
    fiches = st.session_state.qualifications
    exist = next((f for f in fiches if clean_txt(f.get("Fournisseur")) == clean_txt(fournisseur)), None)
    st.header(f"📝 Qualification : {fournisseur}")
    # Champs
    contact = st.text_input("Contact principal", value=exist.get("Contact", "") if exist else "")
    pays = st.text_input("Pays", value=exist.get("Pays", "") if exist else "")
    stock = st.selectbox("Stock réel identifiable ?", ["Oui", "Non"], index=["Oui","Non"].index(exist.get("Stock réel", "Oui")) if exist else 0)
    xdock = st.selectbox("Présence de xdock ?", ["Oui", "Non"], index=["Oui","Non"].index(exist.get("Xdock", "Oui")) if exist else 0)
    delai_stock = st.number_input("Délai annoncé stock (j)", min_value=0, value=exist.get("Délai stock", 0) if exist else 0)
    delai_xdock = st.number_input("Délai annoncé xdock (j)", min_value=0, value=exist.get("Délai xdock", 0) if exist else 0)
    processus = st.selectbox("Processus clair ?", ["Oui","Partiel","Non"], index=["Oui","Partiel","Non"].index(exist.get("Processus commande", "Oui")) if exist else 0)
    transport = st.selectbox("Transport géré par", ["MKP","Fournisseur"], index=["MKP","Fournisseur"].index(exist.get("Transport", "MKP")) if exist else 0)
    tracking = st.selectbox("Tracking fourni ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Tracking", "Oui")) if exist else 0)
    cond = st.selectbox("Condition de paiement", ["A la commande","A expédition","X jours"], index=["A la commande","A expédition","X jours"].index(exist.get("Condition de paiement", "A la commande")) if exist else 0)
    poids = st.selectbox("Poids/volume communiqués ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Poids/volume", "Oui")) if exist else 0)
    statuts = ["Qualifié","Non qualifiés","En cours","Non éligible à l'Elite"]
    statut = st.selectbox("Statut final", statuts, index=statuts.index(exist.get("Statut final", statuts[0])) if exist else 0)
    comment = st.text_area("Commentaire", value=exist.get("Commentaire", "") if exist else "")
    if st.button("Enregistrer"):  # save
        nouvelle = {"Fournisseur": fournisseur, "Contact": contact, "Pays": pays,
                   "Stock réel": stock, "Xdock": xdock,
                   "Délai stock": delai_stock, "Délai xdock": delai_xdock,
                   "Processus commande": processus, "Transport": transport,
                   "Tracking": tracking, "Condition de paiement": cond,
                   "Poids/volume": poids, "Statut final": statut,
                   "Commentaire": comment}
        # mise à jour
        filt = [f for f in fiches if clean_txt(f.get("Fournisseur")) != clean_txt(fournisseur)]
        filt.append(nouvelle)
        sauvegarder_qualifications(filt)
        st.success("Qualification enregistrée.")
        st.session_state.page = "Fournisseurs"
        st.experimental_rerun()


def afficher_dashboard_qualifications():
    st.header("📈 Dashboard des qualifications")
    # recharge
    qualifs = charger_qualifications()
    df = pd.DataFrame(qualifs)
    if df.empty:
        st.info("Aucune qualification disponible.")
        return
    # répartition par statut
    st.subheader("Nombre de fournisseurs par statut")
    stats = df["Statut final"].value_counts().rename_axis("Statut").reset_index(name="Nombre")
    fig = px.bar(stats, x="Statut", y="Nombre", color="Statut", title="Répartition des statuts")
    st.plotly_chart(fig, use_container_width=True)
    # filtres détaillés
    st.sidebar.header("Filtres qualifications")
    sels = st.sidebar.multiselect("Fournisseurs", df["Fournisseur"].unique(), default=df["Fournisseur"].unique())
    num_cols = df.select_dtypes(include="number").columns.tolist()
    crits = st.sidebar.multiselect("Critères numériques", num_cols, default=num_cols)
    sel_df = df[df["Fournisseur"].isin(sels)]
    st.subheader("Tableau synthèse")
    st.dataframe(sel_df[["Fournisseur"] + crits])
    if crits:
        moy = sel_df.groupby("Fournisseur")[crits].mean().reset_index()
        fig2 = px.bar(moy.melt(id_vars="Fournisseur", var_name="Critère", value_name="Moyenne"),
                      x="Critère", y="Moyenne", color="Fournisseur", barmode="group",
                      title="Notes Moyennes par Fournisseur")
        st.plotly_chart(fig2, use_container_width=True)

# --- Navigation par selectbox ---
pages = ["Accueil", "Fournisseurs", "Qualification", "Dashboard Qualifs", "Aide"]
page = st.sidebar.selectbox("Menu", pages)

# --- Routage ---
if page == "Accueil":
    st.write("**Bienvenue !** Sélectionnez une page dans le menu.")
elif page == "Fournisseurs":
    afficher_dashboard_fournisseurs()
elif page == "Qualification":
    afficher_fiche_qualification()
elif page == "Dashboard Qualifs":
    afficher_dashboard_qualifications()
else:
    st.markdown("""
    ### Aide & méthode
    - **Importer** : allez sur 'Fournisseurs' pour charger vos commandes.
    - **Qualifier** : sélectionnez un fournisseur et validez la fiche.
    - **Dashboard** : visualisez la répartition et les statistiques.
    """)
