FROM postgres:latest
ENV POSTGRES_DB bot_db
COPY ./init.sh /docker-entrypoint-initdb.d/init.sh
RUN chown postgres /docker-entrypoint-initdb.d/init.sh
RUN chmod +x /docker-entrypoint-initdb.d/init.sh
