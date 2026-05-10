"""
Load cases from CSV into SQLite database
"""
import csv
import sys
from datetime import datetime
from backend.database import SessionLocal
from backend.models import Ministry, Case
from backend.enums import AppealOutcome, AppealLevel, ExtractionMethod

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

def load_cases():
    db = SessionLocal()

    # Load ministries first
    ministry_map = {}

    print("Loading cases from CSV...")
    with open('data/cases.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            # Get or create ministry
            ministry_name = row['ministry'].strip()
            if ministry_name not in ministry_map:
                ministry = db.query(Ministry).filter(Ministry.name == ministry_name).first()
                if not ministry:
                    ministry = Ministry(name=ministry_name)
                    db.add(ministry)
                    db.flush()
                ministry_map[ministry_name] = ministry.id

            # Parse date
            order_date = None
            if row['order_date']:
                try:
                    order_date = datetime.strptime(row['order_date'], '%Y-%m-%d').date()
                except:
                    pass

            # Parse outcome
            outcome = None
            if row['appeal_outcome']:
                try:
                    outcome = AppealOutcome(row['appeal_outcome'])
                except:
                    pass

            # Parse level
            level = None
            if row['appeal_level']:
                try:
                    level = AppealLevel(row['appeal_level'])
                except:
                    pass

            # Create case
            case = Case(
                order_number=row['order_number'],
                ministry_id=ministry_map[ministry_name],
                section_cited=row['section_cited'] if row['section_cited'] else None,
                appeal_outcome=outcome,
                appeal_level=level,
                order_date=order_date,
                extraction_method=ExtractionMethod.TXT,
                raw_text=row['raw_text']
            )
            db.add(case)

            count += 1
            if count % 1000 == 0:
                db.commit()
                print(f"Loaded {count} cases...")

        db.commit()
        print(f"Done! Loaded {count} cases total.")

    db.close()

if __name__ == "__main__":
    load_cases()
