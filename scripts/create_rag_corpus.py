import sys
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-02-7b95af39ea22"
LOCATION = "us-central1"
GCS_PATH = "gs://smart-pantry-media-qwiklabs-gcp-02-7b95af39ea22/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, medicinal herbs, plants, and recipes described in this text. "
    "Ignore and omit all metadata, license boilerplate, and image captions. "
    "Output clean, self-contained prose."
)


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Configuring serverless mode in us-central1...")
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("Serverless RAG engine mode configured successfully.")
    except Exception as e:
        print(f"Warning updating rag_engine_config (may already be set): {e}")

    print("Creating RAG corpus...")
    corpus = rag.create_corpus(
        display_name="complete-herbal-gutenberg-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print("CORPUS_NAME:", corpus.name)

    print("Importing file from GCS...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-1.5-flash-001",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print("Import completed! Files imported count:", getattr(resp, "imported_rag_files_count", 1))


if __name__ == "__main__":
    main()
