from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi import Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.database import DatabaseManager
from backend.chatbot.src.chatbot import DocumentChatbot
from backend.parse_files_to_text.parse_files import extract_text
from backend.models import ChatbotInit, ChatbotMessage
# ^^ models = pydantic data validation

# Creates a new DatabaseManager object
dbMgr = DatabaseManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await dbMgr.start_connection("NorthStar")
    yield
    # shutdown
    await dbMgr.close_connection()

app = FastAPI(lifespan=lifespan)

async def get_db():
    return dbMgr.db

# comment out during testing to prevent connection errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# endpoint to initialize new chat, refer to ChatbotInit in models.py to know what it takes in as params
@app.post("/chatbot/init/")
async def initiate_chat(init: ChatbotInit, db=Depends(get_db)):

    # this indicates if you need to retrieve data from the localstorage or not (history)
    needsRetrieve = False
    init_msg = ""
 
    # this condition is met when user presses (access previous page)
    if init.newSessionId == "" and init.oldSessionId != "":
        # idk how to validate this with the frontend
        init_msg = ""
        needsRetrieve = True

    # this condition is met if 
    elif init.newSessionId != "":
            await db["bot-state"].delete_many({'sessionId': init.oldSessionId})

            messages = {
                "fp": "Hello, paano kita matutulungan ngayon?",
                "hd": "नमस्ते, मैं आज आपकी सहायता कैसे करूं?",
                "id": "Halo, ada yang bisa saya bantu hari ini?",
                "my": "Hello, bagaimana saya boleh membantu anda hari ini?",
                "bl": "হ্যালো, আজ আমি আপনাকে কিভাবে সাহায্য করতে পারি?"
            }   

            init_msg = messages.get(init.lang, "")

            payload = {
                'sessionId': init.newSessionId,
                'chunks': [],
                'lang': init.lang,
                'translated_doc': ""
            }
            await db["bot-state"].insert_one(payload)

    return {"retrieveLocalStorage": needsRetrieve, "message": init_msg}

@app.post("/chatbot/summary/")
async def get_summary(lang: str, sessionId: str, file : UploadFile = File(...), db=Depends(get_db)):
    # the params above cannot be replaced by a Pydantic model because it is not JSON being posted to this endpoint

    bot = DocumentChatbot(lang)
    # doc = await db["bot-state"].find_one({"sessionId": sessionId}) tf?
    # if doc is not None:
        
    text = await extract_text(file)
    
    # note the IngestedText BaseModel in backend/models.py
    ingested_data = {
        "chunks": [],
        "doc": text,
        "translate": True
    }

    bot_data = bot.ingest_text(ingested_data)
    translated_doc = bot_data['translated_doc']
    chunks = bot_data['chunks']
    summary = bot.initial_summary()
    
    data = {
        'sessionId': sessionId,
        'chunks' : chunks,
        'translated_doc' : translated_doc,
        'lang': lang
    }

    await db["bot-state"].insert_one(data)

    returned_data = {
        "translated_doc": translated_doc,
        "doc_summary": summary
    }

    return returned_data

@app.post("/chatbot/msg/")
async def answer_msg(req: ChatbotMessage, db=Depends(get_db)):
    bot = DocumentChatbot(req.lang)

    doc = await db["bot-state"].find_one({"sessionId": req.sessionId})

    response = ""

    if doc:
        # ingest initial data
        init_ingested_data = {
            "chunks": doc['chunks'],
            "doc": doc['translated_doc'],
            "translate": False
        }
        bot_data1 = bot.ingest_text(init_ingested_data)
        translated_doc = bot_data1['translated_doc']
        chunks = bot_data1['chunks']

        new_ingested_data = {
            'chunks': chunks,
            'doc': req.last_message,
            'translate': False
        }

        bot_data2 = bot.ingest_text(new_ingested_data)
        translated_doc = bot_data2['translated_doc']
        chunks = bot_data2['chunks']

        response = bot.chat(req.message)

        payload = {
            "lang": req.lang,
            "translated_doc": translated_doc,
            "sessionId": req.sessionId,
            "chunks": chunks
        }

        await db['bot-state'].update_one(
            {'sessionId': req.sessionId},                   # filter
            {"$set": payload}  # overwrite array
            )
    
    return {"message": response}