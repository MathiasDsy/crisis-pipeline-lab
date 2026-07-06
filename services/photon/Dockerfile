FROM eclipse-temurin:21-jre

WORKDIR /app

RUN apt-get update && \
    apt-get install -y wget curl zstd && \
    rm -rf /var/lib/apt/lists/*

RUN wget -O /app/photon.jar \
    https://github.com/komoot/photon/releases/download/1.2.1/photon-1.2.1.jar

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 2322

ENTRYPOINT ["/app/entrypoint.sh"]