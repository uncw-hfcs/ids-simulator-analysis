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

    print(
        f"Run the following from .venv terminal: sqlacodegen postgresql:///{PG_DATABASE} --outfile models.py")


def _to_dict(model):
    d = model.__dict__
    d.pop('_sa_instance_state', None)
    return d


def export_excel():
    from models import User, Event, EventDecision

    engine = create_engine(
        f'postgresql+psycopg2://{PG_USERNAME}:{PG_PASSWORD}@{PG_HOST}/{PG_DATABASE}')
    Session = sessionmaker(bind=engine)
    session = Session()

    if not os.path.exists(EXCEL_DIR):
        os.makedirs(EXCEL_DIR)

    connection = psycopg2.connect(user=PG_USERNAME,
                                  password=PG_PASSWORD,
                                  host=PG_HOST,
                                  port="5432",
                                  database=PG_DATABASE)

    events = {e.id: _to_dict(e) for e in session.query(Event)}
    users = {u.username: _to_dict(u) for u in session.query(User)}
    for username, user in users.items():
        user_events = user['events'].split(',')
        decisions = [_to_dict(d) for d in session.query(EventDecision).filter_by(user=username)] 
        latest_decisions = {}
        decision_counts = {}
        i_dont_knows = 0

        for d in decisions:
            # Increment how many times a decision was made for a particular event
            decision_counts[d["event_id"]] = decision_counts.get(d["event_id"], 0) + 1

            # Check events are 74, 75
            # "should_escalate" = 1 for TP, 0 for TN
            d['TP'] = False
            d['FP'] = False
            d['TN'] = False
            d['FN'] = False
            should_escalate = True if events[d['event_id']]['should_escalate'] == '1' else False
            if d['escalate'] == "I don't know":
                d['correct?'] = False
                i_dont_knows += 1
            elif should_escalate and d['escalate'] == "Escalate":
                d['TP'] = True
                d['state'] = 'TP'
                d['correct?'] = True
            elif should_escalate and d['escalate'] == "Don't escalate":
                d['FN'] = True
                d['state'] = 'FN'
                d['correct?'] = False
            elif not should_escalate and d['escalate'] == "Don't escalate":
                d['TN'] = True
                d['state'] = 'TN'
                d['correct?'] = True
            elif not should_escalate and d['escalate'] == 'Escalate':
                d['FP'] = True
                d['state'] = 'FP'
                d['correct?'] = False
            else:
                raise Exception("Encountered an unknown value for 'Escalate' in the event decision", d['escalate'])

            # Add/replace the "most recent decision" for an event in a separate dictionary
            if d["event_id"] not in latest_decisions or d["time_event_decision"] > latest_decisions[d["event_id"]]["time_event_decision"]:
                # print("new latest:",
                #     d["user"],
                #     d["event_id"],
                #     'None' if d["event_id"] not in latest_decisions else latest_decisions[d["event_id"]]["time_event_decision"],
                #     "-->",
                #     d["time_event_decision"])

                latest_decisions[d["event_id"]] = d

        #TPs, FPs, TNs, FNs
        # specificity, sensitivity, precision
        # time on task

        confusion = {
            'TP' : 0,
            'FP' : 0,
            'TN' : 0,
            'FN' : 0
        }
        num_correct = 0
        confidence_sum = 0
        for event_id, decision in latest_decisions.items():
            if 'confidence' in decision:
                confidence_sum += int(decision['confidence'])
            if decision['correct?']:
                num_correct += 1
            # Generate confusion matrix for event decisions made. "I don't knows" are excluded
            if 'state' in decision:
                confusion[decision['state']] += 1
        
        specificity = 0 if confusion['TN'] + confusion['FP'] == 0 else confusion['TN'] / (confusion['TN'] + confusion['FP'])
        sensitivity = 0 if confusion['TP'] + confusion['FN'] == 0 else confusion['TP'] / (confusion['TP'] + confusion['FN'])
        precision = 0 if confusion['TP'] + confusion['FP'] == 0 else confusion['TP'] / (confusion['TP'] + confusion['FP'])

        if len(latest_decisions):
            print(f"{username} - " 
                f"{len(latest_decisions)}/{(len(user_events) + 3)} decided, "     # the 3 are the 2 check events + 1 obvious attack everyone got
                f"{confidence_sum / len(latest_decisions) if latest_decisions else 0:0.1f} avg confidence, "
                f"{num_correct * 100 / len(latest_decisions) if latest_decisions else 0:.0f}% correct, " 
                f"{i_dont_knows} IDKs, "
                f"{specificity * 100:.1f} specificity, "
                f"{sensitivity * 100:.1f} sensitivity, "
                f"{precision * 100:.1f} precision, "
                f"{confusion}"
                )
        
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
    #         for field in range(len(user)):
    #             ws.cell(row=row, column=field+1, value=user[field])
    #         row += 1

    #     wb.save(excel_file)


if __name__ == "__main__":
    # download_and_import()
    export_excel()
