import os
import io
import json
from datetime import datetime
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

FOLDER_ID_PDF = st.secrets["FOLDER_ID_PDF"]

def _load_credentials_json():
    if "GOOGLE_CREDENTIALS" in st.secrets:
        creds_json = st.secrets["GOOGLE_CREDENTIALS"]
        return json.loads(creds_json)
    raise RuntimeError("Credenciais não encontradas em st.secrets.")

@st.cache_resource
def carregar_servico():
    """Carrega o serviço do Drive a partir das credenciais seguras."""
    creds_dict = _load_credentials_json()
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def listar_arquivos_docs():
    """Lista os arquivos Google Docs da pasta do Drive (ordem decrescente)."""
    service = carregar_servico()
    results = service.files().list(
        q=f"'{FOLDER_ID_PDF}' in parents and mimeType='application/vnd.google-apps.document'",
        orderBy="name desc",
        fields="files(id, name, modifiedTime)"
    ).execute()
    return results.get("files", [])


def exportar_pdf(file_id, nome_arquivo):
    """Exporta um Google Docs como PDF e retorna BytesIO + nome do arquivo final (.pdf)."""
    service = carregar_servico()
    request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    nome_pdf = nome_arquivo if nome_arquivo.lower().endswith(".pdf") else nome_arquivo + ".pdf"
    return fh, nome_pdf
