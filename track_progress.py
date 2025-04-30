#!/usr/bin/env python3
import pandas as pd
from datetime import date
import os, re, math

# ───── CONFIGURATION ────────────────────────────────────────────────────────────
FILE_PATH       = 'sprint_tracker.xlsx'

# Sheet names (ensure you manually add a 'Progress' sheet)
SHEET_PROGRESS  = 'Progress'
SHEET_LOG       = 'Daily Log'
SHEET_SUM       = 'Daily Summary'
SHEET_MONTHLY   = 'Monthly OKRs'
SHEET_QUARTERLY = 'Quarterly OKRs'

# When did Month 1 start? (e.g. April=4)
START_MONTH = 4

# ───── Block definitions ───────────────────────────────────────────────────────
BLOCKS = {
    'Block 1':  'SQL Mastery (Data-Eng)',
    'Block 2':  'Python ETL (Data-Eng)',
    'Block 3':  'A – Vocabulaire',
    'Block 4':  'ETL Project (Data-Eng)',
    'Block 5':  'B – Grammatica',
    'Block 6':  'Sys-Design Quickfire (Data-Eng)',
    'Block 7':  'C – Lesson videos – Exam',
    'Block 8':  'D1 – Monologue practice',
    'Block 9':  'Build & Broadcast clip (Data-Eng)',
    'Block 10': 'Family & Fun',
    'Block 11': 'D2 – Dialogue practice',
}

# ───── KR ↔ Block mapping ──────────────────────────────────────────────────────
KR_MAPPING = {
    # Monthly OKRs
    'Complete 8 SQL Mastery modules':        'Block 1',
    'Learn 200 new Dutch words':             'Block 3',
    'Finish present tense grammar':          'Block 5',
    'Build 2 ETL pipelines':                 'Block 4',
    'Learn 300 new Dutch words':             'Block 3',
    'Complete past tense & word order':      'Block 5',
    'Finish 10 Sys-Design quickfires':       'Block 6',
    'Average ≥60% on listening tests':       'Block 7',
    'Hold 3 monologues >5min each':          'Block 8',
    'Deploy one ETL project to Cloud':       'Block 4',
    'Complete 2 mock reading tests':         'Block 7',
    'Score ≥60% on mock writing tests':      'Block 7',
    'Submit one SQL tutorial blog':          'Block 9',
    'Learn 400 new Dutch words':             'Block 3',
    'Master subjunctive & relative clauses': 'Block 5',
    'Pass mock Data-Eng cert exam':          'Block 6',
    'Pass B1 mock Dutch exam':               'Block 7',
    'Deliver final ETL & Dutch presentation':'Block 2',
    # Quarterly OKRs
    'Finish GCP Data Eng certification':     'Block 6',
    'Ship 2 end-to-end ETL projects':        'Block 4',
    'Present one internal talk/article':     'Block 9',
    'Complete 2 mock Staatsexamen NT2 tests':'Block 7',
    'Sustain 30 min/day active Dutch for 90 days':'Block 3',
    'Pass internal B1 placement':            'Block 7',
    'Master complex grammar cases':          'Block 5',
    'Hold 5 tutored conversations ≥10 min':  'Block 8',
}

# ───── Helpers ─────────────────────────────────────────────────────────────────

def load_sheets():
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"{FILE_PATH} not found")
    xls = pd.ExcelFile(FILE_PATH)
    # Progress sheet
    if SHEET_PROGRESS in xls.sheet_names:
        prog_df = pd.read_excel(FILE_PATH, sheet_name=SHEET_PROGRESS)
        expected = ['Date'] + list(BLOCKS.keys())
        if not all(col in prog_df.columns for col in expected):
            prog_df = pd.DataFrame(columns=expected)
    else:
        prog_df = pd.DataFrame(columns=['Date'] + list(BLOCKS.keys()))
    # Other sheets
    log_df = pd.read_excel(FILE_PATH, sheet_name=SHEET_LOG)
    sum_df = pd.read_excel(FILE_PATH, sheet_name=SHEET_SUM)
    mon_df = pd.read_excel(FILE_PATH, sheet_name=SHEET_MONTHLY)
    qtr_df = pd.read_excel(FILE_PATH, sheet_name=SHEET_QUARTERLY)
    return prog_df, log_df, sum_df, mon_df, qtr_df


def prompt_progress(prog_df):
    today = date.today().strftime('%Y-%m-%d')
    if today in prog_df['Date'].astype(str).values:
        idx = prog_df.index[prog_df['Date'].astype(str) == today][0]
    else:
        blank = {'Date': today, **{b: '' for b in BLOCKS}}
        prog_df = pd.concat([prog_df, pd.DataFrame([blank])], ignore_index=True)
        idx = prog_df.index[-1]
    print(f"\nTracking progress for {today}\n" + "-"*30)
    for b, desc in BLOCKS.items():
        ans = input(f"✔ Did you complete {b} ({desc})? [y/N] ").strip().lower()
        prog_df.at[idx, b] = '✔' if ans == 'y' else ''
    return prog_df


