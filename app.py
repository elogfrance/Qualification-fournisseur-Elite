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

        except Exception as e:
            st.error(f"Erreur de traitement : {e}")
