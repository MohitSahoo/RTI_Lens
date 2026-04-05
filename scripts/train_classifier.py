"""
Trains a LogisticRegression and RandomForest classifier on cases.csv.
Saves the better model to data/model.pkl and data/model_card.json.
"""

import json
import pickle
import warnings
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sqlalchemy import create_engine

warnings.filterwarnings('ignore')

DB_URL = "postgresql://mohitsahoo@localhost:5432/rtilens"

# Export cases.csv first
engine = create_engine(DB_URL)
df = pd.read_sql("""
    SELECT c.order_number, c.section_cited, c.appeal_outcome,
           c.appeal_level, c.order_date, c.raw_text, m.name AS ministry
    FROM cases c
    LEFT JOIN ministries m ON m.id = c.ministry_id
""", engine)

df.to_csv("data/cases.csv", index=False)
print(f"Exported {len(df)} rows to data/cases.csv")

# Filter valid rows
df = df[df['appeal_outcome'].notna()].copy()
df['year'] = pd.to_datetime(df['order_date'], errors='coerce').dt.year.fillna(2020).astype(int)
df['target'] = (df['appeal_outcome'] == 'allowed').astype(int)
df['ministry']      = df['ministry'].fillna('Unknown')
df['section_cited'] = df['section_cited'].fillna('unknown')
df['appeal_level']  = df['appeal_level'].fillna('unknown')
df['raw_text']      = df['raw_text'].fillna('')

print(f"Training on {len(df)} rows. Class distribution:\n{df['target'].value_counts()}")

X = df[['ministry', 'section_cited', 'appeal_level', 'year', 'raw_text']]
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

from sklearn.preprocessing import OneHotEncoder, StandardScaler

preprocessor = ColumnTransformer([
    ('ministry',     TfidfVectorizer(max_features=50),  'ministry'),
    ('section',      TfidfVectorizer(max_features=20),  'section_cited'),
    ('appeal_level', OneHotEncoder(handle_unknown='ignore'), ['appeal_level']),
    ('year',         StandardScaler(), ['year']),
    ('text',         TfidfVectorizer(max_features=500, ngram_range=(1,2)), 'raw_text'),
])

results = {}
for name, clf in [
    ("LogisticRegression", LogisticRegression(max_iter=1000, random_state=42)),
    ("RandomForest",       RandomForestClassifier(n_estimators=100, random_state=42)),
]:
    pipe = Pipeline([('prep', preprocessor), ('clf', clf)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    results[name] = {
        "pipeline": pipe,
        "accuracy": accuracy_score(y_test, preds),
        "f1":       f1_score(y_test, preds, zero_division=0),
    }
    print(f"\n{name}: acc={results[name]['accuracy']:.3f} f1={results[name]['f1']:.3f}")
    print(classification_report(y_test, preds, zero_division=0))

best_name = max(results, key=lambda k: results[k]['f1'])
best      = results[best_name]
print(f"\nBest model: {best_name} (F1={best['f1']:.3f})")

with open("data/model.pkl", "wb") as f:
    pickle.dump(best["pipeline"], f)

model_card = {
    "model_type":         best_name,
    "accuracy":           round(best["accuracy"], 4),
    "f1":                 round(best["f1"], 4),
    "training_size":      len(X_train),
    "test_size":          len(X_test),
    "feature_names":      ['ministry', 'section_cited', 'appeal_level', 'year', 'raw_text'],
    "class_distribution": df['target'].value_counts().to_dict(),
    "low_data_threshold": 10,
    "disclaimer":         "This prediction is based on historical data and is not legal advice.",
}
with open("data/model_card.json", "w") as f:
    json.dump(model_card, f, indent=2)

print("Saved data/model.pkl and data/model_card.json")
