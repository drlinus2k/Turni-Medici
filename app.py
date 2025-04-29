import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import zipfile

# Orari predefiniti associati al tipo di turno nel nome colonna
ORARI_PREDEFINITI = {
    "MATTINO": ("08:00", "14:30"),
    "POMERIGGIO": ("14:30", "21:00"),
    "NOTTE": ("21:00", "08:00+1"),
    "OBI": ("14:30", "20:00"),
    "OB": ("08:00", "14:30"),
    "M3": ("08:15", "15:30"),
    "PONTE": ("11:30", "18:30"),
}

INDIRIZZO = "PS San Paolo, Via San Vigilio 22 Milano Italia"

# Estrai turni cercando il nome medico in tutte le colonne (esclusa la prima)
def estrai_turni(df, nome):
    turni = []
    for _, row in df.iterrows():
        data = row["Data"]
        for col in df.columns[1:]:
            if isinstance(row[col], str) and nome.upper() in row[col].upper():
                tipo_turno = None
                for chiave in ORARI_PREDEFINITI:
                    if chiave in str(col).upper():
                        tipo_turno = chiave
                        break
                if tipo_turno:
                    inizio_str, fine_str = ORARI_PREDEFINITI[tipo_turno]
                    start_time = datetime.strptime(f"{data.date()} {inizio_str}", "%Y-%m-%d %H:%M")
                    if "+1" in fine_str:
                        fine_str = fine_str.replace("+1", "")
                        end_date = data.date() + timedelta(days=1)
                    else:
                        end_date = data.date()
                    end_time = datetime.strptime(f"{end_date} {fine_str}", "%Y-%m-%d %H:%M")
                    turni.append({
                        "Titolo": f"Turno {tipo_turno.title()}",
                        "Inizio": start_time,
                        "Fine": end_time
                    })
    return turni

def crea_file_ics(turno, index, output_dir, nome):
    dt_fmt = "%Y%m%dT%H%M%S"
    start = turno['Inizio'].strftime(dt_fmt)
    end = turno['Fine'].strftime(dt_fmt)
    uid = f"turno{index}@{nome.lower()}"
    nome_file = f"turno_{index:02d}_{turno['Titolo'].replace(' ', '_')}.ics"

    contenuto = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TurniMedico//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now(timezone.utc).strftime(dt_fmt)}Z
DTSTART;TZID=Europe/Rome:{start}
DTEND;TZID=Europe/Rome:{end}
SUMMARY:{turno['Titolo']}
DESCRIPTION:Turno lavorativo assegnato a {nome}
LOCATION:{INDIRIZZO}
END:VEVENT
END:VCALENDAR
"""

    path_completo = os.path.join(output_dir, nome_file)
    with open(path_completo, "w") as f:
        f.write(contenuto)
    return path_completo

# --- Interfaccia Streamlit ---

st.title("ICS Extractor – Turni Medici da Excel")

uploaded_file = st.file_uploader("Carica il file Excel dei turni", type=["xlsx"])
nome_medico = st.text_input("Nome del medico (es. VITUCCI)")
nome_foglio = st.text_input("Nome del foglio", value="MAGGIO 2025")

if uploaded_file and nome_medico:
    try:
        # Caricamento dati
        df = pd.read_excel(uploaded_file, sheet_name=nome_foglio)
        prima_colonna = df.columns[0]
        df = df[df[prima_colonna].astype(str).str.contains('2025-05', na=False)]
        df = df.rename(columns={prima_colonna: 'Data'})
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df[df['Data'].notna()]

        # Estrazione turni
        turni = estrai_turni(df, nome_medico)

        if not turni:
            st.warning("Nessun turno trovato per il medico indicato.")
        else:
            st.success(f"Trovati {len(turni)} turni per {nome_medico}.")

            # Generazione dei file ICS
            with st.spinner("Generazione dei file ICS..."):
                output_dir = "ics_files"
                os.makedirs(output_dir, exist_ok=True)

                ics_paths = [crea_file_ics(t, i+1, output_dir, nome_medico) for i, t in enumerate(turni)]
                zip_path = f"{output_dir}_{nome_medico}.zip"
                with zipfile.ZipFile(zip_path, 'w') as z:
                    for file in ics_paths:
                        z.write(file, os.path.basename(file))

                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Scarica tutti i turni in formato ZIP",
                        data=f,
                        file_name=f"turni_{nome_medico}.zip",
                        mime="application/zip"
                    )

    except Exception as e:
        st.error(f"Errore durante l'elaborazione: {e}")
