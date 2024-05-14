FROM postgres:latest
COPY ./init.sh /docker-entrypoint-initdb.d/init.sh
COPY ./init.sql /init.sql
RUN chown postgres /docker-entrypoint-initdb.d/init.sh
RUN chmod ugo+x /docker-entrypoint-initdb.d/init.sh