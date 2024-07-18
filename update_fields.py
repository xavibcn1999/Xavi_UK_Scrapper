from pymongo import MongoClient

# Conectar a la base de datos
client = MongoClient('mongodb+srv://xavidb:WrwQeAALK5kTIMCg@serverlessinstance0.lih2lnk.mongodb.net/')
db = client["Xavi_UK"]
collection_A = db['Search_uk_A']

# Recorrer cada documento en la colección
for document in collection_A.find({}):
    # Actualizar los campos
    new_values = {
        "Amazon Image URL": document.get("Ebay Image URL", ""),
        "Amazon Product Title": document.get("Ebay Product Title", "")
    }
    # Eliminar los campos antiguos
    unset_values = {
        "Ebay Image URL": "",
        "Ebay Product Title": ""
    }
    # Actualizar el documento en la colección
    collection_A.update_one({"_id": document["_id"]}, {"$set": new_values, "$unset": unset_values})

print("Actualización completada.")
