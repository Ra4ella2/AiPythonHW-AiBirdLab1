import csv
import sqlite3
from datetime import datetime

import httpx

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware

AI_SERVER_URL = "http://127.0.0.1:8001/predict"
DATABASE = "birds.db"
CSV_FILE = "bird_analysis.csv"


app = FastAPI(
    title="AI Bird Lab Central Server"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#DATABASE

def get_db():
    return sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )


def create_database():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS birds(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT,
            predicted_species TEXT,
            confidence REAL,
            analysis_date TEXT
        )
    """)

    db.commit()
    db.close()


create_database()

@app.get("/")
def home():
    return {
        "message": "AI Bird Lab Backend працює"
    }


#ANALYZE IMAGE

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    extension = file.filename.lower()

    if not (
        extension.endswith(".jpg")
        or extension.endswith(".jpeg")
        or extension.endswith(".png")
    ):
        raise HTTPException(
            status_code=400,
            detail="Підтримуються тільки JPG, JPEG та PNG"
        )

    file_bytes = await file.read()

    try:
        async with httpx.AsyncClient() as client:

            response = await client.post(
                AI_SERVER_URL,
                files={
                    "file": (
                        file.filename,
                        file_bytes,
                        file.content_type
                    )
                },
                timeout=60
            )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI Server недоступний: {error}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    data = response.json()

    results = data["results"]

    best = results[0]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO birds(
            image_name,
            predicted_species,
            confidence,
            analysis_date
        )
        VALUES (?, ?, ?, ?)
    """, (
        file.filename,
        best["species"],
        best["confidence"],
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    record_id = cur.lastrowid

    db.commit()
    db.close()

    return {
        "id": record_id,
        "image_name": file.filename,
        "best_result": best,
        "top_3": results
    }


#HISTORY

@app.get("/history")
def history():

    db = get_db()
    cur = db.cursor()

    rows = cur.execute("""
        SELECT
            id,
            image_name,
            predicted_species,
            confidence,
            analysis_date
        FROM birds
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return [
        {
            "id": row[0],
            "image_name": row[1],
            "predicted_species": row[2],
            "confidence": row[3],
            "analysis_date": row[4]
        }
        for row in rows
    ]


#GET ONE RECORD

@app.get("/birds/{bird_id}")
def get_bird(bird_id: int):

    db = get_db()
    cur = db.cursor()

    row = cur.execute("""
        SELECT
            id,
            image_name,
            predicted_species,
            confidence,
            analysis_date
        FROM birds
        WHERE id = ?
    """, (
        bird_id,
    )).fetchone()

    db.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Запис не знайдено"
        )

    return {
        "id": row[0],
        "image_name": row[1],
        "predicted_species": row[2],
        "confidence": row[3],
        "analysis_date": row[4]
    }


#SEARCH

@app.get("/search")
def search(name: str):

    db = get_db()
    cur = db.cursor()

    rows = cur.execute("""
        SELECT
            id,
            image_name,
            predicted_species,
            confidence,
            analysis_date
        FROM birds
        WHERE predicted_species LIKE ?
    """, (
        f"%{name}%",
    )).fetchall()

    db.close()

    return [
        {
            "id": row[0],
            "image_name": row[1],
            "predicted_species": row[2],
            "confidence": row[3],
            "analysis_date": row[4]
        }
        for row in rows
    ]

#DELETE

@app.delete("/birds/{bird_id}")
def delete_bird(bird_id: int):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        DELETE FROM birds
        WHERE id = ?
    """, (
        bird_id,
    ))

    deleted = cur.rowcount

    db.commit()
    db.close()

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Запис не знайдено"
        )

    return {
        "message": "Запис видалено"
    }


#STATISTICS

@app.get("/statistics")
def statistics():

    db = get_db()
    cur = db.cursor()

    total = cur.execute("""
        SELECT COUNT(*)
        FROM birds
    """).fetchone()[0]

    most_common = cur.execute("""
        SELECT
            predicted_species,
            COUNT(*) AS count
        FROM birds
        GROUP BY predicted_species
        ORDER BY count DESC
        LIMIT 1
    """).fetchone()

    highest = cur.execute("""
        SELECT
            predicted_species,
            confidence
        FROM birds
        ORDER BY confidence DESC
        LIMIT 1
    """).fetchone()

    lowest = cur.execute("""
        SELECT
            predicted_species,
            confidence
        FROM birds
        ORDER BY confidence ASC
        LIMIT 1
    """).fetchone()

    db.close()

    return {
        "total_images": total,

        "most_common_species": (
            {
                "species": most_common[0],
                "count": most_common[1]
            }
            if most_common
            else None
        ),

        "highest_confidence": (
            {
                "species": highest[0],
                "confidence": highest[1]
            }
            if highest
            else None
        ),

        "lowest_confidence": (
            {
                "species": lowest[0],
                "confidence": lowest[1]
            }
            if lowest
            else None
        )
    }

#CSV

@app.post("/export")
def export_csv():

    db = get_db()
    cur = db.cursor()

    rows = cur.execute("""
        SELECT
            image_name,
            predicted_species,
            confidence,
            analysis_date
        FROM birds
    """).fetchall()

    db.close()

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "image_name",
            "predicted_species",
            "confidence",
            "analysis_date"
        ])

        writer.writerows(rows)

    return {
        "message": "CSV створено",
        "file": CSV_FILE,
        "records": len(rows)
    }

#uvicorn backend:app --port 8000