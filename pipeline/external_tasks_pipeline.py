import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import pandas as pd
from models import db, Task
from acttask import actTask  # import your Flask app
from datetime import datetime, timezone

API_URL = "https://jsonplaceholder.typicode.com/todos"

def run_pipeline():
    with actTask.app_context():

        print("Starting pipeline...")

        # Extract
        response = requests.get(API_URL)
        raw_data = response.json()

        print(f"Extracted {len(raw_data)} records")

        # Transform
        df = pd.DataFrame(raw_data)

        # Normalize schema
        df["title"] = df["title"].fillna("Untitled")
        df["status"] = df["completed"].apply(lambda x: "Completed" if x else "Pending")

        # Add missing fields
        df["description"] = "Imported from external API"
        df["deadline"] = datetime.now(timezone.utc)
        df["owner"] = 1  

        # Remove duplicates
        df = df.drop_duplicates(subset=["title", "owner"])

        print(f"Transformation complete: {len(df)} records ready")

        # Load
        inserted = 0

        for _, row in df.iterrows():
            exists = db.session.query(Task).filter_by(title=row["title"]).first()

            if not exists:
                new_task = Task(
                    title=row["title"],
                    description=row["description"],
                    deadline=row["deadline"],
                    owner=row["owner"],
                    status=row["status"]
                )
                db.session.add(new_task)
                inserted += 1

        db.session.commit()

        print(f"Loaded {inserted} new records into database")
        print("Pipeline completed")

if __name__ == "__main__":
    run_pipeline()