# ActTask

A backend-focused task management system with integrated AI planning and an idempotent ETL pipeline for external data ingestion.

---

## Overview

ActTask is a Flask-based backend system designed to manage user tasks while demonstrating real-world backend and data engineering concepts, including API design, authentication, data processing, and pipeline-based ingestion.

---

## Key Features

### Core Backend
- RESTful API for task management (Create, Read, Update, Delete)
- JWT-based authentication for secure multi-user access
- Pagination, filtering, and search support
- Task statistics aggregation (completed, pending, overdue)

### Data Engineering (ETL Pipeline)
- External data ingestion from REST APIs (JSONPlaceholder)
- Data transformation and normalization (status mapping, null handling)
- Batch loading into relational database (SQLite)
- Idempotent pipeline design (prevents duplicate records across runs)

### AI Integration
- LLM-powered daily task planner
- Multi-step refinement loop (generate → critique → improve)
- Scoring system based on realism, prioritization, and clarity
- Latency and evaluation logging for each AI interaction

---

## Tech Stack

- **Backend:** Flask, SQLAlchemy  
- **Database:** SQLite  
- **Data Processing:** Pandas  
- **Authentication:** JWT (flask-jwt-extended)  
- **AI Integration:** OpenRouter (LLM APIs)  
- **Other:** Docker (environment setup), REST APIs  

---

## ETL Pipeline Details

- Extracts ~200 task records from external API
- Transforms data into internal schema
- Loads data with deduplication logic:
  - Prevents duplicate inserts on repeated runs
- Designed to be idempotent and safe for re-execution

Run pipeline:

```bash
python pipeline/external_tasks_pipeline.py