# syntax=docker/dockerfile:1
FROM python:3.14-alpine AS base

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY parselibrary/ ./parselibrary/

# Stage 1: UDP Parser Service
FROM base AS udpparser
ENV PYTHONUNBUFFERED=1
CMD ["python", "./parselibrary/udp_parser.py"]

# Stage 2: OPC UA Server Service
FROM base AS opcserver
ENV PYTHONUNBUFFERED=1
CMD ["python", "./parselibrary/opcua_server.py"]

# Stage 3: Watchdog / Helper Service
FROM base AS udphelper
ENV PYTHONUNBUFFERED=1
CMD ["python", "./parselibrary/spectrouv_helper.py"]
