import os
import base64
import asyncio
import anthropic
import streamlit as st
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy

load_dotenv()

COLLECTION = "etthic-docs"
zclient = AsyncZeroEntropy()
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MOT_DE_PASSE = "etthic2025"

# Protection mot de passe
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

if not st.session_state.authentifie:
    st.title("ETThic — Accès sécurisé")
    mdp = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if mdp == MOT_DE_PASSE:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    st.stop()

async def chercher(question):
    response = await zclient.queries.top_snippets(
        collection_name=COLLECTION,
        query=question,
        k=5,
        precise_responses=True,
    )
    return response.results

async def indexer_pdf(nom_fichier, contenu_bytes):
    b64 = base64.b64encode(contenu_bytes).decode()
    try:
        await zclient.documents.add(
            collection_name=COLLECTION,
            path=nom_fichier,
            content={"type": "auto", "base64_data": b64},
        )
        return True
    except Exception as e:
        return str(e)

def repondre(question):
    snippets = asyncio.run(chercher(question))
    if not snippets:
        return "Aucun passage pertinent trouvé dans les documents."
    contexte = ""
    for i, s in enumerate(snippets):
        contexte += f"\n---\nExtrait {i+1} (source: {s.path}, pages {s.page_span}):\n{s.content}\n"
    message = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Tu es un assistant expert en finance et juridique pour un cabinet de conseil.
Réponds à la question en te basant uniquement sur les extraits fournis.
Cite toujours la source (nom du document et numéro de page).
Si tu ne trouves pas la réponse dans les extraits, dis-le explicitement sans inventer.

Question : {question}

Extraits des documents :
{contexte}"""
        }]
    )
    return message.content[0].text

st.title("ETThic — Assistant Documents")
st.caption("Posez vos questions sur vos documents indexés")

# Section upload
with st.expander("📂 Ajouter un document"):
    fichier = st.file_uploader("Choisir un PDF", type="pdf")
    if fichier and st.button("Indexer ce document"):
        with st.spinner("Indexation en cours..."):
            resultat = asyncio.run(indexer_pdf(fichier.name, fichier.read()))
            if resultat is True:
                st.success(f"✅ {fichier.name} indexé avec succès")
            else:
                st.error(f"Erreur : {resultat}")

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Posez votre question...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours..."):
            reponse = repondre(question)
        st.write(reponse)
    st.session_state.messages.append({"role": "assistant", "content": reponse})