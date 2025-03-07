import logging
import os
from llama_index.text_splitter import TokenTextSplitter, SentenceSplitter
from llama_index import Document, download_loader
from modules.loaders import LOADERS
import yake
import re
import torch
import time


def IndexDocuments(brain, project, documents, splitter = "sentence", chunks = 256):
    if splitter == "sentence":
        splitter_o = TokenTextSplitter(
                separator=" ", chunk_size=chunks, chunk_overlap=30)
    elif splitter == "token":  
        splitter_o = SentenceSplitter(
                separator=" ", paragraph_separator="\n", chunk_size=chunks, chunk_overlap=30)

    for document in documents:
        text_chunks = splitter_o.split_text(document.text)

        doc_chunks = [Document(text=t, metadata=document.metadata) for t in text_chunks]

        for doc_chunk in doc_chunks:
            project.db.insert(doc_chunk)
    
    return len(doc_chunks)


def ExtractKeywordsForMetadata(documents):
    max_ngram_size = 4
    numOfKeywords = 15
    kw_extractor = yake.KeywordExtractor(n=max_ngram_size, top=numOfKeywords)
    for document in documents:
        metadataKeywords = ""
        keywords = kw_extractor.extract_keywords(document.text)
        for kw in keywords:
            metadataKeywords = metadataKeywords + kw[0] + ", "
        document.metadata["keywords"] = metadataKeywords

    return documents


def FindFileLoader(ext, eargs={}):
    if ext in LOADERS:
        loader_name, loader_args = LOADERS[ext]
        loader = download_loader(loader_name)()
        return loader
    else:
        raise Exception("Invalid file type.")


def FindEmbeddingsPath(projectName):
    embeddings_path = os.environ["EMBEDDINGS_PATH"]
    embeddingsPathProject = None

    if not os.path.exists(embeddings_path):
        os.makedirs(embeddings_path)

    project_dirs = [d for d in os.listdir(
        embeddings_path) if os.path.isdir(os.path.join(embeddings_path, d))]

    for dir in project_dirs:
        if re.match(f'^{projectName}_[0-9]+$', dir):
            embeddingsPathProject = os.path.join(embeddings_path, dir)

    if embeddingsPathProject is None:
        embeddingsPathProject = os.path.join(
            embeddings_path, projectName + "_" + str(int(time.time())))
        os.mkdir(embeddingsPathProject)

    return embeddingsPathProject


def loadEnvVars():
    if "RESTAI_NODE" not in os.environ:
        os.environ["RESTAI_NODE"] = "node1"

    if "RESTAI_HOST" not in os.environ:
        os.environ["RESTAI_HOST"] = ".ai.lan"

    if "EMBEDDINGS_PATH" not in os.environ:
        os.environ["EMBEDDINGS_PATH"] = "./embeddings/"

    if "UPLOADS_PATH" not in os.environ:
        os.environ["UPLOADS_PATH"] = "./uploads/"

    if "ANONYMIZED_TELEMETRY" not in os.environ:
        os.environ["ANONYMIZED_TELEMETRY"] = "False"

    if "LOG_LEVEL" not in os.environ:
        os.environ["LOG_LEVEL"] = "INFO"

    os.environ["ALLOW_RESET"] = "true"


def print_cuda_mem():
    print("Allocated: " +
          (torch.cuda.memory_allocated() /
           1e6) +
          "MB, Max: " +
          (torch.cuda.max_memory_allocated() /
           1e6) +
          " MB, Reserved:" +
          (torch.cuda.memory_reserved() /
              1e6) +
          "MB")


def get_logger(name, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler("./logs/" + name + ".log")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
