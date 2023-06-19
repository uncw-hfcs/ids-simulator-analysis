from pathlib import Path
from typing import List


import numpy as np
import os
import pandas as pd
import scipy.stats as stats

# Constants that may need to be changed based on local machine configuration
HEROKU_APP = 'cry-wolf'
SNAPSHOTS_DIR = 'snapshots'
PG_USERNAME = 'postgres'
PG_PASSWORD = 'postgres'
PG_HOST = 'localhost'
PG_DATABASE = 'crywolf'

EXCEL_DIR = 'excel'

TRUE_ALARM = 'Escalate'
FALSE_ALARM = "Don't escalate"
UNDECIDED = "I don't know"


def normalize_answer(event: pd.Series):
    """
    Normalizes Event table "should_escalate" values to same values stored
    when the user makes a decision.
    :param event: an alarm from the Cry Wolf data set as a Series with labeled columns.
    :return: a string containing 'Escalate' or 'Don't escalate'
    """
    if event['should_escalate'] == 1:
        return TRUE_ALARM
    return FALSE_ALARM


def calc_confusion(user, events, event_decisions):
    user_decisions = event_decisions[event_decisions.user == user.username]
    for decision in user_decisions.itertuples():
        answer = events[events.id == decision.event_id].should_escalate.item()
        # Exclude "I don't know"s
        if decision.escalate == UNDECIDED:
            user[decision.event_id] = 'IDK'
        elif answer == TRUE_ALARM:
            user[decision.event_id] = 'TP' if decision.escalate == TRUE_ALARM else 'FN'
        else:
            user[decision.event_id] = 'FP' if decision.escalate == TRUE_ALARM else 'TN'
    return user


def compute_results(filename):
    input_file = Path('backups') / f"{filename}.xlsx"

    events = pd.read_excel(input_file, sheet_name='Event')
    event_decisions = pd.read_excel(input_file, sheet_name='EventDecision')

    # Drop "check" events from analysis
    events = events[(events['id'] != 74) & (events['id'] != 75)]
    event_decisions = event_decisions[(event_decisions.event_id != 74) & (event_decisions.event_id != 75)]

    # Keep only most recent decision per event per user
    event_decisions.sort_values('time_event_decision', inplace=True)
    orig_len = len(event_decisions)
    event_decisions.drop_duplicates(subset=['user', 'event_id'], keep='last', inplace=True)
    print(f"Dropped {orig_len - len(event_decisions)} duplicate decisions keeping most recent.")

    # Normalize 'should_escalate' column and 'event_decision' column values
    events['should_escalate'] = events.apply(normalize_answer, axis=1)
    print(f"True alarms: {len(events[events.should_escalate == TRUE_ALARM])}, "
          f"False alarms: {len(events[events.should_escalate == FALSE_ALARM])}")

    # Create user dataframe to record users' correctness for each event
    users = pd.read_excel(input_file, sheet_name='User')
    users = users.dropna()
    # Remove user 'awiv3' whose check_score == 2. It was determined to exclude them from analysis.
    # We keep check_score = 3 (typo) and = 0 because that user (wgff3) intentionally picked wrong answers.
    # The check events (ids 74-75) are not included in correctness/confusion matrix.
    users = users[users.username != 'awiv3']
    event_decisions = event_decisions[event_decisions.user != 'awiv3']

    # Get user time on task and determine whether the user is in the 25th percentile in time on task.
    # time_on_task will be timedelta64[ns] type
    users['time_on_task'] = users.time_end - users.time_begin
    quartile_1 = np.quantile(users.time_on_task, 0.25)
    print(f"Time on task 25th percentile: {float(quartile_1) / 1000000000 / 60:.2f} minutes")
    users['25th percentile'] = np.where(users.time_on_task <= quartile_1, True, False)

    # count number of events each user decided upon
    # get mean confidence as well

    # Problem is confidence is object due to none values for "I don't know"s
    event_decisions['confidence'] = pd.to_numeric(event_decisions['confidence'], errors='coerce', downcast='unsigned')

    dec_count = event_decisions[['user', 'event_id', 'confidence']] \
        .groupby(['user'], as_index=False) \
        .agg({'event_id': "count",
              'confidence': "mean"})

    dec_count.rename(columns={'user': 'username', 'event_id': 'decision_count'}, inplace=True)
    users = users.merge(dec_count, how='left', on='username')

    event_ids = sorted(list(event_decisions.event_id.unique()))
    users = users.reindex(
        columns=['username', 'group', 'time_on_task', '25th percentile', 'decision_count', 'confidence'] + event_ids)

    # Compute confusion matrix for each user, dropping "I don't know" answers
    users = users.apply(calc_confusion, axis=1, args=(events, event_decisions))
    users['TP'] = (users[event_ids] == 'TP').sum(axis=1)
    users['FP'] = (users[event_ids] == 'FP').sum(axis=1)
    users['FN'] = (users[event_ids] == 'FN').sum(axis=1)
    users['TN'] = (users[event_ids] == 'TN').sum(axis=1)
    users['i_dont_knows'] = (users[event_ids] == 'IDK').sum(axis=1)

    # Compute performance measures for each user
    users['sensitivity'] = users['TP'] / (users['TP'] + users['FN'])
    users['specificity'] = users['TN'] / (users['TN'] + users['FP'])
    users['precision'] = users['TP'] / (users['TP'] + users['FP'])
    users['correctness'] = (users['TP'] + users['TN']) / (users['TP'] + users['FP'] + users['TN'] + users['FN'])

    # TODO: Need to make check score calculation part of this scripting apparatus, but want to keep some control too
    #     user['avg_first_decision_first_click_delta'] = total_first_decision_first_click_delta / len(latest_decisions) if latest_decisions else 'N/A'

    # print(users.head().to_string())

    # Compute experience groups
    exp_groups = determine_user_groups(filename)
    users = users.merge(exp_groups, how='left', on='username')
    # print(users.head())

    # Convert time_on_task from timedelta64 to fractional minutes
    users['time_on_task'] = users['time_on_task'] / np.timedelta64(1, 'm')

    return users


