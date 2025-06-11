from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores.types import MetadataInfo, VectorStoreInfo
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core.postprocessor import SentenceTransformerRerank

from llama_index.core import get_response_synthesizer



def query_job_posts(query):
    # Define additional information about the metadata which the LLM can use to infer the metadata filters
    vector_store_info = VectorStoreInfo(
        content_info="Names of the Kaggle competitions",
        metadata_info=[
            MetadataInfo(
                name="competition_title",
                type="str",
                description=("Name of the Kaggle competition.")
            )
        ],
    )

  

    # Set up the VectorIndexAutoRetriever
    retriever = VectorIndexAutoRetriever(
        index,
        llm =LLama(api_key) ,
        vector_store_info=vector_store_info,
        similarity_top_k = 4,
        vector_store_query_mode="hybrid",
        alpha=0.5,
        verbose=True
    )

    query = "a job post about AI/Ml software engineer in california requiring only Bachelor’s degree in Computer Science"
    response = retriever.retrieve(query)



    # BAAI/bge-reranker-base
    # link: https://huggingface.co/BAAI/bge-reranker-base
    rerank = SentenceTransformerRerank(
        top_n = 2, 
        model = "BAAI/bge-reranker-base"
    )

    job_search_prompt_tmpl = PromptTemplate(job_search_prompt_tmpl_str)

    # Define response synthesizer
    response_synthesizer = get_response_synthesizer(text_qa_template = job_search_prompt_tmpl)

    # assemble query engine
    advanced_rag_query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors = [rerank],
    )

    return advanced_rag_query_engine._response_synthesizer._llm

