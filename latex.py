from pathlib import Path
import pandas as pd

input_file = Path('excel') / "cry-wolf_20200125_14-35-09_patched_analysis.xlsx"
df = pd.read_excel(input_file, sheet_name='users')

# Generate latex outputs
df.rename(columns={'time_on_task': 'time on task'}, inplace=True)
df['group'] = df['group'].replace(to_replace=1, value='50\% FAR')
df['group'] = df['group'].replace(to_replace=3, value='86\% FAR')

df['time on task percentile'] = df['25th percentile'].astype({'25th percentile': 'str'}).map(
    {'True': '25th%', 'False': 'Others'})

print(df.groupby(['group', 'time on task percentile']).size())
df = df[df['time on task percentile'] == 'Others']


# confidence
print(df[['group', 'confidence']].groupby(['group']).agg(['mean', 'median']))

outcomes = ['time on task', 'sensitivity', 'specificity', 'precision', 'correctness']

# means = df[outcomes].mean()
# medians = df[outcomes].median()
# stds = df[outcomes].std(ddof=0)
# mins = df[outcomes].min()
# maxes = df[outcomes].max()
# stats = pd.concat([means, medians, stds, mins, maxes], axis=1)
# stats.columns = ['mean', 'median', '$\sigma$', 'min', 'max']
# print(stats.to_latex(float_format='%.2f', escape=False))

group_stats = df[outcomes + ['group']].groupby('group').agg(
    ['mean', 'median', lambda x: x.std(ddof=0), 'min', 'max'])
group_stats.rename(columns={'<lambda_0>': '$\sigma$'}, inplace=True)
group_stats = group_stats.transpose()

# print(group_stats.to_latex(float_format='%.2f', escape=False))



