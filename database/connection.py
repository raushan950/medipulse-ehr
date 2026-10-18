"""
Database Connection Management using PyMongo
CSE494: Intelligent NoSQL Databases
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys
import logging
from config import MONGODB_URI, DATABASE_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MediPulseDB")

_client = None

def get_mongo_client(uri: str = MONGODB_URI) -> MongoClient:
    """
    Returns a singleton MongoClient instance with connection pooling.
    """
    global _client
    if _client is None:
        try:
            logger.info(f"Connecting to MongoDB at: {uri}")
            _client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=5
            )
            # Trigger server connection check
            _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB server.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            logger.error(f"MongoDB connection failed: {err}")
            raise
    return _client

def get_database(db_name: str = DATABASE_NAME):
    """
    Returns the MediPulse database instance.
    """
    client = get_mongo_client()
    return client[db_name]

def close_connection():
    """Closes the client connection gracefully."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")
