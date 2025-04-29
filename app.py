import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import zipfile
import argparse

def carica_file_excel(percorso_file, foglio):
    df = pd.read_excel(percorso_file, sheet_name=foglio)
    df = df[df[df.columns[0]].astype(str).str.contains('2025-05')]
    df.columns.values[0] = 'Data'
    df['Data'] = pd.to_datetime(df['Data'])
    return df

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

def esporta_turni(percorso_excel, nome_medico, foglio='MAGGIO 2025', crea_zip=True):
    df = carica_file_excel(percorso_excel, foglio)
    turni = estrai_turni(df, nome_medico)

    output_dir = os.path.join(os.path.dirname(percorso_excel), f"Turni_{nome_medico}_ICS")
    os.makedirs(output_dir, exist_ok=True)

    files = [crea_file_ics(t, i+1, output_dir, nome_medico) for i, t in enumerate(turni)]

    if crea_zip:
        zip_path = output_dir + ".zip"
        with zipfile.ZipFile(zip_path, 'w') as z:
            for file in files:
                z.write(file, os.path.basename(file))
        print(f"[✓] Archivio ZIP creato: {zip_path}")
    else:
        print(f"[✓] File ICS salvati in: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Estrai i turni da un file Excel e genera file ICS.")
    parser.add_argument("file", help="Percorso del file Excel dei turni")
    parser.add_argument("medico", help="Nome del medico da cercare (es. VITUCCI)")
    parser.add_argument("--foglio", default="MAGGIO 2025", help="Nome del foglio Excel (default: 'MAGGIO 2025')")
    parser.add_argument("--nozip", action="store_true", help="Non creare archivio ZIP")

    args = parser.parse_args()
    esporta_turni(args.file, args.medico, foglio=args.foglio, crea_zip=not args.nozip)

if __name__ == "__main__":
    main()
