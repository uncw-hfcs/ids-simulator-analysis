from pathlib import Path

import numpy as np
import pandas as pd


# Constants that may need to be changed based on local machine configuration
HEROKU_APP = 'cry-wolf'
SNAPSHOTS_DIR = 'snapshots'
PG_USERNAME = 'postgres'
PG_PASSWORD = 'postgres'
PG_HOST = 'localhost'
PG_DATABASE = 'crywolf'

EXCEL_DIR = 'excel'
   
TRUE_ALARM = 'Escalate'
FALSE_ALARM = "Don't escalate"
UNDECIDED = "I don't know"
# Escalate, Don't escalate, I don't know
def normalize_answer(event):
    if event['should_escalate'] == 1:
        return TRUE_ALARM
    return FALSE_ALARM

def calc_confusion(user, events, event_decisions): 
    user_decisions = event_decisions[event_decisions.user == user.username]    
    for decision in user_decisions.itertuples():
        answer = events[events.id == decision.event_id].should_escalate.item()
        # Exclude I don't knows
        if decision.escalate == UNDECIDED:
            user[decision.event_id] = np.NaN
        elif answer == TRUE_ALARM:
            user[decision.event_id] = 'TP' if decision.escalate == TRUE_ALARM else 'FN'
        else:
            user[decision.event_id] = 'FP' if decision.escalate == TRUE_ALARM else 'TN'            
    return user    

def compute_results():
    # Use the corected master workbook, which correctly labels the 4 eurotrip alerts as TRUE alarms
    file = Path('backups') / 'cry-wolf_20200125_14-35-09_patched.xlsx'


    events = pd.read_excel(file, sheet_name='Event')
    event_decisions = pd.read_excel(file, sheet_name='EventDecision')

    # Drop "check" events from analysis
    events = events[(events['id'] != 74) & (events['id'] != 75)]
    event_decisions = event_decisions[(event_decisions.event_id != 74) & (event_decisions.event_id != 75)]

    # Keep only most recent decision per event per user
    event_decisions.sort_values('time_event_decision', inplace=True)
    orig_len = len(event_decisions)
    event_decisions.drop_duplicates(subset=['user', 'event_id'], keep='last', inplace=True)
    print(f"Dropped {orig_len - len(event_decisions)} duplicate decisions keeping most recent.")

    # Normalize 'should_escalate' column and 'event_decision' column values
    events['should_escalate'] = events.apply(normalize_answer, axis=1)
    true_alarms = events[events.should_escalate == TRUE_ALARM]
    false_alarms = events[events.should_escalate == FALSE_ALARM]
    print(f"True alarms: {len(true_alarms)}, False alarms: {len(false_alarms)}")

    # Create user dataframe to record users' correctness for each event
    users = pd.read_excel(file, sheet_name='User')
    users = users.dropna()
    # Remove user 'awiv3' whose check_score == 2. It was determined to exclude him from analysis. 
    # We keep check_score = 3 (typo) and = 0 because that user (wgff3) intionally picked wrong answers.
    # The check events (ids 74-75) are not included in correctness/confusion matrix.
    users = users[users.username != 'awiv3']
    event_decisions[event_decisions.user != 'awiv3']

    # Get user time on task and determine whether the user is in the 25th percentile in time on task.
    users['time_on_task'] = users.time_end - users.time_begin
    quartile_1 = np.quantile(users.time_on_task, 0.25)
    print(f"Time on task 25th percentile: {float(quartile_1) / 1000000000 / 60:.2f} minutes")
    users['25th percentile'] = np.where(users.time_on_task <= quartile_1, True, False)

    # count number of events each user decided upon
    # get mean confidence as well

    # Problem is confidence is object due to none values for I don't knows
    
    dec_count = event_decisions[['user', 'event_id', 'confidence']] \
        .groupby(['user'])\
        .agg({'event_id' : "count"})
    print(dec_count.head())
    exit(0)
    dec_count.rename(columns={'user': 'username', 'event_id': 'decision_count'}, inplace=True)
    users = users.merge(dec_count, how='left', on='username')

    confidence = event_decisions[['user', 'confidence']].groupby(['user'], as_index=False).mean().reset_index()
    # dec_count.rename(columns={'user': 'username', 'event_id': 'decision_count'}, inplace=True)
    print(confidence.head())
    exit(0)

    print(dec_count)

    # users['perc_decided'] = len(event_decisions[event_decisions.user == users.username])
    # print(users.head())
    exit(0)
    #     user['perc_decided'] = len(latest_decisions) * 100 / (len(user_events) + 3)
    #     user['avg_confidence'] = confidence_sum / len(latest_decisions) if latest_decisions else 'N/A'

    event_ids = sorted(list(event_decisions.event_id.unique()))
    users = users.reindex(columns = ['username', 'group', 'time_on_task', '25th percentile'] + event_ids)
    
    # Compute confusion matrix for each user, dropping "I don't know" answers
    users = users.apply(calc_confusion, axis=1, args=(events, event_decisions))
    users['TP'] = (users[event_ids] == 'TP').sum(axis=1)
    users['FP'] = (users[event_ids] == 'FP').sum(axis=1)
    users['FN'] = (users[event_ids] == 'FN').sum(axis=1)
    users['TN'] = (users[event_ids] == 'TN').sum(axis=1)

    # Compute performance measures for each user
    users['sensitivity'] = users['TP'] / (users['TP'] + users['FN'])
    users['specificity'] = users['TN'] / (users['TN'] + users['FP'])
    users['precision'] = users['TP'] / (users['TP'] + users['FP'])
    users['correctness'] = (users['TP'] + users['TN']) / (users['TP'] + users['FP'] + users['TN'] + users['FN'])


    # user['decided'] = len(latest_decisions)
    #     user['perc_decided'] = len(latest_decisions) * 100 / (len(user_events) + 3)
    #     user['avg_confidence'] = confidence_sum / len(latest_decisions) if latest_decisions else 'N/A'
    #     user['correct'] = num_correct
    #     user['perc_correct'] = num_correct * 100 / len(latest_decisions) if latest_decisions else 'N/A'
    #     user['i_dont_knows'] = i_dont_knows
    #     user['sensitivity'] = sensitivity
    #     user['specificity'] = specificity
    #     user['precision'] = precision
    #     user['TP'] = confusion['TP']
    #     user['FP'] = confusion['FP']
    #     user['TN'] = confusion['TN']
    #     user['FN'] = confusion['FN']
    #     user['check_score'] = check_score
    #     user['avg_first_decision_first_click_delta'] = total_first_decision_first_click_delta / len(latest_decisions) if latest_decisions else 'N/A'
    print(users.head())

if __name__ == "__main__":

    # 0. Must have run 'heroku login' prior to running this script


    # 2. Manually generate models using sqlacodegen string from 1.

    compute_results()

    # 4. write_excel
    # write_excel(results, user_event_deltas, session)