def compute_experience_group(user):
    GT_1year = ['1 - 5', '5 - 10', '10+']
    # Cyber Security = score >= 5 && > 1 year Security Experience
    # Network/IT admin = score >= 5 && > 1 year Network IT
    # Software development = > 1 year Software Development
    # Novice = score < 5 &  < 1yr software development
    # Novice+ = score >=5 & (<1 || no experience)'
    if (user['exp_security'] in GT_1year or user['exp_admin'] in GT_1year) and user['score'] >= 5:
        return 'Practical'

    if user['score'] >= 5:
        return 'Novice+'

    return 'Novice'


def determine_user_groups(filename):
    input_file = Path('backups') / f"{filename}.xlsx"

    quest = pd.read_excel(input_file, sheet_name='PrequestionnaireAnswer')
    SUBNET_MASK = '255.255.255.0'
    NETWORK_ADDRESS = '173.67.14.0'
    TCP_UDP = 'False'
    HTTP_PORT = '80'
    SEC_DEVICE = 'Firewall'
    IP_AND_PORT = 'Socket'
    MODEL = 'TCP/IP'

    NO_EXPERIENCE = 'No Experience'
    quest['score'] = (quest['subnet_mask'] == SUBNET_MASK).astype(int) + \
                     (quest['network_address'] == NETWORK_ADDRESS) + \
                     (quest['tcp_faster'] == TCP_UDP) + \
                     (quest['http_port'] == HTTP_PORT) + \
                     (quest['firewall'] == SEC_DEVICE) + \
                     (quest['socket'] == IP_AND_PORT) + \
                     (quest['which_model'] == MODEL)
    quest['experience_group'] = quest.apply(compute_experience_group, axis=1)
    quest.rename(columns={'user': 'username'}, inplace=True)
    return quest[['username', 'experience_group']]


# def get_order_of_first_event_clicks(clicks):


