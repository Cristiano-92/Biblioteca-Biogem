import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import base64
import os

# 🔐 Gestione login con sessione
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Biblioteca Fondazione Biogem")
    password = st.text_input("🔒 Inserisci la password", type="password")
    valid_passwords = ["biogem2025", "Renato20Mazza25", "Mario20Zecchino25"]

    if password in valid_passwords:
        st.session_state.logged_in = True
        st.rerun()
    elif password:
        st.warning("Password errata. Riprova.")
        st.stop()
    else:
        st.stop()

st.set_page_config(page_title="Archivio Biblioteca", layout="wide")

# Funzione per convertire immagine locale in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Logo codificato in base64
logo_base64 = get_base64_image("biogem-logo.png")  # Assicurati che il file sia nella stessa cartella

# Mostra titolo con logo allineato
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="data:image/png;base64,{logo_base64}" width="80" style="margin: 0;">
        <h1 style="margin: 0; font-size: 2.5em;">Biblioteca Fondazione Biogem</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Copertina non sfocata
st.image("foto biblioteca biogem.png", use_container_width=True)


# 🔧 Sfondo sfocato con "biblioteca.jpeg"
def set_blurred_background(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/jpeg;base64,{encoded}") no-repeat center center fixed;
            background-size: cover;
        }}
        .main {{
            backdrop-filter: blur(70px);
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem;
            border-radius: 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Applica lo sfondo
set_blurred_background("biblioteca.jpeg")


# Carica i dati Excel
@st.cache_data

def carica_fondi():
    xls = pd.ExcelFile("Elenco interno - 16-06-2025.xlsm")
    fondi = {}
    for nome in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=nome)
            fondi[nome] = df
        except:
            continue
    return fondi

fondi = carica_fondi()

# Ricerca semplice e avanzata
st.markdown("### 🔍 Ricerca nel catalogo")
col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input("Cerca per titolo o autore")

with col2:
    avanzata = st.toggle("Ricerca avanzata")

if avanzata:
    parola_chiave = st.text_input("Parola chiave (presente in qualsiasi campo)")
else:
    parola_chiave = None

# Risultati ricerca
def cerca(fondi, query, parola_chiave):
    risultati = []
    for nome_fondo, df in fondi.items():
        if df.empty:
            continue
        df_copia = df.copy()
        df_copia["_Fondo"] = nome_fondo

        condizioni = []

        if query:
            condizioni.append(
                df_copia.apply(lambda r: query.lower() in str(r).lower(), axis=1)
            )

        if parola_chiave:
            if df_copia.shape[1] > 4:  # Verifica che esista almeno la colonna E
                condizioni.append(
                    df_copia.iloc[:, 4].astype(str).str.lower().str.contains(parola_chiave.lower())
                )
            else:
                continue

        if condizioni:
            filtro = condizioni[0]
            for cond in condizioni[1:]:
                filtro = filtro & cond
            risultati.append(df_copia[filtro])

    if risultati:
        return pd.concat(risultati)
    else:
        return pd.DataFrame()


if query or parola_chiave:
    st.markdown("---")
    st.markdown("### 📃 Risultati della ricerca")
    risultati = cerca(fondi, query, parola_chiave)
    if not risultati.empty:
        for _, riga in risultati.iterrows():
            with st.container():
                st.markdown(
                    f"""
                    <div style='border:1px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px'>
                        <b>Titolo:</b> {riga.iloc[0]}<br>
                        <b>Autore:</b> {riga.iloc[1]}<br>
                        <b>Fondo:</b> {riga['_Fondo']}<br>
                        <b>Collocazione:</b> {riga.iloc[3] if len(riga) > 3 else '-'}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        # Pulsante per scaricare i risultati
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            risultati.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="📄 Scarica risultati Excel",
            data=output,
            file_name="risultati_ricerca.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nessun risultato trovato.")

else:
    st.markdown("---")
    st.markdown("### 📄 Fondi disponibili")
    for nome_fondo in fondi:
        if fondi[nome_fondo].empty:
            continue
        st.markdown(f"#### ► {nome_fondo}")
        if st.button(f"Visualizza il fondo '{nome_fondo}'", key=nome_fondo):
            st.markdown("---")
            st.markdown(f"### Archivio: {nome_fondo}")
            st.dataframe(fondi[nome_fondo], use_container_width=True)
