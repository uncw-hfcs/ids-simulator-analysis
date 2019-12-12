from pathlib import Path
import pandas as pd
import numpy as np

# Escalate, Don't escalate, I don't know
def normalize_answer(event):
    if event['should_escalate'] == 1:
        return 'Escalate'
    return "Don't escalate"

# Given an event, return how many participants answered and answered correctly in group1 and group3.
def calc_difficulty(event, event_decisions):  
    event['group1_count'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('1'))])
    event['group1_correct'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('1')) & (event_decisions.escalate == event.should_escalate)])         

    event['group3_count'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('3'))])
    event['group3_correct'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('3')) & (event_decisions.escalate == event.should_escalate)])         

    event['group1_difficulty'] = np.NaN if event['group1_count'] == 0 else event['group1_correct'] / event['group1_count']
    event['group3_difficulty'] = np.NaN if event['group3_count'] == 0 else event['group3_correct'] / event['group3_count']
    event['total_difficulty'] = np.nansum([event['group1_correct'], event['group3_correct']]) / np.nansum([event['group1_count'], event['group3_count']])    

    print(f"{event['id']}: Group1: {event['group1_correct']}/{event['group1_count']} ({event['group1_difficulty']*100:2.0f}), " \
          f"Group 3: {event['group3_correct']}/{event['group3_count']} ({event['group3_difficulty']*100:2.0f}), " \
          f"Total difficulty: {(event['total_difficulty'])*100:2.0f}")

    return event


def calc_confusion(user, events, event_decisions): 
    user_decisions = event_decisions[event_decisions.user == user.user]    
    for decision in user_decisions.itertuples():
        answer = events[events.id == decision.event_id].should_escalate.item()
        if answer == 'Escalate':
            user[decision.event_id] = 'TP' if decision.escalate == 'Escalate' else 'FN'
        else:
            user[decision.event_id] = 'FP' if decision.escalate == 'Escalate' else 'TN'            
    return user    





file = Path('backups') / 'cry-wolf_20191021_13-51-49_MIS310.xlsx'

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

# Compute confusion matrix for each user
users = pd.DataFrame(event_decisions.user.unique(), columns=['user'])
event_ids = sorted(list(event_decisions.event_id.unique()))
users = users.reindex(columns = ['user'] + event_ids)
# Extract group id
users['group'] = users.user.str[-1:]

# Remove user 'awiv3' whose check_score == 2. It was determined to exclude him from analysis. 
# We keep check_score = 3 (typo) and = 0 because that user (wgff3) intionally picked wrong answers.
# The check events (ids 74-75) are not included in correctness/confusion matrix.
users = users[users.user != 'awiv3']

# Get user time on task. Not using this data currently -- may want to drop bottom quartile.
master = pd.read_excel(file, sheet_name='master')
master['time_on_task'] = master.time_end - master.time_begin
user_info = master[['username', 'time_on_task']]
user_info.rename(columns={"username": "user"}, inplace=True)
users = pd.merge(users, user_info, how='left', on=['user'])

# Compute confusion matrix for each user
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

# Compute per event difficulty based on user correctness. Difficulty is % of users correct: 0-100.
event_results = pd.DataFrame([num for num in list(users.columns) if isinstance(num, np.int64)], columns=['id'])
event_results['difficulty'] = [((users[e] == 'TP').sum() + (users[e] == 'TN').sum()) / users[e].notna().sum() for e in event_results['id']]


def calc_discrimination_index(event, label, high, low):
    eid = event['id']
    if high[eid].isna().all() or low[eid].isna().all():
        event[label] = np.NaN
    else:
        high_correct = len(high[high[eid] == 'TP']) + len(high[high[eid] == 'TN'])
        low_correct = len(low[low[eid] == 'TP']) + len(low[low[eid] == 'TN'])
        event[label] = (high_correct - low_correct)/ max([len(high), len(low)])
    return event

# Calculate discrimination index for each event based on user correctness.
# Treat different false alarm rate groups as different tests as they are, according to performance measures, testing different skills/constructs.
for group in ['1', '3']:
    df = users[users.group == group]
    df.sort_values(by='correctness', ascending=False, inplace=True)

    # Take the 27% highest and lowest performers from the group across all events        
    size = round(len(df)*0.27)
    event_results = event_results.apply(calc_discrimination_index, axis=1, args=(f'group{group}_D', df.head(n=size), df.tail(n=size)))


event_types = pd.read_excel('events.xlsx', sheet_name='event_type')
headers = [
    'id',
    'true/false alarm',
    'city 1',
    'city 1: successful logins',
    'city 1: failed logins',
    'city 1: source provider',
    'city 2',
    'city 2: successful logins',
    'city 2: failed logins',
    'city 2: source provider',
    'time b/w authentications',
    'VPN confidence',
    'type'
]

sample_ids = [52, 66, 2, 11, 18, 26, 40]
event_samples = event_types[event_types['id'].isin(sample_ids)]
with open('event_samples.tex', 'w') as tab:
    event_samples.to_latex(buf=tab, header=headers, index=False)

# this matching is fragile. Requires both dataframes to be sorted by event id. Event id is also generated by Cry Wolf, so it could change in subsequent analyses
event_results['type'] = event_types['comments']

# print(event_results.sort_values(by='difficulty').to_string())
# print(event_results.to_string())
# print(events.to_csv())
    
    



