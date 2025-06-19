import streamlit as st
import pandas as pd
import json
import os
import shutil
import plotly.express as px

# --- Chemins des fichiers ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUAL_JSON_PATH = os.path.join(BASE_DIR, "data", "qualifications.json")
FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data_current.json")
OLD_FOURN_JSON_PATH = os.path.join(BASE_DIR, "data", "fournisseurs_data.json")

# --- Chargement & sauvegarde ---
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

# --- Utilitaires ---
def clean_txt(s: str) -> str:
    return str(s).strip().lower()

# --- Session State ---
if "qualifications" not in st.session_state:
    st.session_state.qualifications = charger_qualifications()
if "fournisseurs_df" not in st.session_state:
    st.session_state.fournisseurs_df = charger_fournisseurs()

# --- Config Page ---
st.set_page_config(page_title="Qualification Fournisseur Express", page_icon="📦", layout="centered")

# --- En‑tête ---
st.image("assets/logo_marketparts.png", width=400)
st.title("Projet : Qualification Fournisseur Express")

# --- Fonction de saisie de qualification ---
def afficher_form_qualification(fournisseur):
    """Affiche le formulaire de qualification pour un fournisseur donné."""
    # Recherche existante
    fiches = st.session_state.qualifications
    exist = next((f for f in fiches if clean_txt(f.get("Fournisseur")) == clean_txt(fournisseur)), None)
    st.subheader(f"📝 Qualification : {fournisseur}")

    # Champs
    contact = st.text_input("Contact principal", value=exist.get("Contact", "") if exist else "")
    pays = st.text_input("Pays", value=exist.get("Pays", "") if exist else "")
    stock = st.selectbox("Stock identifiable ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Stock réel","Oui")) if exist else 0)
    xdock = st.selectbox("Présence de xdock ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Xdock","Oui")) if exist else 0)
    delai_stock = st.number_input("Délai stock (j)", min_value=0, value=exist.get("Délai stock",0) if exist else 0)
    delai_xdock = st.number_input("Délai xdock (j)", min_value=0, value=exist.get("Délai xdock",0) if exist else 0)
    proc = st.selectbox("Processus clair ?", ["Oui","Partiel","Non"], index=["Oui","Partiel","Non"].index(exist.get("Processus commande","Oui")) if exist else 0)
    transport = st.selectbox("Transport géré par", ["MKP","Fournisseur"], index=["MKP","Fournisseur"].index(exist.get("Transport","MKP")) if exist else 0)
    tracking = st.selectbox("Tracking fourni ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Tracking","Oui")) if exist else 0)
    cond = st.selectbox("Condition de paiement", ["A la commande","A expédition","X jours"], index=["A la commande","A expédition","X jours"].index(exist.get("Condition de paiement","A la commande")) if exist else 0)
    poids = st.selectbox("Poids/volume ?", ["Oui","Non"], index=["Oui","Non"].index(exist.get("Poids/volume","Oui")) if exist else 0)
    statuts = ["Qualifié","Non qualifiés","En cours","Non éligible à l'Elite"]
    statut = st.selectbox("Statut final", statuts, index=statuts.index(exist.get("Statut final",statuts[0])) if exist else 0)
    comment = st.text_area("Commentaire", value=exist.get("Commentaire","") if exist else "")

    if st.button("Enregistrer qualification", key=f"save_{fournisseur}"):
        nouvelle = {
            "Fournisseur": fournisseur, "Contact": contact, "Pays": pays,
            "Stock réel": stock, "Xdock": xdock,
            "Délai stock": delai_stock, "Délai xdock": delai_xdock,
            "Processus commande": proc, "Transport": transport,
            "Tracking": tracking, "Condition de paiement": cond,
            "Poids/volume": poids, "Statut final": statut,
            "Commentaire": comment
        }
        # MAJ et sauvegarde
        updated = [f for f in fiches if clean_txt(f.get("Fournisseur")) != clean_txt(fournisseur)]
        updated.append(nouvelle)
        sauvegarder_qualifications(updated)
        st.session_state.qualifications = updated
        st.success("✅ Qualification enregistrée !")

# --- Page: Fournisseurs ---
def afficher_dashboard_fournisseurs():
    st.subheader("📊 Fournisseurs à qualifier")
    fichier = st.file_uploader("Importer commandes (xlsx)", type=["xlsx"])
    if fichier:
        try:
            df = pd.read_excel(fichier)
            df = df.rename(columns={"Supplier name":"Fournisseur","Date ARC fournisseur reçu":"Date ARC","Date ready for pickup":"Date Ready"})
            df["Date ARC"] = pd.to_datetime(df["Date ARC"],errors="coerce")
            df["Date Ready"] = pd.to_datetime(df["Date Ready"],errors="coerce")
            df = df.dropna(subset=["Date ARC","Date Ready","Fournisseur"])
            df["Délai (jours)"] = (df["Date Ready"]-df["Date ARC"]).dt.days
            result = df.groupby("Fournisseur").agg(Nombre_commandes=("Fournisseur","count"),Délai_moyen=("Délai (jours)",lambda x: round(x.mean(),1))).reset_index().sort_values("Nombre_commandes",ascending=False)
            sauvegarder_fournisseurs(result)
            st.session_state.fournisseurs_df = result
            st.success("✅ Données commandes sauvegardées.")
        except Exception as e:
            st.error(f"Erreur de traitement : {e}")
    df_f = st.session_state.fournisseurs_df
    if df_f.empty:
        st.info("Aucun fournisseur en mémoire. Importez des commandes.")
        return
    for i,row in df_f.iterrows():
        with st.expander(f"➡️ {row['Fournisseur']}"):
            c1,c2 = st.columns(2)
            c1.metric("Commandes",row["Nombre_commandes"])
            c2.metric("Délai moyen (j)",row["Délai_moyen"])
            if st.button("Qualifier",key=f"qual_{i}"):
                afficher_form_qualification(row["Fournisseur"])

# --- Page: Dashboard Qualifs ---
def afficher_dashboard_qualifications():
    st.subheader("📈 Dashboard des qualifications")
    df = pd.DataFrame(st.session_state.qualifications)
    if df.empty:
        st.info("Aucune qualification.")
        return
    st.write("### Répartition par statut")
    status = df["Statut final"].value_counts().rename_axis("Statut").reset_index(name="Nombre")
    fig=px.bar(status,x="Statut",y="Nombre",color="Statut",title="Répartition des statuts")
    st.plotly_chart(fig,use_container_width=True)

# --- Navigation ---
pages=["Fournisseurs","Dashboard Qualifs","Aide"]
page=st.sidebar.selectbox("Menu",pages)
if page=="Fournisseurs":
    afficher_dashboard_fournisseurs()
elif page=="Dashboard Qualifs":
    afficher_dashboard_qualifications()
else:
    st.markdown("- Import: page Fournisseurs\n- Aide: en cours...")
