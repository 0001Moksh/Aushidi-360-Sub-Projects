# import pandas as pd
# df = pd.read_excel('medicine_data.xlsx')
# # df = pd.read_excel('medicinces_updated_oct.xlsx')
# print(df.head(1))
# print(df.columns)
# print(len(df))
# # print(df.isnull().sum())

# # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.

# from pymongo import MongoClient

# # Replace this with your actual password
# password = "moksh0001"

# uri = f"mongodb+srv://moksh:{password}@cluster0.6ty3pnm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# client = MongoClient(uri)

# db = client["medicine_db"]
# collection = db["oct_medicines"]

# import pandas as pd
# df = pd.read_excel('medicine_data.xlsx')

# records = df.to_dict('records')

# collection.insert_many(records)

# print(f"{len(records)} medicine records inserted into MongoDB collection 'oct_medicines'")


## >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
