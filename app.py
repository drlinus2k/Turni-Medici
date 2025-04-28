import streamlit as st
import pandas as pd
from datetime import datetime
from ics import Calendar, Event
import re

# Configurazione Streamlit
st.set_page_config(
    page_title="Gestione Turni Medici",
    page_icon="favicon.ico",
    layout="wide"
)

st.title("Gestione Turni Medici")

# Caricamento file turni
uploaded_file = st.file_uploader("Carica il file dei turni (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("File caricato correttamente!")

    # Selezione del cognome
    cognome_cercato = st.text_input("Inserisci il tuo cognome esattamente come nel file").strip()

    # Selezione contratto
    contratto = st.radio(
        "Seleziona il tipo di contratto:",
        ("Standard Ospedaliero (38h/settimana)", "Calabria Specializzandi (32h/settimana)")
    )
    ore_settimanali = 38 if contratto.startswith("Standard") else 32
    ore_mensili_contratto = ore_settimanali * 4  # Approssimazione 4 settimane

    indirizzo_lavoro = st.text_input("Inserisci l'indirizzo del luogo di lavoro").strip()

    if cognome_cercato and indirizzo_lavoro:
        calendario = Calendar()
        ore_totali = 0

        # Estraggo i dati dalla prima riga: nome turno + orario
        turni_info = []
        for col_idx in range(1, len(df.columns)):
            valore = str(df.iloc[0, col_idx])
            if pd.notna(valore):
                try:
                    # Dividiamo testo in nome turno + orario
                    match = re.search(r"(\d{1,2}[.,-]\d{2})[-](\d{1,2}[.,-]\d{2})", valore)
                    if match:
                        ora_inizio_raw = match.group(1).replace(",", ":").replace(".", ":").replace("-", ":")
                        ora_fine_raw = match.group(2).replace(",", ":").replace(".", ":").replace("-", ":")
                        
                        ora_inizio = pd.to_datetime(ora_inizio_raw, format="%H:%M").time()
                        ora_fine = pd.to_datetime(ora_fine_raw, format="%H:%M").time()
                        
                        nome_turno = valore[:match.start()].strip()

                        turni_info.append((col_idx, nome_turno, ora_inizio, ora_fine))
                except Exception as e:
                    st.warning(f"Errore nella lettura della prima riga nella colonna {col_idx + 1}: {e}")

        # Scorro i giorni successivi (dalla seconda riga)
        for i in range(1, len(df)):
            giorno = df.iloc[i, 0]
            if pd.isna(giorno):
                continue
            giorno_data = pd.to_datetime(giorno).date()

            for col_idx, nome_turno, ora_inizio, ora_fine in turni_info:
                valore_cella = df.iloc[i, col_idx]
                if str(valore_cella).strip().upper() == cognome_cercato.upper():
                    evento = Event()
                    evento.name = nome_turno
                    evento.begin = datetime.combine(giorno_data, ora_inizio)
                    evento.end = datetime.combine(giorno_data, ora_fine)
                    evento.location = indirizzo_lavoro
                    evento.description = "Turno registrato automaticamente."

                    calendario.events.add(evento)

                    durata_ore = (datetime.combine(giorno_data, ora_fine) - datetime.combine(giorno_data, ora_inizio)).total_seconds() / 3600
                    if durata_ore < 0:
                        durata_ore += 24  # correggo notte che attraversa mezzanotte
                    ore_totali += durata_ore

        # Visualizzazione risultati
        st.subheader("Risultati Turni")

        st.markdown(f"**Ore totali lavorate:** {round(ore_totali, 2)} ore")
        st.markdown(f"**Ore previste da contratto selezionato:** {ore_mensili_contratto} ore")

        scostamento = round(ore_totali - ore_mensili_contratto, 2)
        colore = "green" if scostamento >= 0 else "red"

        st.markdown(f"<span style='color:{colore};'><b>Scostamento: {scostamento} ore</b></span>", unsafe_allow_html=True)

        # Download file calendario
        st.download_button(
            label="📅 Scarica il tuo calendario (.ics)",
            data=str(calendario),
            file_name=f"turni_{cognome_cercato.lower()}.ics",
            mime="text/calendar"
        )
