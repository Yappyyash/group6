from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
import socket

def get_mongo_client():
    try:
        client = MongoClient(
            'mongodb+srv://guptarajat2206:qHBUZpZ9f7UCSXH2@cluster0.u3ocn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000  # 5 seconds timeout
        )
        # Attempt a simple operation to confirm connection
        client.admin.command('ping')
        print("Connected to the production MongoDB.")
    except (ConnectionFailure, ConfigurationError, socket.timeout) as e:
        # If connection fails, use the local MongoDB for testing
        print(f"Failed to connect to production MongoDB: {e}")
        client = MongoClient('mongodb://localhost:27017/')
        print("Connected to the local MongoDB for testing.")
    
    return client

# Use the function to get the MongoClient instance
client = get_mongo_client()

# Your database and collection
db = client["MynewDB"]
person_collection = db['user']

