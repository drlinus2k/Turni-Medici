import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar, Event

# CONFIGURAZIONE STREAMLIT
st.set_page_config(
    page_title="Turni Medici",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="auto",
)

# SFONDO CON CORRIDOIO OSPEDALIERO ASTRATTO
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1588776814546-ec77c5e3e5d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80');
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
ore_mensili_contratto = ore_settimanali * 4  # approssimazione base 4 settimane

# CARICAMENTO FILE TURNI
st.subheader("Carica il file dei turni (.xlsx o .csv)")
uploaded_file = st.file_uploader("Seleziona file", type=["xlsx", "csv"])

calendario = Calendar()
gettoni = []
ore_normali = 0
ore_gettoni = 0

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)

    nome_cercato = st.text_input("Nome da cercare esattamente come nel file (es: MARIO ROSSI)").strip()
    indirizzo_lavoro = st.text_input("Indirizzo di lavoro (es: Ospedale Generale, Milano)").strip()

    if nome_cercato and indirizzo_lavoro:
        turni = df[df.iloc[:, 0].str.upper() == nome_cercato.upper()]

        for index, row in turni.iterrows():
            giorno = row.iloc[1]
            inizio = row.iloc[2]
            fine = row.iloc[3]
            tipo_turno = row.iloc[4] if len(row) > 4 else "Turno"

            if pd.notna(giorno) and pd.notna(inizio) and pd.notna(fine):
                evento = Event()
                evento.name = f"Turno - {tipo_turno}"
                evento.begin = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(inizio).time())
                evento.end = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(fine).time())
                evento.location = indirizzo_lavoro
                evento.description = "Turno ordinario"

                diff_ore = (pd.to_datetime(fine) - pd.to_datetime(inizio)).total_seconds() / 3600
                ore_normali += diff_ore

                calendario.events.add(evento)

# AGGIUNTA TURNI GETTONI
st.subheader("Aggiungi eventuali turni extra a gettone")
with st.form(key="form_gettoni"):
    data_gettone = st.date_input("Data del turno gettone")
    ora_inizio_gettone = st.time_input("Ora inizio turno gettone")
    ora_fine_gettone = st.time_input("Ora fine turno gettone")
    submit_gettone = st.form_submit_button("Aggiungi turno a gettone")

    if submit_gettone:
        evento = Event()
        evento.name = "Turno Gettone Extra"
        evento.begin = datetime.combine(data_gettone, ora_inizio_gettone)
        evento.end = datetime.combine(data_gettone, ora_fine_gettone)
        evento.location = "Turno a gettone"
        evento.description = "Turno a gettone extra"

        diff_ore_gettone = (datetime.combine(data_gettone, ora_fine_gettone) - datetime.combine(data_gettone, ora_inizio_gettone)).total_seconds() / 3600
        ore_gettoni += diff_ore_gettone
