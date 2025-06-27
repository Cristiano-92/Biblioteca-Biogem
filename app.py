import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import base64

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

# Funzione per mostrare un fondo con schede libro
def visualizza_fondo(nome_fondo, df):
    st.markdown(f"## Archivio: {nome_fondo}")
    for _, row in df.iterrows():
        titolo = str(row[0]).strip() if not pd.isna(row[0]) else ""
        autore = str(row[1]).strip() if not pd.isna(row[1]) else ""
        editore_anno = str(row[2]).strip() if not pd.isna(row[2]) else ""
        collocazione = str(row[3]).strip() if not pd.isna(row[3]) else ""

        if titolo and autore and editore_anno and collocazione:
            st.markdown(
                f"""
                <div style='border: 1px solid #ccc; border-left: 4px solid #e66100; padding: 10px; margin-bottom: 10px; background-color: #fefefe; border-radius: 6px;'>
                    <h4 style='margin: 0; color: #e66100;'>{titolo}</h4>
                    <p style='margin: 4px 0;'><strong>{autore}</strong></p>
                    <p style='margin: 4px 0;'>📍 {editore_anno}</p>
                    <p style='margin: 4px 0;'>Collocazione: <code>{collocazione}</code></p>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif titolo:
            st.markdown(
                f"""
                <div style='padding: 8px; margin-top: 20px; margin-bottom: 6px; background-color: #f0f0f0; border-left: 4px solid #bbb; border-radius: 4px;'>
                    <strong>{titolo}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

# Funzione per convertire immagine locale in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Logo codificato in base64
logo_base64 = get_base64_image("biogem-logo.png")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="data:image/png;base64,{logo_base64}" width="80" style="margin: 0;">
        <h1 style="margin: 0; font-size: 2.5em;">Biblioteca Fondazione Biogem</h1>
    </div>
    """,
    unsafe_allow_html=True
)

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

set_blurred_background("biblioteca.jpeg")

@st.cache_data
def carica_fondi():
    xls = pd.ExcelFile("Elenco interno - 16-06-2025.xlsm")
    fondi = {}
    for nome in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=nome, dtype=str, header=2)
            fondi[nome] = df
        except:
            continue
    return fondi

fondi = carica_fondi()

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
            if df_copia.shape[1] > 4:
                condizioni.append(
                    df_copia.iloc[:, 4].astype(str).str.lower().str.contains(parola_chiave.lower())
                )

        if condizioni:
            filtro = condizioni[0]
            for cond in condizioni[1:]:
                filtro = filtro & cond
            risultati.append(df_copia[filtro])

    return pd.concat(risultati) if risultati else pd.DataFrame()

if query or parola_chiave:
    st.markdown("---")
    st.markdown("### 📃 Risultati della ricerca")
    risultati = cerca(fondi, query, parola_chiave)

    if not risultati.empty:
        for _, riga in risultati.iterrows():
            titolo = str(riga.iloc[0]).strip() if not pd.isna(riga.iloc[0]) else "Titolo non disponibile"
            autore = str(riga.iloc[1]).strip() if not pd.isna(riga.iloc[1]) else ""
            collocazione = str(riga.iloc[3]).strip() if len(riga) > 3 and not pd.isna(riga.iloc[3]) else ""

            with st.container():
                st.markdown(
                    f"""
                    <div style='border:1px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px'>
                        <b>Titolo:</b> {titolo}<br>
                        <b>Autore:</b> {autore}<br>
                        <b>Fondo:</b> {riga['_Fondo']}<br>
                        <b>Collocazione:</b> {collocazione}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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
        with st.expander(f"► {nome_fondo}", expanded=False):
            visualizza_fondo(nome_fondo, fondi[nome_fondo])
