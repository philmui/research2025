from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import asyncio
from llama_index.core import (
    PromptTemplate,
    Settings,
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.tools import QueryEngineTool, ToolMetadata
import sys
import warnings
import logging
from IPython.display import clear_output

FILE_NAME = "HAI_AI-Index-Report-2024.pdf"
STORAGE_DIR = "../storage/hai"

hai_engine = None

async def setup():
    warnings.filterwarnings('ignore')
    logging.getLogger().setLevel(logging.ERROR)

    llm = Ollama(model="llama3.2:3b-instruct-q8_0", temperature=0.01)
    embedding = OllamaEmbedding(model_name="mxbai-embed-large")

    Settings.llm = llm
    Settings.embed_model = embedding

    try:
        storage_context = StorageContext.from_defaults(
            persist_dir = STORAGE_DIR
        )
        hai_index = load_index_from_storage(storage_context=storage_context)
    except:
        hai_report = SimpleDirectoryReader(
            input_files=[f"../data/{FILE_NAME}"]
        ).load_data()
        
        hai_index = VectorStoreIndex.from_documents(
            hai_report
        )
        hai_index.storage_context.persist(persist_dir=STORAGE_DIR)
    
    global hai_engine
    hai_engine = hai_index.as_chat_engine(
        chat_mode=ChatMode.BEST,
    )
    
async def main():
    
    query_str = input("==> What question do you have about the HAI 2024 report? ")
    while len(query_str.strip()) > 0:
        response = await hai_engine.achat("What is the general trend of A.I. in 2024 and beyond? ")
        print(f"\n\tAgent Response: {response.response}")
        query_str = input("\n==> What question do you have about the HAI 2024 report?")
    
    print("\nThank you for using this awesome tool!!! 👍")
    
if __name__ == "__main__":
    asyncio.run(setup()) 
    asyncio.run(main())