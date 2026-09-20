import vertexai
from vertexai.preview import rag

CORPUS_NAME = "projects/472679648067/locations/us-central1/ragCorpora/1931437309723410432"

vertexai.init(project="qwiklabs-gcp-02-7b95af39ea22", location="us-central1")

try:
    resp = rag.retrieval_query(
        text="herb for stomach headache digestion",
        rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
        rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
    )
    contexts = getattr(resp.contexts, "contexts", [])
    print("Passages retrieved count:", len(contexts))
    for i, c in enumerate(contexts, 1):
        print(f"\n--- Context {i} ---")
        print(c.text[:300])
except Exception as e:
    print("Retrieval query error:", e)
