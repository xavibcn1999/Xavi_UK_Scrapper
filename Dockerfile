# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos y lo instala
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Añade el directorio de Python bin al PATH
ENV PATH="/app/python/bin:$PATH"

# Comando para ejecutar Scrapy
CMD ["scrapy", "crawl", "ebay_top2"]
