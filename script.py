from datetime import datetime
from openpyxl import Workbook
import os
from pathlib import Path
import psycopg2
import shlex
import shutil
from subprocess import Popen

HEROKU_APP = 'cry-wolf'
SNAPSHOTS_DIR = 'snapshots'
PG_USERNAME = 'postgres'
PG_PASSWORD = 'postgres'
PG_HOST = 'localhost'
PG_DATABASE = 'crywolf'

EXCEL_DIR = 'excel'


class User:
    def __init__(self, idnum, username, time_begin, time_end, questionnaire_complete, survey_complete, training_complete):
        self.idnum = idnum
        self.username = username
        self.time_begin = time_begin
        self.time_end = time_end
        self.questionnaire_complete = questionnaire_complete
        self.survey_complete = survey_complete
        self.training_complete = training_complete

    def __repr__(self):
        return f"{self.idnum} {self.username} {self.time_begin} {self.time_end} {self.questionnaire_complete} {self.survey_complete} {self.training_complete}"


def download_and_import():
    # Must have run 'heroku login' from prior to running this script
    Popen(shlex.split(f"heroku pg:backups:capture -a {HEROKU_APP}")).wait()
    Popen(shlex.split(f"heroku pg:backups:download -a {HEROKU_APP}")).wait()

    if not os.path.exists(SNAPSHOTS_DIR):
        os.makedirs(SNAPSHOTS_DIR)
    snapshot = Path(
        SNAPSHOTS_DIR, f'{HEROKU_APP}_{datetime.now().strftime("%Y%m%d_%H-%M-%S")}.dump')
    shutil.copy('latest.dump', snapshot)
    os.remove('latest.dump')

    # Need to set this so Postgres can log in. Not recommended for security reasons on a server.
    # Assumes Postgres is running on localhost
    os.environ["PGPASSWORD"] = PG_PASSWORD
    Popen(shlex.split(
        f"pg_restore --verbose --clean --no-acl --no-owner -h {PG_HOST} -U {PG_USERNAME} -d {PG_DATABASE} {snapshot}")).wait()


def export_excel():
    if not os.path.exists(EXCEL_DIR):
        os.makedirs(EXCEL_DIR)

    connection = psycopg2.connect(user=PG_USERNAME,
                                  password=PG_PASSWORD,
                                  host=PG_HOST,
                                  port="5432",
                                  database=PG_DATABASE)

    with connection as conn:
        cursor = conn.cursor()
        # cursor.execute('select id, username, time_begin, time_end, questionnaire_complete, survey_complete, training_complete from "user"')

        cursor.execute('''SELECT u.*, pqa.* 
            FROM "user" AS u 
            INNER JOIN prequestionnaire_answers as pqa 
            ON u.username = pqa.user''')

        users = cursor.fetchall()
        for u in users:
            print(u[0])

        exit(0)

        excel_file = Path(
            EXCEL_DIR, f'{HEROKU_APP}_{datetime.now().strftime("%Y%m%d_%H-%M-%S")}.xlsx')

        wb = Workbook()
        ws = wb.active
        ws.title = 'users'

        headers = ['id', 'username', 'time_begin', 'time_end',
                   'questionnaire_complete', 'survey_complete', 'training_complete']
        for col in range(len(headers)):
            ws.cell(row=1, column=col+1, value=headers[col])

        row = 2
        for user in users:
            # build user computations here

            for field in range(len(user)):
                ws.cell(row=row, column=field+1, value=user[field])
            row += 1

        wb.save(excel_file)


if __name__ == "__main__":
    # download_and_import()
    export_excel()
