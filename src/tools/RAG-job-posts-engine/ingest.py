import sys
import os

import csv
from jobspy import scrape_jobs
import pandas as pd

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.weaviate import WeaviateVectorStore

from flask import current_app

from vector_store import connect_to_vector_store


def scrape_jobs(tech_specialties, locations):
    all_jobs = []
    for country, location in locations.items():
        for specialty in tech_specialties:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=specialty,
                location=location,
                results_wanted=15,  # Limit to 15 per specialty per location
                hours_old=72,  # Jobs posted in the last 3 days
                country_indeed=country,
                linkedin_fetch_description=True,  # Fetch job descriptions
            )
            all_jobs.extend(jobs.to_dict(orient="records"))

    fieldnames = all_jobs[0].keys() if all_jobs else []
    if all_jobs:
        with open("tech_jobs_dataset.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_NONNUMERIC,
                escapechar="\\",
            )
            writer.writeheader()
            writer.writerows(all_jobs)
        print(f"Saved {len(all_jobs)} job postings to tech_jobs_dataset.csv")
    else:
        print("No job postings found.")


def load_data(filepath):
    """Load and preprocess CSV data"""
    df = pd.read_csv(filepath)
    df = df.dropna(subset=["job_url", "title"])
    df = df.iloc[:2]  # Limit to 2 job posts for testing
    return df


def preprocess_data(df):
    """Convert job posts into documents"""
    documents = [
        Document(
            text=row["description"],
            metadata={
                key: row[key]
                for key in [
                    "title",
                    "company",
                    "location",
                    "job_url",
                    "job_type",
                    "date_posted",
                    "company_industry",
                ]
                if pd.notna(row[key])
            },
        )
        for _, row in df.iterrows()
    ]

    return documents


def chunk_documents(documents):
    parser = SentenceSplitter(chunk_size=300, chunk_overlap=20)
    nodes = parser.get_nodes_from_documents(documents)

    print(f"Created {len(nodes)} nodes from {len(documents)} documents")

    for i in range(5):
        print(f"Chunk {i}:")
        print("Text:")
        print(nodes[i].text)
        print("------------------")
        print(f"Job post title: {nodes[i].metadata['title']}\n")

    return nodes


def update_vector_store(nodes):

    # Initialize Weaviate client with embedded options
    client = weaviate.WeaviateClient(
        embedded_options=EmbeddedOptions(
            hostname="localhost",
            port=8080,
            persistence_data_path="./weaviate_data"
        )
    )

    # Connect to Weaviate (important step)
    client.connect()

    # Verify connection
    if client.is_ready():
        print("✅ Connected to Weaviate (v4) in embedded mode.")
    else:
        print("❌ Failed to connect. Check logs below:")
        print(client.get_meta())  # Provides metadata for troubleshooting
        
    


    index_name = "JobPosts"

    # 1️⃣ Construct vector store
    vector_store = WeaviateVectorStore(
        weaviate_client=client, 
        index_name=index_name
    )

    # 2️⃣ Set up storage context for embeddings
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 3️⃣ Delete existing index (if exists) - v4 uses `collections`
    if client.collections.exists(index_name):
    client.collections.delete(index_name)
    print(f"🗑️ Deleted existing collection: {index_name}")

    # 4️⃣ Create VectorStoreIndex (handles chunking + embeddings)
    index = VectorStoreIndex(
        nodes,  
        storage_context=storage_context,
    )


    return index


if __name__ == "__main__":
    df = load_data("../../../data/jobs-reserve.csv")
    documents = preprocess_data(df)
    nodes = chunk_documents(documents)
    index = update_vector_store(nodes)


