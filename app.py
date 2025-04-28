import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ics import Calendar, Event

st.set_page_config(page_title="Turni Medici", page_icon="🩺", layout="centered")

st.title("Turni Medici 🩺")
st.subheader("Crea il tuo calendario turni personalizzato")

uploaded_file = st.file_uploader("Carica il file turni (.xlsx o .csv)", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)

    nome_cercato = st.text_input("Nome da cercare esattamente come nel file (es: VITUCCI)")
    indirizzo_lavoro = st.text_input("Indirizzo di lavoro (es: Ospedale San Paolo, Milano)")

    contratto = st.radio("Seleziona contratto:", ("Standard Ospedaliero (38h/settimana)", "Calabria Specializzandi (32h/settimana)"))

    if nome_cercato and indirizzo_lavoro:
        turni = df[df.iloc[:, 0].str.upper() == nome_cercato.upper()]

        calendario = Calendar()

        for index, row in turni.iterrows():
            giorno = row.iloc[1]
            inizio = row.iloc[2]
            fine = row.iloc[3]
            if pd.notna(giorno) and pd.notna(inizio) and pd.notna(fine):
                evento = Event()
                evento.name = f"Turno - {row.iloc[4]}"
                evento.begin = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(inizio).time())
                evento.end = datetime.combine(pd.to_datetime(giorno).date(), pd.to_datetime(fine).time())
                evento.location = indirizzo_lavoro
                evento.description = "Turno generato da Turni Medici"
                calendario.events.add(evento)

        st.download_button("Scarica file .ics", data=str(calendario), file_name="turni_medici.ics", mime="text/calendar")