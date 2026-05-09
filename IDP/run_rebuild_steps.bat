@echo off
REM Step-by-step rebuild with verification
REM Run from: C:\Users\WIN11\Downloads\IDP 2\IDP\IDP

echo.
echo ========================================
echo Step-by-Step Rebuild Process
echo ========================================
echo.

cd "C:\Users\WIN11\Downloads\IDP 2\IDP\IDP"

echo [STEP 1/5] Cleaning and Ingesting to PostgreSQL...
python -c "from sqlalchemy import create_engine, text; from pathlib import Path; import json; from datetime import datetime; import hashlib; from tqdm import tqdm; engine = create_engine('postgresql://mohitsahoo@localhost:5432/rtilens'); conn = engine.connect(); print('Cleaning PostgreSQL...'); [conn.execute(text(f'DELETE FROM {t}')) or conn.commit() for t in ['workflow_actions', 'workflow_sessions', 'paragraphs', 'section_stats', 'ministry_stats', 'cases', 'ministries']]; print('Loading JSONL...'); cases = [json.loads(line) for line in open('clean_cases_final_balanced.jsonl', 'r', encoding='utf-8')]; print(f'Processing {len(cases)} cases...'); ministry_cache = {}; def get_ministry(name): name = name or 'Unknown Ministry'; if name in ministry_cache: return ministry_cache[name]; result = conn.execute(text('SELECT id FROM ministries WHERE name = :name'), {'name': name}).fetchone(); if result: mid = result[0]; else: mid = conn.execute(text('INSERT INTO ministries (name) VALUES (:name) RETURNING id'), {'name': name}).fetchone()[0]; conn.commit(); ministry_cache[name] = mid; return mid; [conn.execute(text('INSERT INTO cases (order_number, ministry_id, section_cited, appeal_outcome, appeal_level, order_date, extraction_method, raw_text) VALUES (:on, :mid, :sc, :ao, :al, :od, :em, :rt)'), {'on': c.get('metadata', {}).get('order_number', c.get('case_id')), 'mid': get_ministry(c.get('metadata', {}).get('ministry')), 'sc': c.get('metadata', {}).get('section_cited'), 'ao': c.get('metadata', {}).get('appeal_outcome'), 'al': c.get('metadata', {}).get('appeal_level'), 'od': None, 'em': 'jsonl', 'rt': c.get('clean_text') or c.get('raw_text', '')}) or conn.commit() for c in tqdm(cases, desc='Ingesting')]; conn.close(); print('Step 1 complete!')"

if %errorlevel% neq 0 (
    echo [ERROR] Step 1 failed!
    pause
    exit /b 1
)

echo.
echo [VERIFY] Checking PostgreSQL...
python -c "from sqlalchemy import create_engine, text; engine = create_engine('postgresql://mohitsahoo@localhost:5432/rtilens'); conn = engine.connect(); print(f'Cases: {conn.execute(text(\"SELECT COUNT(*) FROM cases\")).scalar()}'); print(f'Ministries: {conn.execute(text(\"SELECT COUNT(*) FROM ministries\")).scalar()}'); conn.close()"

echo.
pause

echo.
echo [STEP 2/5] Creating Markdown files and MongoDB documents...
python rebuild_from_jsonl.py

pause
