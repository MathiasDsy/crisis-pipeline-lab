FROM eclipse-temurin:17-jre

WORKDIR /app

COPY photon-0.7.3.jar /app/photon.jar

EXPOSE 2322

CMD ["java", "-jar", "/app/photon.jar", "-data-dir", "/data"]