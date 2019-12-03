from pathlib import Path
import pandas as pd

# Escalate, Don't escalate, I don't know
def normalize_answer(event):
    if event['should_escalate'] == 1:
        return 'Escalate'
    return "Don't escalate"

def count_correct(event, event_decisions):
    
    event['group1_count'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('1'))])
    event['group1_correct'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('1')) & (event_decisions.escalate == event.should_escalate)])         
    

    event['group3_count'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('3'))])
    event['group3_correct'] = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('3')) & (event_decisions.escalate == event.should_escalate)])         
    print(f"{event['id']}: Group1: {event['group1_correct']}/{event['group1_count']}, Group 3: {event['group3_correct']}/{event['group3_count']}")
    return event



file = Path('backups') / 'cry-wolf_20191021_13-51-49_MIS310.xlsx'

events = pd.read_excel(file, sheet_name='Event')
event_decisions = pd.read_excel(file, sheet_name='EventDecision')

# Keep only most recent decision per event per user
event_decisions.sort_values('time_event_decision', inplace=True)
orig_len = len(event_decisions)
event_decisions.drop_duplicates(subset=['user', 'event_id'], keep='last', inplace=True)
print(f"Dropped {orig_len - len(event_decisions)} duplicate decisions keeping most recent.")

# Convert 'should_escalate' column to match event_decision column values
events['should_escalate'] = events.apply(normalize_answer, axis=1)

events = events.apply(count_correct, axis=1, args=(event_decisions,))
print(events.head())



