import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ics import Calendar, Event
import re

# Funzione per convertire numeri tipo 8.00 in "08:00"
def float_to_time_string(valore):
    ore = int(valore)
    minuti = int(round((valore - ore) * 60))
    return f"{ore:02d}:{minuti:02d}"

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

        # Estraggo nome turno + orario dalla prima riga
        turni_info = []
        for col_idx in range(1, len(df.columns)):
            valore = df.iloc[0, col_idx]

            if pd.isna(valore):
                continue

            valore_str = str(valore)

            try:
                # Se contiene numeri separati da trattino
                match = re.search(r"(\d{1,2}[.,-]?\d{0,2})[-](\d{1,2}[.,-]?\d{0,2})", valore_str)
                if match:
                    ora_inizio_raw = match.group(1).replace(",", ".").replace("-", ".")
                    ora_fine_raw = match.group(2).replace(",", ".").replace("-", ".")

                    try:
                        # Prova a interpretare come numeri
                        ora_inizio_num = float(ora_inizio_raw)
                        ora_fine_num = float(ora_fine_raw)

                        ora_inizio = pd.to_datetime(float_to_time_string(ora_inizio_num), format="%H:%M").time()
                        ora_fine = pd.to_datetime(float_to_time_string(ora_fine_num), format="%H:%M").time()

                    except:
                        # Se non sono numeri, tratta come testo orario normale
                        ora_inizio = pd.to_datetime(ora_inizio_raw.replace(".", ":")).time()
                        ora_fine = pd.to_datetime(ora_fine_raw.replace(".", ":")).time()

                    nome_turno = valore_str[:match.start()].strip()

                    turni_info.append((col_idx, nome_turno, ora_inizio, ora_fine))
            except Exception as e:
                st.warning(f"Errore nella lettura della prima riga nella colonna {col_idx + 1}: {e}")

        # Scorro i giorni successivi
        for i in range(1, len(df)):
            giorno = df.iloc[i, 0]
            if pd.isna(giorno):
                continue
            giorno_data = pd.to_datetime(giorno).date()

            for col_idx, nome_turno, ora_inizio, ora_fine in turni_info:
                valore_cella = df.iloc[i, col_idx]
                if str(valore_cella).strip().upper() == cognome_cercato.upper():
                    # Costruisco inizio e fine turno
                    inizio_dt = datetime.combine(giorno_data, ora_inizio)
                    fine_dt = datetime.combine(giorno_data, ora_fine)

                    # Se il turno attraversa la mezzanotte, aggiungo 1 giorno
                    if fine_dt <= inizio_dt:
                        fine_dt += timedelta(days=1)

                    # Creo evento
                    evento = Event()
                    evento.name = nome_turno
                    evento.begin = inizio_dt
                    evento.end = fine_dt
                    evento.location = indirizzo_lavoro
                    evento.description = "Turno registrato automaticamente."

                    calendario.events.add(evento)

                    # Calcolo ore
                    durata_ore = (fine_dt - inizio_dt).total_seconds() / 3600
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
