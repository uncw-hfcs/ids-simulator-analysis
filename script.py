from datetime import datetime
from openpyxl import Workbook
import os
from pathlib import Path
import psycopg2
import shlex
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from subprocess import Popen

MODEL_FILE = 'models.py'
HEROKU_APP = 'cry-wolf'
SNAPSHOTS_DIR = 'snapshots'
PG_USERNAME = 'postgres'
PG_PASSWORD = 'postgres'
PG_HOST = 'localhost'
PG_DATABASE = 'crywolf'

EXCEL_DIR = 'excel'


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

    print(f"Run the following from .venv terminal: sqlacodegen postgresql:///{PG_DATABASE} --outfile models.py")
    

def _to_dict(model):
    d = model.__dict__
    d.pop('_sa_instance_state', None)
    return d


def export_excel():
    from models import User, Event, EventDecision

    engine = create_engine(f'postgresql+psycopg2://{PG_USERNAME}:{PG_PASSWORD}@{PG_HOST}/{PG_DATABASE}')
    Session = sessionmaker(bind=engine)
    session = Session()


    if not os.path.exists(EXCEL_DIR):
        os.makedirs(EXCEL_DIR)

    connection = psycopg2.connect(user=PG_USERNAME,
                                  password=PG_PASSWORD,
                                  host=PG_HOST,
                                  port="5432",
                                  database=PG_DATABASE)

    events = { e.id : _to_dict(e) for e in session.query(Event) }
    users = { u.username : _to_dict(u) for u in session.query(User) }
    for username in users.keys():
        decisions = [ _to_dict(d) for d in session.query(EventDecision).filter_by(user=username)]

        # For each decision, determine if it is correct and a TP/FP/TN/FN
        for d in decisions:
            # Check events are 74, 75
            # "should_escalate" = 1 for TP, 0 for TN
            d['TP'] = False
            d['FP'] = False
            d['TN'] = False
            d['FN'] = False
            should_escalate = True if events[d['event_id']]['should_escalate'] == '1' else False 
            if should_escalate and d['escalate'] == "Escalate":
                d['TP'] = True
                d['correct?'] = True
            elif should_escalate and d['escalate'] == "Don't escalate":
                d['FN'] = True
                d['correct?'] = False
            elif not should_escalate and d['escalate'] == "Don't escalate":
                d['TN'] = True
                d['correct?'] = True            
            elif not should_escalate and d['escalate'] == 'Escalate':
                d['FP'] = True
                d['correct?'] = False
            else:
                d['correct?'] = False


        #TPs, FPs, TNs, FNs
        # specificity, sensitivity, precision
        # time on task

        #for each event
        # - get count of all decisions
        # - get latest decision (may not have made one)
        # - get count of undecided events

        i_dont_knows = 0
        for event_id, event in events.items():
            for decision in decisions:
                if decision['event_id'] == event_id:
                 pass

        #for each latest decision
        # - counter for FPs, TPs, TNs, FNs

            # TODO: Count number not decided at all.

    # with connection as conn:
    #     cursor = conn.cursor()
    #     # cursor.execute('select id, username, time_begin, time_end, questionnaire_complete, survey_complete, training_complete from "user"')

    #     cursor.execute('''SELECT u.*, pqa.* 
    #         FROM "user" AS u 
    #         INNER JOIN prequestionnaire_answers as pqa 
    #         ON u.username = pqa.user''')

    #     users = cursor.fetchall()
    #     for u in users:
    #         print(u[0])

    #     exit(0)

    #     excel_file = Path(
    #         EXCEL_DIR, f'{HEROKU_APP}_{datetime.now().strftime("%Y%m%d_%H-%M-%S")}.xlsx')

    #     wb = Workbook()
    #     ws = wb.active
    #     ws.title = 'users'

    #     headers = ['id', 'username', 'time_begin', 'time_end',
    #                'questionnaire_complete', 'survey_complete', 'training_complete']
    #     for col in range(len(headers)):
    #         ws.cell(row=1, column=col+1, value=headers[col])

    #     row = 2
    #     for user in users:
    #         # build user computations here

    #         for field in range(len(user)):
    #             ws.cell(row=row, column=field+1, value=user[field])
    #         row += 1

    #     wb.save(excel_file)


if __name__ == "__main__":
    # download_and_import()
    export_excel()
