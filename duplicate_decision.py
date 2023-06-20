from pathlib import Path

import openpyxl


class EventDecision:
    def __init__(self, _row):
        self.time = _row[1].value
        self.decision = _row[2].value
        self.user = _row[3].value
        self.confidence = _row[4].value
        self.event_id = _row[5].value
        self.decision_id = _row[0].value

    def __repr__(self):
        return f'({self.user},{self.event_id},{self.decision},{self.confidence})'

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        """
        Equality in an EventDecisions is when the user, event_id, decision, and confidence are equal.
        :param other: the EventDecision to compare to
        :return: True or False
        """
        return self.user == other.user and self.event_id == other.event_id \
            and self.decision == other.decision and self.confidence == other.confidence

    def __hash__(self):
        return hash((self.user, self.event_id, self.decision, self.confidence))

    def __lt__(self, value):
        return self.time < value.time


file = Path('backups') / 'cry-wolf_20200125_14-35-09_patched.xlsx'
wb = openpyxl.load_workbook(file)
event_sheet = wb['EventDecision']

# users is a dictionary whose key is the username. the Values are a dictionary of eventId : Set(EventDecision).
users: dict[str: dict[str:set[EventDecision]]] = {}
resubmit_count = 0  # this will count the total number of resubmissions, including resubmissions that do not change
event_decision_count = 0
for row in event_sheet.iter_rows(min_row=2):
    event_decision_count += 1
    ed = EventDecision(row)

    if ed.user not in users:
        users[ed.user] = {ed.event_id: {ed}}
    else:
        if ed.event_id in users[ed.user]:
            # The value here is added to a Set. Thus, equivalent EventDecisions will not be saved.
            users[ed.user][ed.event_id].add(ed)
            # This will capture all resubmissions
            resubmit_count += 1
        else:
            users[ed.user][ed.event_id] = {ed}

print(f"Number of unique event decisions: {event_decision_count}")
print(f"Number of resubmitted event decisions: {resubmit_count}")
print(f"Number of unique users: {len(users.keys())}")
print("Users+event ids with changes on resubmit:")

count_changed = 0
count_changed_events = 0

change_counts_by_user = {}

for user, v in users.items():
    for event_id, decisions in v.items():
        if len(decisions) > 1:
            if user in change_counts_by_user:
                change_counts_by_user[user] += 1
            else:
                change_counts_by_user[user] = 1
            count_changed += len(decisions) - 1
            count_changed_events += 1
            print(sorted(decisions))

print(f"Number of changes on resubmit: {count_changed}")
print(f"Number of unique events that were changed: {count_changed_events}")
print(f"Users who changed their answers: {change_counts_by_user}")
