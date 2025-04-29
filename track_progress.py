#!/usr/bin/env python3
import pandas as pd
from datetime import date
import os

# ───── Configuration ───────────────────────────────────────────────────────────
FILE_PATH  = 'sprint_tracker.xlsx'
SHEET_NAME = 'Progress'
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

def load_progress():
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
    cols = ['Date'] + list(BLOCKS.keys())
    return pd.DataFrame(columns=cols)

def prompt_and_update(df):
    today = date.today().strftime('%Y-%m-%d')
    if today in df['Date'].astype(str).values:
        idx = df.index[df['Date'].astype(str) == today][0]
    else:
        blank = {'Date': today, **{b: '' for b in BLOCKS}}
        df = pd.concat([df, pd.DataFrame([blank])], ignore_index=True)
        idx = df.index[-1]

    print(f"\nTracking progress for {today}\n" + "-"*30)
    for block, desc in BLOCKS.items():
        ans = input(f"✔ Did you complete {block} ({desc})? [y/N]: ").strip().lower()
        df.at[idx, block] = '✔' if ans == 'y' else ''
    return df

def save_progress(df):
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    print(f"\n✅ Saved to {FILE_PATH}")

def main():
    df = load_progress()
    df = prompt_and_update(df)
    save_progress(df)

if __name__ == '__main__':
    main()
