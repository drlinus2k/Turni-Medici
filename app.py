import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import zipfile

# --- Funzioni di supporto ---

def estrai_turni(df, nome):
    turni = []
    orari = {
        'PS Mattino': ('08:00', '14:30'),
        'PS Pomeriggio': ('14:30', '21:00'),
        'PS Notte': ('21:00', '08:00+1'),
        'OB Mattino': ('08:00', '14:30'),
        'OBI Pomeriggio': ('14:30', '20:00'),
        'M3': ('08:15', '15:30'),
        'PS Ponte': ('11:30', '18:30'),
    }

    colonne = {
        'PS Mattino 1', 'PS Mattino 2', 'PS Pomeriggio 1', 'PS Pomeriggio 2',
        'PS Notte 1', 'PS Notte 2', 'OB Mattino', 'OBI Pomeriggio', 'M3', 'PS Ponte'
    }

    df = df[[col for col in df.columns if col == 'Data' or col in colonne]]

    for _, row in df.iterrows():
        for col in colonne:
            if col in row and isinstance(row[col], str) and nome.upper() in row[col].upper():
                turno = col.replace(' 1', '').replace(' 2', '')
                start, end = orari[turno]
                dt_start = datetime.strptime(f"{row['Data'].date()} {start}", "%Y-%m-%d %H:%M")
                if '+1' in end:
                    dt_end = datetime.strptime(f"{row['Data'].date() + timedelta(days=1)} {end.replace('+1', '')}", "%Y-%m-%d %H:%M")
                else:
                    dt_end = datetime.strptime(f"{row['Data'].date()} {end}", "%Y-%m-%d %H:%M")
                turni.append({'Titolo': turno, 'Inizio': dt_start, 'Fine': dt_end})
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
SUMMARY:Turno {turno['Titolo']}
DESCRIPTION:Turno lavorativo assegnato a {nome}
END:VEVENT
END:VCALENDAR
"""

    path_completo = os.path.join(output_dir, nome_file)
    with open(path_completo, "w") as f:
        f.write(contenuto)
    return path_completo

# --- Streamlit UI ---

st.title("ICS Extractor – Turni Medici da Excel")

uploaded_file = st.file_uploader("Carica il file Excel dei turni", type=["xlsx"])
nome_medico = st.text_input("Nome del medico (es. VITUCCI)")
nome_foglio = st.text_input("Nome del foglio", value="MAGGIO 2025")

if uploaded_file and nome_medico:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=nome_foglio)
        df = df[df[df.columns[0]].astype(str).str.contains('2025-05')]
        df.columns.values[0] = 'Data'
        df['Data'] = pd.to_datetime(df['Data'])

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
