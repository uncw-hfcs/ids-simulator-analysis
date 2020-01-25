import os
import shlex
import shutil
from datetime import datetime
from pathlib import Path
from subprocess import Popen


def download_and_import(heroku_app, snapshots_dir, pg_password, pg_host, pg_username, pg_database):
    # Download the database dump
    Popen(shlex.split(f"heroku pg:backups:capture -a {heroku_app}")).wait()
    Popen(shlex.split(f"heroku pg:backups:download -a {heroku_app}")).wait()

    # copy it to snapshots folder and timestamp it
    if not os.path.exists(snapshots_dir):
        os.makedirs(snapshots_dir)
    snapshot = Path(
        snapshots_dir, f'{heroku_app}_{datetime.now().strftime("%Y%m%d_%H-%M-%S")}.dump')
    shutil.copy('latest.dump', snapshot)
    os.remove('latest.dump')

    # Need to set this so Postgres can log in. Not recommended for security reasons on a server.
    # Assumes Postgres is running on localhost
    os.environ["PGPASSWORD"] = pg_password

    # Do the import using the pg_restore tool
    Popen(shlex.split(
        f"pg_restore --verbose --clean --no-acl --no-owner -h {pg_host} -U {pg_username} -d {pg_database} {snapshot}")).wait()

    print(
        f"Run the following from .venv terminal: sqlacodegen postgresql:///{pg_database} --outfile models.py")


if __name__ == "__main__":
    HEROKU_APP = 'cry-wolf'
    SNAPSHOTS_DIR = 'snapshots'
    PG_USERNAME = 'postgres'
    PG_PASSWORD = 'postgres'
    PG_HOST = 'localhost'
    PG_DATABASE = 'crywolf'
    download_and_import(heroku_app='cry-wolf',
                        snapshots_dir='snapshots',
                        pg_password='postgres',
                        pg_host='localhost',
                        pg_username='postgres',
                        pg_database='crywolf')
