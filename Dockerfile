FROM python: 3 AS filemanager

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache -r requirements.txt

COPY . . 

CMD ["python", "./parselibrary/ftp_filemanagement.py"]

FROM python:3 AS opcserver

WORKDIR /app

COPY requirements.txt ./ 
RUN pip install --no-cache -r requirements.txt 

COPY . . 

CMD ["python", "./parselibrary/opcua_server.py"]

FROM python:3 AS ftpserver

WORKDIR /app

COPY requirements.txt ./ 
RUN pip install --no-cache -r requirements.txt 

COPY . . 

USER root 
CMD ["python", "./ftpserver/ftp_server.py"]