def event_decision_time(filename: str, users: pd.DataFrame) -> pd.DataFrame:
    file = Path('backups') / f"{filename}.xlsx"

    # Filter on first clicks on each event for each user
    event_clicked = pd.read_excel(file, sheet_name="EventClicked")
    event_clicked.rename(columns={'user': 'username'}, inplace=True)
    event_clicked = event_clicked.sort_values('time_event_click').drop_duplicates(subset=['event_id', 'username'])

    # Filter on first decisions on each event for each user
    event_decision = pd.read_excel(file, sheet_name="EventDecision")
    event_decision.rename(columns={'user': 'username'}, inplace=True)
    event_decision = event_decision.sort_values('time_event_decision').drop_duplicates(subset=['event_id', 'username'])

    event_decision = event_decision.merge(event_clicked, how='left', on=['username', 'event_id'])
    event_decision['time_to_first_decide'] = event_decision['time_event_decision'] - event_decision['time_event_click']

    # print(event_decision[['username', 'event_id', 'time_to_first_decide']].head().to_string())

    grouped = event_decision.groupby(['username'])

    # create a dataframe where the row indices are users and the columns are
    # "time to decide an event" for the order the events were decided in
    lst = []
    ids = []
    for name, group in grouped:
        # "name" is the user id
        # "group" is a df with each decision they made as a row

        # "values" is a series of the time_to_first_decide for "name" user id
        values = group['time_to_first_decide'].reset_index(drop=True)
        ids.append(name[0])
        lst.append(values)

    df = pd.DataFrame(lst, index=ids, columns=list(range(52)))

    # filter out the 25th percentile
    # _filter = list(users[users['25th percentile'] == True]['username'])
    # time_to_first_decision = time_to_first_decision.drop(_filter)

    # Calculate the mean event decision time per user
    df['mean_time_per_user'] = df.mean(axis=1)

    # Add group column.
    groups = users.merge(df, right_index=True, left_on="username")
    # Convert mean to float
    groups['mean_time_per_user'] = groups['mean_time_per_user'].apply(lambda x: x.total_seconds())

    # Compute the mean decision times per group
    performance_basic_stats(groups, ['mean_time_per_user'])
    compute_stats(groups[groups['group'] == 1],groups[groups['group'] == 3], ['mean_time_per_user'])

    df.drop('mean_time_per_user', axis=1)
    df = df.transpose()
    df['mean'] = df.mean(axis=1)
    return df


def tlx(filename, users):
    file = Path('backups') / f"{filename}.xlsx"
    df = pd.read_excel(file, sheet_name="SurveyAnswer")
    df.rename(columns={'user': 'username'}, inplace=True)
    df = df[['username', 'mental', 'physical', 'temporal', 'performance', 'effort', 'frustration']]
    df = df.merge(users, how='left', on='username')

    deps = ['mental', 'physical', 'temporal', 'performance', 'effort', 'frustration']
    # Convert from 1-10 scale to 1-7
    # df[deps] = df[deps].apply(lambda x: 1/3 + ((2/3)*x))
    # Flip the 'Performance' to it's original, which is 1: better performance, 7: poor performance
    df['performance'] = 11 - df['performance']

    # df = df[df['25th percentile'] == False]
    # print(df.to_string())

    far50 = df[df['group'] == 1]
    far86 = df[df['group'] == 3]
    for d in deps:
        res = stats.mannwhitneyu(far50[d], far86[d])
        print(d, res)

    print("NASA TLX overall values")
    print("Mean")
    print(df[deps].mean())

    print("Median")
    print(df[deps].median())

    print("NASA TLX group comparison")
    tab = df[['mental', 'physical', 'temporal', 'performance', 'effort', 'frustration', 'group']].groupby(
        ['group']).agg(['mean', 'median'])
    print(tab.to_string())


