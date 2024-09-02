from pymongo import MongoClient

#For Production
# client = MongoClient(
#     'mongodb+srv://guptarajat2206:qHBUZpZ9f7UCSXH2@cluster0.u3ocn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
#     tls=True,
#     tlsAllowInvalidCertificates=True
# )

#For Testing Purpose
client = MongoClient('mongodb://localhost:27017/')

db = client["MynewDB"]
person_collection = db['user']

