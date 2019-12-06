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


def set_group(user, measure, median_value):
    user[f'{measure}_group'] = "High" if user[measure] >= median_value else "Low"
    return user


file = Path('backups') / 'cry-wolf_20191021_13-51-49_MIS310.xlsx'

events = pd.read_excel(file, sheet_name='Event')
event_decisions = pd.read_excel(file, sheet_name='EventDecision')

# Need to drop "check" events
events = events[(events['id'] != 74) & (events['id'] != 75)]
event_decisions = event_decisions[(event_decisions.event_id != 74) & (event_decisions.event_id != 75)]

# Keep only most recent decision per event per user
event_decisions.sort_values('time_event_decision', inplace=True)
orig_len = len(event_decisions)
event_decisions.drop_duplicates(subset=['user', 'event_id'], keep='last', inplace=True)
print(f"Dropped {orig_len - len(event_decisions)} duplicate decisions keeping most recent.")

# Normalize 'should_escalate' column and 'event_decision' column values
events['should_escalate'] = events.apply(normalize_answer, axis=1)

# Calculate correctness measures per group and append onto dataframe
# events = events.apply(calc_difficulty, axis=1, args=(event_decisions,))

# Compute confusion matrix for each user
users = pd.DataFrame(event_decisions.user.unique(), columns=['user'])
event_ids = sorted(list(event_decisions.event_id.unique()))
users = users.reindex(columns = ['user'] + event_ids)

# Remove user 'awiv3' whose check_score == 2. It was determined to exclude him from analysis. 
# We keep check_score = 3 (typo) and = 0 because that user (wgff3) intionally picked wrong answers.
# The check events (ids 74-75) are not included in correctness/confusion matrix.
users = users[users.user != 'awiv3']

# Get user time on task
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

# Compute performance measures per user
users['sensitivity'] = users['TP'] / (users['TP'] + users['FN'])
users['specificity'] = users['TN'] / (users['TN'] + users['FP'])
users['precision'] = users['TP'] / (users['TP'] + users['FP'])

# Interpolate group value
users['group'] = users.user.str[-1:]

g50 = users[users.group == '1']
g96 = users[users.group == '3']
group_dfs = [g50, g96]

for df in group_dfs:
    df = df.dropna(axis=1, how='all').copy()
    event_cols = [num for num in list(df.columns) if isinstance(num, np.int64)]

    for m in ['sensitivity', 'specificity', 'precision']:
        high = pd.DataFrame()
        low = pd.DataFrame()
        median = df[m].median().copy()
        df = df.apply(set_group, axis=1, args=(m, median))
        # print(f"{m.title()} median: {median}")

        size = round(len(df)*0.27)
        try:
            high = df[df[f'{m}_group'] == "High"].sample(n=size)
            low = df[df[f'{m}_group'] == "Low"].sample(n=size)

            for e in event_cols:
                high_correct = len(high[high[e] == 'TP']) + len(high[high[e] == 'TN'])
                low_correct = len(low[low[e] == 'TP']) + len(low[low[e] == 'TN'])
                print(f"Event {e} difficulty: {(high_correct - low_correct)/len(high)}")
        except ValueError:
            print(f"Cannot compute {m} difficulty")
        



