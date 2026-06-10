import os
import base64
import asyncio
from dotenv import load_dotenv
from zeroentropy import AsyncZeroEntropy, ConflictError

load_dotenv()

COLLECTION = "etthic-docs"
zclient = AsyncZeroEntropy()

async def main():
    # Créer la collection
    try:
        await zclient.collections.add(collection_name=COLLECTION)
        print("Collection créée.")
    except ConflictError:
        print("Collection déjà existante.")

    # Indexer les PDFs
    dossier = "documents"
    fichiers = [f for f in os.listdir(dossier) if f.endswith(".pdf")]

    if not fichiers:
        print("Aucun PDF trouvé dans /documents")
        return

    for fichier in fichiers:
        chemin = os.path.join(dossier, fichier)
        b64 = base64.b64encode(open(chemin, "rb").read()).decode()

        print(f"Indexation de {fichier}...")
        await zclient.documents.add(
            collection_name=COLLECTION,
            path=fichier,
            content={"type": "auto", "base64_data": b64},
        )
        print(f"{fichier} envoyé. En attente d'indexation...")

        # Attendre que le doc soit indexé
        while True:
            info = await zclient.documents.get_info(
                collection_name=COLLECTION, path=fichier
            )
            status = info.document.index_status
            print(f"  Status : {status}")
            if status == "indexed":
                print(f"  ✅ {fichier} indexé avec succès.")
                break
            elif "failed" in status:
                print(f"  ❌ Échec : {status}")
                break
            await asyncio.sleep(2)

asyncio.run(main())