def compute_stats(x: pd.DataFrame, y: pd.DataFrame, deps: List[str]):

    for dep in deps:
        U1, p = stats.mannwhitneyu(x[dep], y[dep])
        nx = len(x[dep])
        ny = len(y[dep])
        U2 = nx * ny - U1
        # print(U1, U2)

        # U is the smallest of the U values
        U = U1 if U1 < U2 else U2
        effect = 1 - ((2 * U) / (nx * ny))
        # print(dep, res, res.statistic)
        #
        print(
            f"{dep} -- mean(x):{x[dep].mean():.2f}, mean(y):{y[dep].mean():.2f} U1:{U1}, p:{p}, n1:{nx} n2:{ny} effect: {effect:.3}")
        # plt.hist(far50[dep], edgecolor='black', bins=20)
        # plt.show()
        # plt.hist(far86[dep], edgecolor='black', bins=20)


def analyze_fastest_quantile(users):
    print("---- Comparison of all participants")
    # group 1 = 50% FAR, group 3 = 86% FAR
    far50 = users[users['group'] == 1]
    far86 = users[users['group'] == 3]

    deps = ['time_on_task', 'sensitivity', 'precision', 'correctness', 'specificity', 'confidence']
    compute_stats(far50, far86, deps)

    print("---- Comparison excluding fastest 25% of participants")
    # group 1 = 50% FAR, group 3 = 86% FAR
    df = users.copy()
    df = df[df['25th percentile'] == False]

    far50 = df[df['group'] == 1]
    far86 = df[df['group'] == 3]

    compute_stats(far50, far86, deps)

    quantiles = [0.1, 0.15, 0.2, 0.25, 0.30]

    for q in quantiles:
        df = users.copy()

        print(f"---- Fastest {q * 100:.0f}% vs others")

        quart = np.quantile(users.time_on_task, q)
        print(f"Time on task {q * 100:.0f}th percentile: {quart:.2f} minutes")
        df['in_quantile'] = np.where(df.time_on_task <= quart, True, False)

        far50 = df[df['group'] == 1]
        far86 = df[df['group'] == 3]

        print('=== 50% FAR ===')
        compute_stats(far50[far50['in_quantile'] == True], far50[far50['in_quantile'] == False], deps)

        print('=== 86% FAR ===')
        compute_stats(far86[far86['in_quantile'] == True], far86[far86['in_quantile'] == False], deps)


def _printab(first, second, third):
    if isinstance(second, float) and isinstance(third, float):
        print(f'{first:<10} {second:>7.2f} {third:>7.2f}')
    else:
        print(f'{str(first):10} {str(second):>10} {str(third):>10}')


def performance_basic_stats(_df: pd.DataFrame, cols: List[str]):
    df = _df.copy()

    far50 = df[df['group'] == 1]
    far86 = df[df['group'] == 3]

    _printab(' ', "50% FAR", "86% FAR")
    _printab('n', len(far50), len(far86))

    for o in cols:
        print(o, '-----')
        _printab('mean', far50[o].mean(), far86[o].mean())
        _printab('median', far50[o].median(), far86[o].median())
        _printab('\u03C3', far50[o].std(), far86[o].std())
        _printab('min', far50[o].min(), far86[o].min())
        _printab('max', far50[o].max(), far86[o].max())


if __name__ == "__main__":

    excel_dir = Path('excel')
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)

    # Use the patched workbook, which correctly labels the 4 eurotrip alerts as TRUE alarms
    _filename = 'cry-wolf_20200125_14-35-09_patched'
    _users = compute_results(_filename)

    # analyze_fastest_quantile(_users)
    decision_time = event_decision_time(_filename, _users[['username', 'group', '25th percentile']])

    tlx(_filename, _users[['username', 'group', '25th percentile']])
    # performance_basic_stats(_users, ['sensitivity', 'precision', 'time_on_task'])

    exit(0)

    excel_file = excel_dir / f"{_filename}_decision_time.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl', datetime_format='hh:mm:ss') as writer:
        decision_time.to_excel(writer, sheet_name="event_decision_time", index=False)

    excel_file = excel_dir / f"{_filename}_analysis.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl', datetime_format='hh:mm:ss') as writer:
        _users.to_excel(writer, sheet_name="users", index=False)
