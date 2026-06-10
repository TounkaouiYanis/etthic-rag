import os
import asyncio
import anthropic
import streamlit as st
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy

load_dotenv()

COLLECTION = "etthic-docs"
zclient = AsyncZeroEntropy()
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def chercher(question):
    response = await zclient.queries.top_snippets(
        collection_name=COLLECTION,
        query=question,
        k=5,
        precise_responses=True,
    )
    return response.results

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

Question : {question}

Extraits des documents :
{contexte}"""
        }]
    )
    return message.content[0].text

st.title("ETThic — Assistant Documents")
st.caption("Posez vos questions sur vos documents indexés")

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