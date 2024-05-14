sleep 20

Path_To_Db_Binary=`pg_config --bindir`
Path_To_Db_Data=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW data_directory'`

/$Path_To_Db_Binary/pg_ctl stop -D $Path_To_Db_Data
rm -rf /var/lib/postgresql/data/*
pg_basebackup -R -h db -U $DB_REPL_USER -D /var/lib/postgresql/data -P
/$Path_To_Db_Binary/pg_ctl start -D $Path_To_Db_Data
