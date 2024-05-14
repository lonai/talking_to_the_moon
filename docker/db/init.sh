Path_To_Db_Binary=`pg_config --bindir`
Path_To_Db_Config=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW config_file'`
Path_To_Hba=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW hba_file'`
Path_To_Db_Data=`psql -U postgres --no-align --quiet --tuples-only --command='SHOW data_directory'`

sed -i "s/^#*\(log_replication_commands *= *\).*/\1on/" $Path_To_Db_Config
sed -i "s/^#*\(archive_mode *= *\).*/\1on/" $Path_To_Db_Config
sed -i "s|^#*\(archive_command *= *\).*|\1'cp %p /tmp/archive/%f'|" $Path_To_Db_Config
sed -i "s/^#*\(max_wal_senders *= *\).*/\110/" $Path_To_Db_Config
sed -i "s/^#*\(wal_level *= *\).*/\1replica/" $Path_To_Db_Config
sed -i "s/^#*\(wal_log_hints *= *\).*/\1on/" $Path_To_Db_Config
sed -i "s/^#*\(logging_collector *= *\).*/\1on/" $Path_To_Db_Config
sed -i -e"s/^#log_filename = 'postgresql-\%Y-\%m-\%d_\%H\%M\%S.log'.*$/log_filename = 'postgresql.log'/" $Path_To_Db_Config
sed -i "s/#log_line_prefix = '%m \[%p\] '/log_line_prefix = '%m [%p] %q%u@%d '/g" $Path_To_Db_Config

mkdir -p /tmp/archive
psql -c "CREATE USER $DB_REPL_USER WITH REPLICATION LOGIN PASSWORD '$DB_REPL_PASSWORD';" 
psql -c "CREATE DATABASE $DB_DATABASE;" 
psql -d $DB_DATABASE -a -f /init.sql 
psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 
psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_DATABASE TO $DB_USER;" 
psql -d $DB_DATABASE -c "ALTER TABLE email OWNER TO $DB_USER;" 
psql -d $DB_DATABASE -c "ALTER TABLE phone OWNER TO $DB_USER;" 
psql -d db_bot -c "GRANT EXECUTE ON FUNCTION pg_current_logfile() TO $DB_USER;" 
psql -d db_bot -c "GRANT EXECUTE ON FUNCTION pg_read_file(text) TO $DB_USER;"

echo "host replication $DB_REPL_USER 0.0.0.0/0 trust" >> $Path_To_Hba 
echo "host all $DB_USER bot trust" >> $Path_To_Hba

/$Path_To_Db_Binary/pg_ctl restart -D $Path_To_Db_Data
