# Verbesserte import_data.py
import base64
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
import io
from utils.chat_api import get_db

app = FastAPI()

@app.post("/import/events")
async def import_events(user_id: int, file_type: str = Query("csv"), file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        if file_type == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:  # Excel
            try:
                df = pd.read_excel(io.BytesIO(content))
            except ImportError as e:
                if "openpyxl" in str(e):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Excel-Import nicht möglich: Das Paket 'openpyxl' ist nicht installiert.",
                            "solution": "Führe 'pip install openpyxl' aus oder verwende CSV-Format."
                        }
                    )

        # Validierung
        if df.empty:
            return JSONResponse(status_code=400, content={"error": "Die Datei enthält keine Daten."})

        required = {"Titel", "Beschreibung"}  # Minimale Anforderungen
        optional = {"Aufgabe Titel", "Aufgabe Inhalt", "Event ID", "Aufgabe ID"}
        
        if not required.issubset(df.columns):
            return JSONResponse(
                status_code=400, 
                content={
                    "error": f"Fehlende Spalten: {', '.join(required - set(df.columns))}",
                    "required": list(required),
                    "found": list(df.columns)
                }
            )

        db = get_db()
        imported_events = 0
        imported_tasks = 0
        
        try:
            # Gruppiere nach Event-Titel um Duplikate zu vermeiden
            events_processed = set()
            
            for index, row in df.iterrows():
                try:
                    title = str(row["Titel"]).strip() if pd.notna(row["Titel"]) else ""
                    description = str(row["Beschreibung"]).strip() if pd.notna(row["Beschreibung"]) else ""
                    
                    if not title:
                        continue

                    # Event erstellen (nur einmal pro Titel)
                    event_id = None
                    if title not in events_processed:
                        # Prüfe ob Event bereits existiert
                        existing_event = db.execute(
                            "SELECT id FROM events WHERE title=? AND user_id=?", 
                            (title, user_id)
                        ).fetchone()
                        
                        if existing_event:
                            event_id = existing_event["id"]
                        else:
                            # Neues Event erstellen
                            cursor = db.execute(
                                    "INSERT INTO events (user_id, title, description, is_imported) VALUES (?, ?, ?, 1)",
                                    (user_id, title, description)
                                )
                            event_id = cursor.lastrowid
                            imported_events += 1
                        
                        events_processed.add(title)
                    else:
                        # Event-ID für bereits verarbeitetes Event finden
                        event_result = db.execute(
                            "SELECT id FROM events WHERE title=? AND user_id=?", 
                            (title, user_id)
                        ).fetchone()
                        if event_result:
                            event_id = event_result["id"]

                    # Aufgabe hinzufügen (falls vorhanden)
                    if event_id and "Aufgabe Titel" in row and pd.notna(row["Aufgabe Titel"]):
                        task_title = str(row["Aufgabe Titel"]).strip()
                        task_content = str(row["Aufgabe Inhalt"]).strip() if "Aufgabe Inhalt" in row and pd.notna(row["Aufgabe Inhalt"]) else ""
                        
                        if task_title:
                            # Prüfe ob Aufgabe bereits existiert
                            existing_task = db.execute(
                                "SELECT id FROM tasks WHERE event_id=? AND title=?", 
                                (event_id, task_title)
                            ).fetchone()
                            
                            if not existing_task:
                                db.execute(
                                    "INSERT INTO tasks (event_id, title, content) VALUES (?, ?, ?)",
                                    (event_id, task_title, task_content)
                                )
                                imported_tasks += 1

                except Exception as row_error:
                    print(f"Fehler in Zeile {index + 1}: {str(row_error)}")
                    continue

            db.commit()
            
            return {
                "message": "Import erfolgreich abgeschlossen!",
                "imported_events": imported_events,
                "imported_tasks": imported_tasks,
                "total_rows_processed": len(df),
                "success": True
            }
            
        except Exception as db_error:
            db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Datenbankfehler: {str(db_error)}",
                    "success": False
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={
                "error": f"Unerwarteter Fehler: {str(e)}",
                "success": False
            }
        )

def create_download_link(df, filename, label="Download-Datei"):
    """
    Erstellt einen Download-Link für eine DataFrame-Datei (CSV) als HTML-Button.
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">{label}</a>'
    return href