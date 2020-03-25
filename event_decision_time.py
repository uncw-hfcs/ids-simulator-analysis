from pathlib import Path
import openpyxl

class EventDecision:
    def __init__(self, row):
        self.time = row[0].value
        self.decision = row[1].value
        self.user = row[2].value
        self.confidence = row[3].value
        self.event_id = row[4].value
        self.decision_id = row[5].value

    def __repr__(self):
        return f'({self.user},{self.event_id},{self.decision},{self.confidence})'

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.user == other.user and self.event_id == other.event_id and self.decision == other.decision and self.confidence == other.confidence

    def __hash__(self):
        return hash((self.user, self.event_id, self.decision, self.confidence))

    def __lt__(self, value):
        return self.time < value.time


file = Path('backups') / 'cry-wolf_20200125_14-35-09_patched.xlsx'
wb = openpyxl.load_workbook(file)
event_sheet = wb['EventDecision']

# for each user, get the order of events first clicked and their time
#   then, get the time of the first event decision for that event
#   then, calculate the time diff
