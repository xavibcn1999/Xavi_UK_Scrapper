from pymongo import MongoClient

def main():
    # Conectar al cliente MongoDB
    client = MongoClient('mongodb+srv://xavidb:WrwQeAALK5kTIMCg@serverlessinstance0.lih2lnk.mongodb.net/')
    db = client["Xavi_UK"]
    collection_A = db['Search_uk_A']

    # Eliminar la columna 'Ebay Search URL' de todos los documentos
    result = collection_A.update_many({}, {'$unset': {'Ebay Search URL': ""}})

    print(f"Columna 'Ebay Search URL' eliminada de {result.modified_count} documentos.")

if __name__ == '__main__':
    main()

