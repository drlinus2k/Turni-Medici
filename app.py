import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar, Event

st.set_page_config(page_title="Turni Medici", page_icon="🩺", layout="centered")

# Titolo elegante centrato e azzurro
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🩺 Turni Medici</h1>", unsafe_allow_html=True)
st.subheader("Crea il tuo calendario turni personalizzato")

uploaded_file = st.file_uploader("Carica il file turni (.xlsx o .csv)", type=["xlsx", "csv"])

if uploaded_file:
   df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)

   nome_cercato = st.text_input("Nome da cercare esattamente come nel file (es: VITUCCI)")
   indirizzo_lavoro = st.text_input("Indirizzo di lavoro (es: Ospedale San Paolo, Milano)")

   contratto = st.radio("Seleziona contratto:", ("Standard Ospedaliero (38h/settimana)", "Calabria Specializzandi (32h/settimana)"))

   calendario = Calendar()
   gettoni = []

   if nome_cercato and indirizzo_lavoro:
       turni = df[df.iloc[:, 0].str.upper() == nome_cercato.upper()]

       st.subheader("💰 Aggiungi turno extra a gettone")
       with st.form(key="form_gettone"):
           data_gettone = st.date_input("Data del turno gettone")
           ora_inizio_gettone = st.time_input("Ora inizio turno gettone")
           ora_fine_gettone = st.time_input("Ora fine turno gettone")
           submit_gettone = st.form_submit_button("Aggiungi turno gettone")

           if submit_gettone:
               gettoni.append((data_gettone, ora_inizio_gettone, ora_fine_gettone))

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
               evento.description = "Turno normale generato da Turni Medici"
               calendario.events.add(evento)

       for data_g, ora_inizio_g, ora_fine_g in gettoni:
           evento = Event()
           evento.name = "Turno Gettone Extra 💰"
           evento.begin = datetime.combine(data_g, ora_inizio_g)
           evento.end = datetime.combine(data_g, ora_fine_g)
           evento.location = indirizzo_lavoro
           evento.description = "Turno a gettone extra"
           calendario.events.add(evento)

       st.download_button("📅 Scarica calendario (.ics)", data=str(calendario), file_name="turni_medici.ics", mime="text/calendar")
