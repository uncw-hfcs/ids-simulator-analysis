from pathlib import Path

import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns

sns.set_palette("pastel")
sns.set(rc={"font.size":12,"axes.titlesize":14,"axes.labelsize":12})

PLOT_DIR = Path('plots')
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)


def _plot(df, x, y, title=None, title_suffix='', file_suffix='', **kwargs):
    if not title:
        title = y.title()
    if title_suffix:
        title_suffix = u' \u2014 ' + title_suffix
    ax = sns.boxplot(x=x, y=y, width=0.5, data=df)
    ax.set_title(title + title_suffix)
    ax.set(**kwargs)
    plt.savefig(PLOT_DIR / (x + '-' + y + file_suffix + ".png"))
    plt.show()


def plot_user_results(df):

    df['group'] = df['group'].astype({'group': 'str'}).map({'1': '50% FAR', '3': '86% FAR'})
    df['25th percentile'] = df['25th percentile'].astype({'25th percentile': 'str'}).map({'True': '25th%', 'False': 'Others'})
    max_time = max(df['time_on_task'])

    # Performance measures - whole group
    _plot(df, x="group", y="sensitivity", ylim=(-0.05, 1.05))
    _plot(df, x="group", y="specificity", ylim=(-0.05, 1.05))
    _plot(df, x="group", y="precision", ylim=(-0.05, 1.05))
    _plot(df, x="group", y="time_on_task", ylim=(-0.05, max_time+1), title='Time on Task (Minutes)')

    # Performance measures - 25% vs rest
    _plot(df, x="25th percentile", y="sensitivity", ylim=(-0.05, 1.05))
    _plot(df, x="25th percentile", y="specificity", ylim=(-0.05, 1.05))
    _plot(df, x="25th percentile", y="precision", ylim=(-0.05, 1.05))
    _plot(df, x="25th percentile", y="time_on_task", ylim=(-0.05, max_time+1), title='Time on Task (Minutes)')


    # Perf measure - 25% removed
    print(df.groupby(['group', '25th percentile']).size())
    df = df[df['25th percentile'] == 'Others']

    _plot(df, x="group", y="sensitivity", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="specificity", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="precision", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="time_on_task", ylim=(-0.05, max_time+1), title_suffix='25th% removed', title='Time on Task (Minutes)', file_suffix='_25th_removed')

    print(df.head().to_string())


if __name__ == "__main__":
    input_file = Path('excel') / "cry-wolf_20200125_14-35-09_patched_analysis.xlsx"
    users = pd.read_excel(input_file, sheet_name='users')
    plot_user_results(users)