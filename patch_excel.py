from pathlib import Path
import pandas as pd

file = Path('backups') / 'cry-wolf_20200125_14-35-09.xlsx'

to_correct = [8, 9, 10, 12, 13]
df = pd.read_excel(file, sheet_name='Event')
df.loc[df.id.isin(to_correct), 'should_escalate'] = 1
print(df[['id', 'should_escalate']].to_string())
