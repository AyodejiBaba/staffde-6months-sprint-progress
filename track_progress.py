#!/usr/bin/env python3
import pandas as pd
from datetime import date
import os, re, math

# ───── CONFIGURATION ────────────────────────────────────────────────────────────
FILE_PATH      = 'sprint_tracker.xlsx'

# sheet names in your workbook
SHEET_PROGRESS = 'Progress'
SHEET_LOG      = 'Daily Log'
SHEET_SUM      = 'Daily Summary'
SHEET_MONTHLY  = 'Monthly OKRs'
SHEET_QUARTERLY= 'Quarterly OKRs'

# When did Month 1 start? (e.g. April = 4)
START_MONTH = 4

# your blocks → human descriptions
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

# map a piece of each Key Result → the Block that drives it
# adjust these substrings & block-IDs to match exactly your OKR wording
KR_MAPPING = {
    'Complete 8 SQL Mastery module':                'Block 1',  # “Complete 8 SQL Mastery modules”
    'Learn 200 new Dutch words':                    'Block 3',  # “Learn 200 new Dutch words”
    'Finish present tense grammar':                 'Block 5',  # “Finish present tense grammar”
    'Build 2 ETL pipelines':                        'Block 4',  # “Build 2 ETL pipelines”
    'Learn 300 new Dutch words':                    'Block 3',
    'Complete past tense & word order':             'Block 5',
    'Finish 10 Sys‑Design quickfires':              'Block 6',
    'Average ≥60% on listening tests':              'Block 7',
    'Hold 3 monologues >5min each':                 'Block 8',
    'Deploy one ETL project to Cloud':              'Block 4',
    'Complete 2 mock reading tests':                'Block 7',
    'Score ≥60% on mock writing tests':             'Block 7',
    'Submit one SQL tutorial blog':                 'Block 9',
    'Learn 400 new Dutch words':                    'Block 3',
    'Master subjunctive & relative clauses':        'Block 5',
    'Pass mock Data‑Eng cert exam':                 'Block 6',
    'Pass B1 mock Dutch exam':                      'Block 7',
    'Deliver final ETL & Dutch presentation':       'Block 2'
}

# ─────— helper functions —──────────────────────────────────────────────────────

def load_sheets():
    return pd.read_excel(FILE_PATH, sheet_name=[SHEET_PROGRESS, SHEET_LOG, SHEET_SUM, SHEET_MONTHLY, SHEET_QUARTERLY])

def prompt_progress(df):
    """Prompt for each Block; write '✔' or ''. """
    today = date.today().strftime('%Y-%m-%d')
    if today in df['Date'].astype(str).values:
        idx = df.index[df['Date'].astype(str)==today][0]
    else:
        row = {'Date': today, **{b:'' for b in BLOCKS}}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        idx = df.index[-1]

    print(f"\nTracking {today}\n" + "-"*30)
    for b, desc in BLOCKS.items():
        ans = input(f"✔ Did you complete {b} ({desc})? [y/N] ").strip().lower()
        df.at[idx, b] = '✔' if ans=='y' else ''
    return df

def update_daily_log(progress, log):
    """Rebuild today’s section of Daily Log from the first‐seen date as template."""
    # pick the very first date in the existing log as a “template”
    template_date = log['Date'].min()
    tpl = log[log['Date']==template_date].copy()
    tpl['Date'] = pd.to_datetime(date.today())
    # map Done by Block
    done_blocks = {b for b,v in progress.items() if v=='✔'}
    tpl['Done'] = tpl['Block'].fillna('').map(lambda b: b in done_blocks)
    # replace today
    log = log[log['Date'] != tpl['Date'].iloc[0]]
    return pd.concat([log, tpl], ignore_index=True)

def update_daily_summary(log, summary):
    today = pd.to_datetime(date.today())
    today_log = log[log['Date']==today]
    total     = len(today_log)
    completed = today_log['Done'].sum()
    pct       = int(round( completed/total*100 )) if total else 0
    bar       = '█'*(pct//5) + '░'*(20 - pct//5)

    # drop old row for today
    summary = summary[summary['Date'].dt.date != today.date()]
    new = {'Date': today, 'Total': total, 'Completed': completed,
           'Progress (%)': f"{pct}%", 'Progress Bar': bar}
    return pd.concat([summary, pd.DataFrame([new])], ignore_index=True)

def update_monthly_okrs(progress_df, monthly):
    """Update only the rows matching the current Month N."""
    today = date.today()
    mi    = today.month - START_MONTH + 1
    label = f"Month {mi}"
    m_idx = monthly['Month']==label

    for i,row in monthly[m_idx].iterrows():
        kr     = row['Key Result']
        target = int(re.search(r'\d+', str(row['Target'])).group())
        # find which block drives this KR
        block = next((b for k,b in KR_MAPPING.items() if k in kr), None)
        if not block: continue
        # count how many ✔ in that block this month
        df = progress_df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        mask = df['Date'].dt.month == today.month
        done = df[mask & (df[block]=='✔')].shape[0]
        pct  = int(round(done/target*100))
        bar  = '█'*(pct//5) + '░'*(20 - pct//5)

        monthly.at[i,'Progress (%)'] = f"{pct}%"
        monthly.at[i,'Progress Bar'] = bar

    return monthly

def update_quarterly_okrs(progress_df, quarterly):
    """Update every row based on Q-aggregates."""
    today = date.today()
    mi    = today.month - START_MONTH + 1
    q     = math.ceil(mi/3)
    start = START_MONTH + (q-1)*3
    months = list(range(start, start+3))

    for i,row in quarterly.iterrows():
        kr     = row['Key Result']
        target = int(re.search(r'\d+', str(row['Target'])).group())
        block  = next((b for k,b in KR_MAPPING.items() if k in kr), None)
        if not block: continue
        df = progress_df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        done = df[df['Date'].dt.month.isin(months) & (df[block]=='✔')].shape[0]
        pct  = int(round(done/target*100))
        bar  = '█'*(pct//5) + '░'*(20 - pct//5)

        quarterly.at[i,'Progress (%)'] = f"{pct}%"
        quarterly.at[i,'Progress Bar'] = bar

    return quarterly

def save_all(dfs):
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='w') as w:
        dfs[SHEET_PROGRESS].to_excel(w, sheet_name=SHEET_PROGRESS, index=False)
        dfs[SHEET_LOG].     to_excel(w, sheet_name=SHEET_LOG,      index=False)
        dfs[SHEET_SUM].     to_excel(w, sheet_name=SHEET_SUM,      index=False)
        dfs[SHEET_MONTHLY]. to_excel(w, sheet_name=SHEET_MONTHLY,  index=False)
        dfs[SHEET_QUARTERLY].to_excel(w, sheet_name=SHEET_QUARTERLY,index=False)
    print(f"\n✅ All sheets updated in {FILE_PATH}")

# ───── main ────────────────────────────────────────────────────────────────────
def main():
    sheets = load_sheets()
    prog   = prompt_progress( sheets[SHEET_PROGRESS] )
    log    = update_daily_log(prog,   sheets[SHEET_LOG])
    summ   = update_daily_summary(log, sheets[SHEET_SUM])
    month  = update_monthly_okrs(prog, sheets[SHEET_MONTHLY])
    quart  = update_quarterly_okrs(prog, sheets[SHEET_QUARTERLY])

    dfs = {
      SHEET_PROGRESS: prog,
      SHEET_LOG:       log,
      SHEET_SUM:       summ,
      SHEET_MONTHLY:   month,
      SHEET_QUARTERLY: quart
    }
    save_all(dfs)

if __name__=='__main__':
    main()
