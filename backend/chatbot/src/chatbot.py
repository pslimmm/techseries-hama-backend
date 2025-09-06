import json
import pathlib
from typing import List
from backend.chatbot.src.chunker import chunk_text
from backend.chatbot.src.retriever import BM25Retriever
from backend.models import IngestedText
from backend.chatbot.src.translator import translate_text, answer_from_context
from backend.chatbot.src.prompts import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_PROMPT, CHAT_SYSTEM_PROMPT, CHAT_USER_PROMPT
import backend.chatbot.src.config as config

class DocumentChatbot:
    def __init__(self, t):
        self.target_language: str = config.TARGET_LANGUAGE.get(t, "English")
        self.translated_doc: str = ""
        self.chunks: List[str] = []
        self.retriever: BM25Retriever = None

    def clean_output(self, s: str) -> str:
        return (s or "").replace("**", "").strip()

    def read_txt_files_from_data_raw(self) -> List[str]:
        root = pathlib.Path(config.DATA_RAW_DIR)
        json_path = pathlib.Path(__file__).parent.parent / root / "data.json"
        target_lang = config.TARGET_LANGUAGE.get(self.target_language, "English")
        translate_mode = config.TRANSLATE_DATA_RAW

        if not json_path.exists():
            return []

        chunks = []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # prepare texts first
            texts = [entry.get("info") for entry in data if entry.get("info")]

            # bulk translate 
            if translate_mode:
                texts = [translate_text(t, target_lang) or t for t in texts]

            # chunk in one pass
            chunks = [c for text in texts for c in chunk_text(text, max_chars=1000, overlap=200) if len(c) > 10]

        except Exception as e:
            print(f"Error reading or processing JSON: {e}")
        return chunks
    
    # main functions:

    # translate the document
    def ingest_text(self, data: IngestedText) -> str:
        # how to use:
        # support_chunks is the data from MOM and other sources that we have gathered
        # "doc_chunks" are chunks from data that we submit to the bot, like parsed text from a document
        # OR any relevant information, e.g. the previous response of the bot
        # ^^ for doc, you can pass the {parsed text of a document} or can pass in the {{previous response of the bot}}

        # data is a 3 key dict
        # {chunks: [], doc: str, translate: boolean} 

        # chunks can be empty[] or filled, chunks are stored in the db

        # doc: you can pass the {{parsed text of a document}} or can pass in the {{previous response of the bot}} to 
        # provide more context to the bot

        # translate is a boolean value that indicates if you want a translated document or not 
        # ^^ slight modification to the code; ONLY use [[translate]] when you are using ingest text to get the translated doc
        
        # who designed this? idk, but it works

        return_dict = {}

        doc_chunks = []
        uploaded_txt = data["doc"]

        if data['translate']:
            self.translated_doc = translate_text(uploaded_txt, self.target_language) or uploaded_txt
            doc_chunks = chunk_text(self.translated_doc, max_chars=1000, overlap=200)
        else:
            doc_chunks = chunk_text(uploaded_txt, max_chars=1000, overlap=200)

        support_chunks = data['chunks'] or self.read_txt_files_from_data_raw()
        self.chunks = doc_chunks + support_chunks
        self.retriever = BM25Retriever(self.chunks) if self.chunks else None

        return_dict = {
            "translated_doc": self.translated_doc,
            "chunks": self.chunks   # source chunks + context chunks
        }
        return return_dict

    # summarize the document
    def initial_summary(self) -> str:
        user_prompt = SUMMARY_USER_PROMPT.format(doc=self.translated_doc, target_language=self.target_language)
        raw = answer_from_context(SUMMARY_SYSTEM_PROMPT.format(target_language=self.target_language), user_prompt)
        return self.clean_output(raw)

    # chat the bot
    def chat(self, question: str) -> str:
        if self.retriever:
            top = self.retriever.retrieve(question, k=8)
            context_snippets = "\n\n---\n".join(top)
        else:
            context_snippets = self.translated_doc
        user_prompt = CHAT_USER_PROMPT.format(question=question, context=context_snippets)
        raw = answer_from_context(CHAT_SYSTEM_PROMPT.format(target_language=self.target_language), user_prompt)
        ans = self.clean_output(raw)
        return ans
