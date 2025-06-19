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

def clean(nom):
    return str(nom).strip().lower()

# --- Initialisation du session state ---
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()
if "page" not in st.session_state:
    st.session_state.page = "home"
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

# --- Page: Dashboard Fournisseurs ---
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
            result = df.groupby("Fournisseur").agg(
                Nombre_commandes=("Fournisseur", "count"),
                Délai_moyen=("Délai (jours)", lambda x: round(x.dropna().mean(), 1))
            ).reset_index().sort_values(by="Nombre_commandes", ascending=False)

            sauvegarder_fournisseurs(result)
            st.session_state.fournisseurs_df = result
            st.success("✅ Données importées et sauvegardées.")
        except Exception as e:
            st.error(f"Erreur pendant le traitement du fichier : {e}")

    df_f = st.session_state.fournisseurs_df
    if not df_f.empty:
        st.markdown("### Données fournisseurs en mémoire")
        for i, row in df_f.iterrows():
            with st.expander(f"➡️ {row['Fournisseur']}"):
                c1, c2 = st.columns(2)
                c1.metric("📦 Commandes", row["Nombre_commandes"])
                c2.metric("⏱️ Délai moyen", f"{row['Délai_moyen']} j")
                if st.button("📝 Accéder à la qualification", key=f"btn_qualif_{i}"):
                    st.session_state.fournisseur_en_cours = row['Fournisseur']
                    st.session_state.page = "qualification"
                    st.rerun()
    else:
        st.info("📥 Veuillez importer un fichier pour voir le tableau.")

# --- Page: Fiche Qualification ---
def afficher_fiche_qualification():
    fournisseur = st.session_state.get("fournisseur_en_cours")
    if not fournisseur:
        st.warning("Aucun fournisseur sélectionné.")
        return

    fiche_existante = next(
        (f for f in st.session_state.qualifications if clean(f.get("Fournisseur")) == clean(fournisseur)),
        None
    )
    st.title(f"📝 Qualification : {fournisseur}")

    # Champs de saisie
    contact = st.text_input("👤 Contact principal", value=fiche_existante.get("Contact", "") if fiche_existante else "")
    pays = st.text_input("🌍 Pays", value=fiche_existante.get("Pays", "") if fiche_existante else "")
    stock_identifiable = st.selectbox(
        "📦 Stock réel identifiable ?", [" ", "Oui", "Non"],
        index=[" ", "Oui", "Non"].index(fiche_existante.get("Stock réel", " ")) if fiche_existante else 0
    )
    xdock_present = st.selectbox(
        "🔁 Présence de xdock ?", [" ", "Oui", "Non"],
        index=[" ", "Oui", "Non"].index(fiche_existante.get("Xdock", " ")) if fiche_existante else 0
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
        "📋 Processus de commande clair ?", [" ", "Oui", "Partiel", "Non"],
        index=[" ", "Oui", "Partiel", "Non"].index(fiche_existante.get("Processus commande", " ")) if fiche_existante else 0
    )
    transport = st.selectbox(
        "🚚 Qui gère le transport ?", [" ", "MKP", "Fournisseur"],
        index=[" ", "MKP", "Fournisseur"].index(fiche_existante.get("Transport", "MKP")) if fiche_existante else 0
    )
    tracking = st.selectbox(
        "📦 Tracking fourni ?", [" ", "Oui", "Non"],
        index=[" ", "Oui", "Non"].index(fiche_existante.get("Tracking", " ")) if fiche_existante else 0
    )
    options_cond = [" ", "A la commande", "A expédition", "X jours"]
    idx_cond = options_cond.index(fiche_existante.get("Condition de paiement", " ")) if fiche_existante else 0
    condition_paiement = st.selectbox("💳 Condition de paiement", options_cond, index=idx_cond)
    poids_volume = st.selectbox(
        "📏 Poids/volume communiqués ?", [" ", "Oui", "Non"],
        index=[" ", "Oui", "Non"].index(fiche_existante.get("Poids/volume", " ")) if fiche_existante else 0
    )
    statut_final = st.selectbox(
        "📌 Statut final", ["Non qualifiés", "Qualifié", "En cours", "Non éligible à l'Elite"],
        index=["Non qualifiés", "Qualifié", "En cours", "Non éligible à l'Elite"].index(fiche_existante.get("Statut final", " ")) if fiche_existante else 0
    )
    commentaire = st.text_area("📝 Commentaire", value=fiche_existante.get("Commentaire", "") if fiche_existante else "")

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
            "Condition de paiement": condition_paiement,
            "Poids/volume": poids_volume,
            "Statut final": statut_final,
            "Commentaire": commentaire
        }
        st.session_state.qualifications = [
            f for f in st.session_state.qualifications
            if clean(f.get("Fournisseur")) != clean(fournisseur)
        ]
        st.session_state.qualifications.append(nouvelle_fiche)
        sauvegarder_qualifications(st.session_state.qualifications)
        st.success("✅ Données sauvegardées.")
        st.session_state.page = "fournisseurs"
        st.rerun()

