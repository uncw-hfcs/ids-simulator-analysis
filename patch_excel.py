from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

NAME = 'cry-wolf_20200125_14-35-09'
excel_file = Path('backups') /  (NAME + '.xlsx')
patched_file = Path('backups') / (NAME + '_patched.xlsx')

to_correct = [8, 9, 10, 12, 13]
df = pd.read_excel(excel_file, sheet_name='Event')
df.loc[df.id.isin(to_correct), 'should_escalate'] = 1
# print(df[['id', 'should_escalate']].to_string())


with pd.ExcelWriter(patched_file, engine='openpyxl') as writer:
    book = load_workbook(excel_file)
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer, "Event", index=False)

    writer.save()
