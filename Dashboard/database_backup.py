import sqlite3
import subprocess
def backup_database(source_db_path, backup_db_path):
    try:
        with sqlite3.connect(source_db_path) as source_conn:
            with sqlite3.connect(backup_db_path) as backup_conn:
                source_conn.backup(backup_conn)
        print(f"Backup successful: {backup_db_path}")
    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
def transfer_backup(backup_path, target_user, target_host, target_path):
    try:
        subprocess.run(
            ["scp", backup_path, f"{target_user}@{target_host}:{target_path}"],
            check=True
        )
        print(f"Backup transferred successfully to {target_host}:{target_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error transferring backup: {e}")

''

backup_database("./home/imamu/website/database/chair.sqlite", "./home/imamu/website/database_backup/chair_backup_sqlite")
transfer_backup("./home/imamu/website/database_backup/chair_backup_sqlite", "martin", "192.168.2.4", "./home/martin/database_backup")
