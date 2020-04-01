from pathlib import Path

import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns

sns.set_palette("pastel")
sns.set(font_scale = 1.5)
# sns.set(rc={"font.size":12,"axes.titlesize":14,"axes.labelsize":12})
# sns.set(rc={"font.size":24,"axes.titlesize":24,"axes.labelsize":24})

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
    plt.tight_layout()
    plt.savefig(PLOT_DIR / (x.replace(' ', '_') + '-' + y.replace(' ', '_') + file_suffix + ".png"))
    plt.show()


def plot_user_results(df):
    df['group'] = df['group'].astype({'group': 'str'}).map({'1': '50% FAR', '3': '86% FAR'})
    df['time on task percentile'] = df['25th percentile'].astype({'25th percentile': 'str'}).map({'True': '25th%', 'False': 'Others'})
    max_time = max(df['time_on_task'])

    # Performance measures - whole group
    _plot(df, x="group", y="sensitivity", ylim=(-0.05, 1.05))
    _plot(df, x="group", y="specificity", ylim=(-0.05, 1.05))
    _plot(df, x="group", y="precision", ylim=(-0.05, 1.05), xlabel='')
    _plot(df, x="group", y="time_on_task", ylim=(-0.05, max_time+1), title='Time on Task (Minutes)')

    # Performance measures - 25% vs rest
    _plot(df, x='time on task percentile', y="sensitivity", ylim=(-0.05, 1.05), title_suffix='Time on Task effects')
    _plot(df, x='time on task percentile', y="specificity", ylim=(-0.05, 1.05), title_suffix='Time on Task effects')
    _plot(df, x='time on task percentile', y="precision", ylim=(-0.05, 1.05), title_suffix='Time on Task effects')
    _plot(df, x='time on task percentile', y="time_on_task", ylim=(-0.05, max_time+1), title='Time on Task (Minutes)')


    # Perf measure - 25% removed
    print(df.groupby(['group', 'time on task percentile']).size())
    df = df[df['time on task percentile'] == 'Others']

    _plot(df, x="group", y="sensitivity", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="specificity", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="precision", ylim=(-0.05, 1.05), title_suffix='25th% removed', file_suffix='_25th_removed')
    _plot(df, x="group", y="time_on_task", ylim=(-0.05, max_time+1), title_suffix='25th% removed', title='Time on Task (Minutes)', file_suffix='_25th_removed')

    print(df.head().to_string())


def plot_decision_time(df):
    df['mean'] = pd.to_timedelta(df['mean'], unit='day').dt.total_seconds()
    ax = sns.regplot(data=df.reset_index(), x='index', y='mean', lowess=True, line_kws={'color': 'red'})
    ax.set_title("Mean time to make a decision")
    ax.set_xlabel("order of events")
    ax.set_ylabel("mean time to decide (s)")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "event_decision_time.png")
    plt.show()

if __name__ == "__main__":
    input_file = Path('excel') / "cry-wolf_20200125_14-35-09_patched_analysis.xlsx"
    users = pd.read_excel(input_file, sheet_name='users')
    plot_user_results(users)

    input_file = Path('excel') / "cry-wolf_20200125_14-35-09_patched_decision_time.xlsx"
    decision_times = pd.read_excel(input_file, sheet_name='event_decision_time')
    plot_decision_time(decision_times)