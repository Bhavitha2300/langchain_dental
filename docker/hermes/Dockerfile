FROM eclipse-temurin:21-jre-alpine

ADD https://github.com/wardle/hermes/releases/download/v1.4.1585/hermes-1.4.1585-lucene10.jar /app/hermes.jar

EXPOSE 8080

CMD ["java", "-jar", "/app/hermes.jar", "--db", "/data/snomed.db", "--bind-address", "0.0.0.0", "serve"]