def afficher_dashboard_qualifications():
    st.header("📈 Dashboard des qualifications
    Dealis et nbr de commandes mesurés 90 jours avant le 19/06/2025
    Delais caluclés entre validation arc et date de reception e log")

    # Charger fournisseurs + qualifications
    df_fourn = st.session_state.fournisseurs_df.copy()
    df_qual = pd.DataFrame(charger_qualifications()) if st.session_state.qualifications else pd.DataFrame(columns=["Fournisseur","Statut final"])
    df = df_fourn.merge(df_qual, on="Fournisseur", how="left")
    df["Statut final"] = df["Statut final"].fillna("Non qualifiés")

    # — Camembert des statuts —
    st.subheader("Répartition des fournisseurs par statut")
    stats = (
        df["Statut final"]
        .value_counts()
        .rename_axis("Statut")
        .reset_index(name="Nombre")
    )
    fig = px.pie(
        stats,
        names="Statut",
        values="Nombre",
        title="Répartition des statuts (camembert)",
        hole=0
    )
    st.plotly_chart(fig, use_container_width=True)

   # Filtres supplémentaires
    st.sidebar.header("Filtres qualifications")
    fournisseurs = df["Fournisseur"].tolist()
    sel_fourn = st.sidebar.multiselect(
        "Fournisseurs", fournisseurs, default=fournisseurs, key="dash_fourn"
    )
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    sel_cols = st.sidebar.multiselect(
        "Critères numériques", num_cols, default=num_cols, key="dash_cols"
    )

    df_sel = df[df["Fournisseur"].isin(sel_fourn)]

    # Tableau synthèse
    st.subheader("Tableau synthèse")
    # Renommer la colonne 'Statut final' en 'Statut' pour l'affichage
    if "Statut final" in df_sel.columns:
        df_sel = df_sel.rename(columns={"Statut final": "Statut"})
    # Construire les colonnes à afficher : Fournisseur, Statut, puis critères sélectionnés
    display_cols = ["Fournisseur", "Statut"] + sel_cols
    st.dataframe(df_sel[display_cols])

    if sel_cols:
        moy = df_sel.groupby("Fournisseur")[sel_cols].mean().reset_index()
        fig2 = px.bar(
            moy.melt(id_vars="Fournisseur", var_name="Critère", value_name="Moyenne"),
            x="Critère", y="Moyenne", color="Fournisseur", barmode="group",
            title="Notes Moyennes par Fournisseur"
        )
        st.plotly_chart(fig2, use_container_width=True)
# --- Routage des pages ---
if st.session_state.page == "home":
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📂 Fournisseurs"):
            st.session_state.page = "fournisseurs"
            st.rerun()
    with col2:
        if st.button("📈 Dashboard Qualifs"):
            st.session_state.page = "dashboard_qualifs"
            st.rerun()
    with col3:
        if st.button("📘 Aide"):
            st.session_state.page = "aide"
            st.rerun()

elif st.session_state.page == "fournisseurs":
    afficher_dashboard_fournisseurs()

elif st.session_state.page == "qualification":
    afficher_fiche_qualification()

elif st.session_state.page == "dashboard_qualifs":
    afficher_dashboard_qualifications()

elif st.session_state.page == "aide":
    st.title("Aide & méthode")
    st.markdown(
        """
        - **Importer** : utilisez le bouton "Fournisseurs" pour charger vos données de commandes.
        - **Qualifier** : accédez à chaque fiche via le tableau des fournisseurs.
        - **Dashboard** : visualisez un résumé des qualifications réalisées.
        """
    )
