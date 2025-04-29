#!/usr/bin/env python3
import pandas as pd
from datetime import date
import os, re, math

# ───── CONFIGURATION ────────────────────────────────────────────────────────────
FILE_PATH       = 'sprint_tracker.xlsx'

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
    # ---- Monthly OKRs ----
    'Complete 8 SQL Mastery modules':       'Block 1',
    'Learn 200 new Dutch words':            'Block 3',
    'Finish present tense grammar':         'Block 5',
    'Build 2 ETL pipelines':                'Block 4',
    'Learn 300 new Dutch words':            'Block 3',
    'Complete past tense & word order':     'Block 5',
    'Finish 10 Sys-Design quickfires':      'Block 6',
    'Average ≥60% on listening tests':      'Block 7',
    'Hold 3 monologues >5min each':         'Block 8',
    'Deploy one ETL project to Cloud':      'Block 4',
    'Complete 2 mock reading tests':        'Block 7',
    'Score ≥60% on mock writing tests':     'Block 7',
    'Submit one SQL tutorial blog':         'Block 9',
    'Learn 400 new Dutch words':            'Block 3',
    'Master subjunctive & relative clauses':'Block 5',
    'Pass mock Data-Eng cert exam':         'Block 6',
    'Pass B1 mock Dutch exam':              'Block 7',
    'Deliver final ETL & Dutch presentation':'Block 2',

    # ---- Quarterly OKRs (additions) ----
    'Finish GCP Data Eng certification':        'Block 6',  # Data-Eng cert prep
    'Ship 2 end-to-end ETL projects':           'Block 4',
    'Present one internal talk/article':        'Block 9',
    'Complete 2 mock Staatsexamen NT2 tests':   'Block 7',
    'Sustain 30 min/day active Dutch for 90 days':'Block 3',
    'Pass internal B1 placement':               'Block 7',
    'Master complex grammar cases':             'Block 5',
    'Hold 5 tutored conversations ≥10 min':     'Block 8',
}

# ─────— Helpers —───────────────────────────────────────────────────────────────

def load_sheets():
    return pd.read_excel(FILE_PATH, sheet_name=[SHEET_PROGRESS, SHEET_LOG,
                                               SHEET_SUM, SHEET_MONTHLY,
                                               SHEET_QUARTERLY])

def prompt_progress(df):
    today = date.today().strftime('%Y-%m-%d')
    if today in df['Date'].astype(str).values:
        idx = df.index[df['Date'].astype(str)==today][0]
    else:
        blank = {'Date': today, **{b:'' for b in BLOCKS}}
        df = pd.concat([df, pd.DataFrame([blank])], ignore_index=True)
        idx = df.index[-1]

    print(f"\nTracking progress for {today}\n" + "-"*30)
    for b, desc in BLOCKS.items():
        ans = input(f"✔ Did you complete {b} ({desc})? [y/N] ").strip().lower()
        df.at[idx, b] = '✔' if ans=='y' else ''
    return df

def update_daily_log(prog_df, log_df):
    # use first date as template
    template = log_df[log_df['Date']==log_df['Date'].min()].copy()
    template['Date'] = pd.to_datetime(date.today())
    done = {b for b,v in prog_df.iloc[-1].items() if v=='✔'}
    template['Done'] = template['Block'].fillna('').isin(done)
    # replace today
    log_df = log_df[log_df['Date']!=template['Date'].iloc[0]]
    return pd.concat([log_df, template], ignore_index=True)

def update_daily_summary(log_df, sum_df):
    today = pd.to_datetime(date.today())
    today_log = log_df[log_df['Date']==today]
    total     = len(today_log)
    done      = today_log['Done'].sum()
    pct       = int(round(done/total*100)) if total else 0
    bar       = '█'*(pct//5) + '░'*(20-pct//5)
    sum_df    = sum_df[sum_df['Date'].dt.date!=today.date()]
    new_row   = {'Date': today, 'Total': total,
                 'Completed': done,
                 'Progress (%)': f"{pct}%", 'Progress Bar': bar}
    return pd.concat([sum_df, pd.DataFrame([new_row])], ignore_index=True)

def update_monthly_okrs(prog_df, mon_df):
    today = date.today()
    mi    = today.month - START_MONTH + 1
    label = f"Month {mi}"
    mask  = mon_df['Month']==label

    for i, row in mon_df[mask].iterrows():
        kr     = row['Key Result']
        tgt    = int(re.search(r'\d+', str(row['Target'])).group())
        block  = next((b for k,b in KR_MAPPING.items() if k in kr), None)
        if not block: continue

        df2 = prog_df.copy()
        df2['Date'] = pd.to_datetime(df2['Date'])
        done = df2[(df2['Date'].dt.month==today.month) & (df2[block]=='✔')].shape[0]
        pct  = int(round(done/tgt*100))
        bar  = '█'*(pct//5) + '░'*(20-pct//5)

        mon_df.at[i,'Progress (%)'] = f"{pct}%"
        mon_df.at[i,'Progress Bar'] = bar

    return mon_df

def update_quarterly_okrs(prog_df, q_df):
    today = date.today()
    mi    = today.month - START_MONTH + 1
    q     = math.ceil(mi/3)
    start = START_MONTH + (q-1)*3
    months= list(range(start, start+3))

    for i, row in q_df.iterrows():
        kr     = row['Key Result']
        tgt    = int(re.search(r'\d+', str(row['Target'])).group())
        block  = next((b for k,b in KR_MAPPING.items() if k in kr), None)
        if not block: continue

        df2 = prog_df.copy()
        df2['Date'] = pd.to_datetime(df2['Date'])
        done = df2[df2['Date'].dt.month.isin(months) & (df2[block]=='✔')].shape[0]
        pct  = int(round(done/tgt*100))
        bar  = '█'*(pct//5) + '░'*(20-pct//5)

        q_df.at[i,'Progress (%)'] = f"{pct}%"
        q_df.at[i,'Progress Bar'] = bar

    return q_df

def save_all(dfs):
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='w') as w:
        dfs[SHEET_PROGRESS].to_excel(w, sheet_name=SHEET_PROGRESS, index=False)
        dfs[SHEET_LOG].to_excel(w, sheet_name=SHEET_LOG, index=False)
        dfs[SHEET_SUM].to_excel(w, sheet_name=SHEET_SUM, index=False)
        dfs[SHEET_MONTHLY].to_excel(w, sheet_name=SHEET_MONTHLY, index=False)
        dfs[SHEET_QUARTERLY].to_excel(w, sheet_name=SHEET_QUARTERLY, index=False)
    print(f"\n✅ All sheets updated in {FILE_PATH}")

def main():
    sheets = load_sheets()
    prog   = prompt_progress(sheets[SHEET_PROGRESS])
    log    = update_daily_log(prog, sheets[SHEET_LOG])
    summ   = update_daily_summary(log, sheets[SHEET_SUM])
    mon    = update_monthly_okrs(prog, sheets[SHEET_MONTHLY])
    quart  = update_quarterly_okrs(prog, sheets[SHEET_QUARTERLY])

    dfs = {
        SHEET_PROGRESS:  prog,
        SHEET_LOG:       log,
        SHEET_SUM:       summ,
        SHEET_MONTHLY:   mon,
        SHEET_QUARTERLY: quart
    }
    save_all(dfs)

if __name__=='__main__':
    main()
