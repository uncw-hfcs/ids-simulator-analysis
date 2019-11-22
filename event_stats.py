from pathlib import Path
import pandas as pd


def count_correct(event, event_decisions):
    group1_count = len(event_decisions[(event_decisions.event_id == event['id']) & (event_decisions.user.str.endswith('1'))])
    print(group1_count)



file = Path('backups') / 'cry-wolf_20191021_13-51-49_MIS310.xlsx'

events = pd.read_excel(file, sheet_name='Event')
event_decisions = pd.read_excel(file, sheet_name='EventDecision')

event_decisions.sort_values('time_event_decision', inplace=True)
orig_len = len(event_decisions)
event_decisions.drop_duplicates(subset=['user', 'event_id'], keep='last', inplace=True)
print(f"Dropped {orig_len - len(event_decisions)} duplicate decisions keeping most recent.")

events['should_escalate'] = events['should_escalate'] == 1

# events.apply(count_correct, axis=1, args=(event_decisions,))



