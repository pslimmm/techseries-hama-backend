import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

class DatabaseManager():

    # constructor function
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv("DB_URI")
        self.client = None
        self.db = None
    
    
    # starts the connection to the database and initializes 
    # the db variable inside the DatabaseManager class
    async def start_connection(self, db_name: str = "NorthStar"):
        # note to self: NorthStar-techseries-2025 is the cluster name
        try:
            # Create a new client and connect to the server
            self.client: AsyncMongoClient = AsyncMongoClient(self.uri, 
                                server_api=ServerApi(
                                    version="1",                # Stable API version, to ensure consistent responses from the server, even when drivers get updated
                                    strict=True,                # ensure only commands that are part of the declared API version
                                    deprecation_errors=True))   # raises Exception if deprecated commands are called
        
            self.db = self.client[db_name]
            print("yeah it worked")

            return True
        except Exception as e:
            print(e)
            return False

    async def close_connection(self):
        if self.client:
            await self.client.close()
            print("Database Connection Closed")

