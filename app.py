import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar, Event

# CONFIGURAZIONE STREAMLIT
st.set_page_config(
    page_title="Turni Medici",
    page_icon="favicon.ico",
    layout="wide",
)

# SFONDO CORRIDOIO ASTRATTO
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('assets/corridoio.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# TITOLO
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>Turni Medici</h1>", unsafe_allow_html=True)
st.markdown("### ")

# SCELTA CONTRATTO
contratto = st.radio("Seleziona il tipo di contratto:", ("Standard Ospedaliero (38h/settimana)", "Calabria Specializzandi (32h/settimana)"))

ore_settimanali = 38 if contratto.startswith("Standard") else 32
ore_mensili_contratto = ore_settimanali * 4  # Approssimazione base

# INIZIALIZZAZIONE
calendario_ufficiale = Calendar()
calendario_gettoni = Calendar()
ore_ordinari = 0
ore_gettoni = 0

# CARICAMENTO FILE TURNI UFFICIALI
st.subheader("Carica il file dei turni ordinari (.xlsx)")
uploaded_file = st.file_uploader("Seleziona file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("File caricato correttamente!")

    nome_cercato = st.text_input("Nome da cercare esattamente come nel file (es: VITUCCI)").strip()
    indirizzo_lavoro = st.text_input("Indirizzo di lavoro turni ordinari (es: Ospedale Generale, Milano)").strip()

    if nome_cercato and indirizzo_lavoro:
        turni = df[df.iloc[:, 0].str.upper() == nome_cercato.upper()]

        if not turni.empty:
            for index, row in turni.iterrows():
                giorno = row.iloc[1]
                inizio = row.iloc[2]
                fine = row.iloc[3]

                if pd.notna(giorno) and pd.notna(inizio) and pd.notna(fine):
                    evento = Event()
                    evento.name = "Turno Ordinario"
                    evento.begin = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(inizio).time())
                    evento.end = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(fine).time())
                    evento.location = indirizzo_lavoro
                    evento.description = "Turno ordinario ufficiale"

                    diff_ore = (pd.to_datetime(fine) - pd.to_datetime(inizio)).total_seconds() / 3600
                    ore_ordinari += diff_ore

                    calendario_ufficiale.events.add(evento)
        else:
            st.warning("Nome non trovato nel file caricato!")

# AGGIUNTA TURNI A GETTONE
st.subheader("Aggiungi turni a gettone extra")
with st.form(key="form_gettoni"):
    data_gettone = st.date_input("Data turno gettone")
    ora_inizio_gettone = st.time_input("Ora inizio turno gettone")
    ora_fine_gettone = st.time_input("Ora fine turno gettone")
    indirizzo_gettone = st.text_input("Indirizzo di lavoro gettone", value="Struttura privata")

    submit_gettone = st.form_submit_button("Aggiungi turno gettone")

    if submit_gettone:
        evento = Event()
        evento.name = "Turno Gettone Extra"
        evento.begin = datetime.combine(data_gettone, ora_inizio_gettone)
        evento.end = datetime.combine(data_gettone, ora_fine_gettone)
        evento.location = indirizzo_gettone
        evento.description = "Turno gettone extra"

        diff_ore_gettone = (datetime.combine(data_gettone, ora_fine_gettone) - datetime.combine(data_gettone, ora_inizio_gettone)).total_seconds() / 3600
        ore_gettoni += diff_ore_gettone

        calendario_gettoni.events.add(evento)

# RISULTATI CONTEGGIO
st.subheader("Risultati conteggio")
st.markdown(f"**Ore totali turni ordinari:** {round(ore_ordinari, 2)} ore")
st.markdown(f"**Ore totali turni a gettone:** {round(ore_gettoni, 2)} ore")
st.markdown(f"**Ore complessive:** {round(ore_ordinari + ore_gettoni, 2)} ore")
st.markdown(f"**Ore teoriche previste dal contratto:** {ore_mensili_contratto} ore")

scostamento = ore_ordinari - ore_mensili_contratto
colore = "green" if scostamento >= 0 else "red"
st.markdown(f"<span style='color:{colore};'><b>Scostamento rispetto al contratto: {round(scostamento, 2)} ore</b></span>", unsafe_allow_html=True)

# DISCLAIMER
st.markdown("---")
st.markdown("<small>⚠️ Conteggio indicativo. Non sostituisce il conteggio ufficiale dell'amministrazione ospedaliera.</small>", unsafe_allow_html=True)

# DOWNLOAD FILES
st.subheader("Scarica i calendari")

st.download_button(
    label="📅 Scarica turni ordinari (.ics)",
    data=str(calendario_ufficiale),
    file_name="turni_ufficiali.ics",
    mime="text/calendar"
)

st.download_button(
    label="💰 Scarica turni a gettone (.ics)",
    data=str(calendario_gettoni),
    file_name="turni_gettoni.ics",
    mime="text/calendar"
)
