from pymongo import MongoClient
client = MongoClient()
db = client.test_database
collection = db.update_try

import datetime
x = 25
y = 'fuck'
list_ = [i for i in range(10)]
post = {"author": "Mikewww",
        "text": "My first blog post!",
        "tags": ["mongodb", "python", "pymongo"],
        "date": datetime.datetime.utcnow(),
        "fuu":list_}
new_tst = {"author": "fuck",
        "text": "My first blog dog!",
        "tags": ["mongodb", "python", "pymongo"],
        "date": datetime.datetime.utcnow(),
        "fuu":list_}
posts = db.posts
post_id = posts.insert_one(post).inserted_id
params = db.params
params.update_one({ '_id': 12345 },{"$set": new_tst},upsert=True)
# print(parameters_db.find_one({'_id': chat_id}))
# params = parameters_db.find_one({'_id': chat_id})