def update_daily_log(prog_df, log_df):
    template = log_df.loc[log_df['Date'] == log_df['Date'].min()].copy()
    today = date.today()
    template['Date'] = pd.to_datetime(today)
    done_blocks = set(prog_df.loc[prog_df['Date'] == today.strftime('%Y-%m-%d'), BLOCKS.keys()].stack()[lambda x: x == '✔'].index.get_level_values(1))
    template['Done'] = template['Block'].fillna('').isin(done_blocks)
    log_df = log_df[log_df['Date'] != template['Date'].iloc[0]]
    return pd.concat([log_df, template], ignore_index=True)


def update_daily_summary(prog_df, sum_df):
    if prog_df.empty:
        return sum_df
    last = prog_df.iloc[-1]
    today_str = last['Date']
    done = sum(1 for b in BLOCKS if last.get(b) == '✔')
    total = len(BLOCKS)
    pct   = int(round(done / total * 100)) if total else 0
    bar   = '█' * (pct // 5) + '░' * (20 - pct // 5)
    temp = sum_df.copy()
    temp['Date_str'] = temp['Date'].astype(str)
    temp = temp[temp['Date_str'] != today_str]
    temp = temp.drop(columns=['Date_str'], errors='ignore')
    new_row = pd.DataFrame([{ 'Date':         today_str,
                               'Total':        total,
                               'Completed':    done,
                               'Progress (%)': f"{pct}%",
                               'Progress Bar': bar }])
    return pd.concat([temp, new_row], ignore_index=True)


def update_monthly_okrs(prog_df, mon_df):
    today = date.today()
    mi = today.month - START_MONTH + 1
    label = f"Month {mi}"
    for i, row in mon_df[mon_df['Month'] == label].iterrows():
        kr = row['Key Result']
        m = re.search(r"\d+", str(row['Target']))
        if not m:
            continue
        tgt = int(m.group())
        block = next((b for k, b in KR_MAPPING.items() if k in kr), None)
        if not block:
            continue
        df2 = prog_df.copy()
        df2['Date'] = pd.to_datetime(df2['Date'])
        done = df2[(df2['Date'].dt.month == today.month) & (df2[block] == '✔')].shape[0]
        pct = int(round(done / tgt * 100))
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        mon_df.at[i, 'Progress (%)'] = f"{pct}%"
        mon_df.at[i, 'Progress Bar'] = bar
    return mon_df


def update_quarterly_okrs(prog_df, qtr_df):
    today = date.today()
    mi = today.month - START_MONTH + 1
    qtr = math.ceil(mi / 3)
    months = list(range(START_MONTH + (qtr - 1) * 3, START_MONTH + qtr * 3))
    for i, row in qtr_df.iterrows():
        kr = row['Key Result']
        m = re.search(r"\d+", str(row['Target']))
        if not m:
            continue
        tgt = int(m.group())
        block = next((b for k, b in KR_MAPPING.items() if k in kr), None)
        if not block:
            continue
        df2 = prog_df.copy()
        df2['Date'] = pd.to_datetime(df2['Date'])
        done = df2[df2['Date'].dt.month.isin(months) & (df2[block] == '✔')].shape[0]
        pct = int(round(done / tgt * 100))
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        qtr_df.at[i, 'Progress (%)'] = f"{pct}%"
        qtr_df.at[i, 'Progress Bar'] = bar
    return qtr_df


def save_all(prog_df, log_df, sum_df, mon_df, qtr_df):
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='w') as writer:
        prog_df.to_excel(writer, sheet_name=SHEET_PROGRESS, index=False)
        log_df.to_excel(writer, sheet_name=SHEET_LOG, index=False)
        sum_df.to_excel(writer, sheet_name=SHEET_SUM, index=False)
        mon_df.to_excel(writer, sheet_name=SHEET_MONTHLY, index=False)
        qtr_df.to_excel(writer, sheet_name=SHEET_QUARTERLY, index=False)
    print(f"\n✅ All sheets updated in {FILE_PATH}")


def main():
    prog_df, log_df, sum_df, mon_df, qtr_df = load_sheets()
    prog_df = prompt_progress(prog_df)
    log_df  = update_daily_log(prog_df, log_df)
    sum_df  = update_daily_summary(prog_df, sum_df)
    mon_df  = update_monthly_okrs(prog_df, mon_df)
    qtr_df  = update_quarterly_okrs(prog_df, qtr_df)
    save_all(prog_df, log_df, sum_df, mon_df, qtr_df)

if __name__ == '__main__':
    main()
