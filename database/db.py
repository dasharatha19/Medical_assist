"""
database/db.py
PostgreSQL database layer for MediBook.
"""
import psycopg2
import psycopg2.extras
import pandas as pd
import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR       = Path(__file__).parent.parent
PATIENTS_CSV   = BASE_DIR / "data" / "patients.csv"
SCHEDULES_XLSX = BASE_DIR / "data" / "doctor_schedules.xlsx"


# ── Connection ────────────────────────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host     = os.getenv("DB_HOST", "localhost"),
        port     = os.getenv("DB_PORT", "5432"),
        dbname   = os.getenv("DB_NAME", "medibook"),
        user     = os.getenv("DB_USER", "postgres"),
        password = os.getenv("DB_PASSWORD", "postgres123")
    )

def create_database_if_not_exists():
    try:
        conn = psycopg2.connect(
            host     = os.getenv("DB_HOST", "localhost"),
            port     = os.getenv("DB_PORT", "5432"),
            dbname   = "postgres",
            user     = os.getenv("DB_USER", "postgres"),
            password = os.getenv("DB_PASSWORD", "postgres123")
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s",
                    (os.getenv("DB_NAME", "medibook"),))
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'medibook')}")
            logger.info("Created database: medibook")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Could not create database: {e}")


# ── Schema ────────────────────────────────────────────────────────────────────
def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id        TEXT PRIMARY KEY,
            first_name        TEXT,
            last_name         TEXT,
            full_name         TEXT,
            dob               TEXT,
            phone             TEXT,
            email             TEXT,
            insurance_carrier TEXT,
            member_id         TEXT,
            group_id          TEXT,
            last_visit        TEXT,
            patient_type      TEXT DEFAULT 'new'
        );

        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id      TEXT PRIMARY KEY,
            name           TEXT,
            specialization TEXT,
            location       TEXT,
            working_hours  TEXT,
            break_time     TEXT
        );

        CREATE TABLE IF NOT EXISTS doctor_slots (
            id          SERIAL PRIMARY KEY,
            doctor_id   TEXT REFERENCES doctors(doctor_id),
            date        TEXT,
            time_slot   TEXT,
            status      TEXT DEFAULT 'available'
        );

        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id      TEXT PRIMARY KEY,
            patient_id          TEXT,
            patient_name        TEXT,
            patient_dob         TEXT,
            patient_email       TEXT,
            patient_phone       TEXT,
            doctor_name         TEXT,
            appointment_date    TEXT,
            appointment_time    TEXT,
            duration_minutes    INTEGER,
            patient_type        TEXT,
            insurance_carrier   TEXT,
            insurance_member_id TEXT,
            insurance_group_id  TEXT,
            insurance_valid     BOOLEAN DEFAULT FALSE,
            booking_confirmed   BOOLEAN DEFAULT FALSE,
            booking_success     BOOLEAN DEFAULT FALSE,
            reminders_setup     BOOLEAN DEFAULT FALSE,
            form_sent           BOOLEAN DEFAULT FALSE,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status              TEXT DEFAULT 'pending'
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("PostgreSQL tables created/verified")


# ── Seed patients ─────────────────────────────────────────────────────────────
def seed_patients():
    if not PATIENTS_CSV.exists():
        logger.warning(f"patients.csv not found at {PATIENTS_CSV}")
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM patients")
    if cur.fetchone()[0] >= 10:
        cur.close()
        conn.close()
        return
    df = pd.read_csv(PATIENTS_CSV)
    df['phone'] = df['phone'].apply(
        lambda x: str(int(float(x))) if pd.notna(x) else "")
    df['full_name'] = df['first_name'].str.strip() + " " + df['last_name'].str.strip()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO patients
            (patient_id,first_name,last_name,full_name,dob,phone,email,
             insurance_carrier,member_id,group_id,last_visit,patient_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (patient_id) DO NOTHING
        """, (
            row.get('patient_id',''),
            row.get('first_name',''),
            row.get('last_name',''),
            row.get('full_name',''),
            str(row.get('dob','')),
            str(row.get('phone','')),
            row.get('email',''),
            row.get('insurance_carrier',''),
            row.get('member_id',''),
            row.get('group_id',''),
            str(row.get('last_visit','')),
            row.get('patient_type','returning')
        ))
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Patients seeded")


# ── Seed doctors ──────────────────────────────────────────────────────────────
def seed_doctors():
    if not SCHEDULES_XLSX.exists():
        logger.warning(f"doctor_schedules.xlsx not found at {SCHEDULES_XLSX}")
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM doctors")
    if cur.fetchone()[0] >= 3:
        cur.close()
        conn.close()
        return
    xl = pd.read_excel(SCHEDULES_XLSX, sheet_name=None, header=None)
    for sheet_name, df in xl.items():
        def get_val(i):
            try: return str(df.iloc[i, 1]).strip()
            except: return ""
        name          = get_val(0)
        specialization= get_val(1)
        location      = get_val(2)
        working_hours = get_val(3)
        break_time    = get_val(4)
        doctor_id     = f"DR_{name.replace(' ','_').replace('.','')}"
        cur.execute("""
            INSERT INTO doctors
            (doctor_id,name,specialization,location,working_hours,break_time)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (doctor_id) DO NOTHING
        """, (doctor_id,name,specialization,location,working_hours,break_time))
        header_row = df.iloc[6]
        dates = []
        for col_idx in range(1, len(header_row)):
            cell = str(header_row.iloc[col_idx])
            if cell and cell != 'nan':
                dates.append((col_idx, cell.split('\n')[0].strip()))
        for row_idx in range(7, len(df)):
            time_slot = str(df.iloc[row_idx, 0]).strip()
            if not time_slot or time_slot == 'nan':
                continue
            for col_idx, date in dates:
                try:
                    raw = str(df.iloc[row_idx, col_idx]).strip().lower()
                    status = 'available' if raw == 'available' else \
                             'break' if raw == 'break' else 'unavailable'
                except:
                    status = 'unavailable'
                cur.execute("""
                    INSERT INTO doctor_slots (doctor_id,date,time_slot,status)
                    VALUES (%s,%s,%s,%s)
                """, (doctor_id, date, time_slot, status))
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Doctors seeded")


# ── Initialize ────────────────────────────────────────────────────────────────
def initialize_database():
    create_database_if_not_exists()
    create_tables()
    seed_patients()
    seed_doctors()
    logger.info("PostgreSQL database ready")


# ── Patient Queries ───────────────────────────────────────────────────────────
def lookup_patient(name: str, dob: str) -> dict:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM patients
        WHERE LOWER(full_name)=%s AND dob=%s
    """, (name.strip().lower(), dob))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def register_new_patient(data: dict) -> str:
    conn = get_connection()
    cur = conn.cursor()
    pid = f"P{uuid.uuid4().hex[:6].upper()}"
    cur.execute("""
        INSERT INTO patients
        (patient_id,full_name,dob,phone,email,patient_type)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (pid, data.get('name',''), data.get('dob',''),
          data.get('phone',''), data.get('email',''), 'new'))
    conn.commit()
    cur.close()
    conn.close()
    return pid


# ── Doctor Queries ────────────────────────────────────────────────────────────
def get_all_doctors() -> list:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM doctors")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_available_slots(doctor_name: str, date: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    doctor_id = f"DR_{doctor_name.replace(' ','_').replace('.','')}"
    cur.execute("""
        SELECT time_slot FROM doctor_slots
        WHERE doctor_id=%s AND date=%s AND status='available'
        ORDER BY time_slot
    """, (doctor_id, date))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def book_slot(doctor_name: str, date: str, time_slot: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    doctor_id = f"DR_{doctor_name.replace(' ','_').replace('.','')}"
    cur.execute("""
        UPDATE doctor_slots SET status='booked'
        WHERE doctor_id=%s AND date=%s AND time_slot=%s
    """, (doctor_id, date, time_slot))
    conn.commit()
    cur.close()
    conn.close()
    return True


# ── Appointment Queries ───────────────────────────────────────────────────────
def save_appointment(state: dict) -> str:
    conn = get_connection()
    cur = conn.cursor()
    appt_id = state.get('appointment_id') or f"APT{uuid.uuid4().hex[:6].upper()}"
    cur.execute("""
        INSERT INTO appointments (
            appointment_id,patient_id,patient_name,patient_dob,
            patient_email,patient_phone,doctor_name,appointment_date,
            appointment_time,duration_minutes,patient_type,
            insurance_carrier,insurance_member_id,insurance_group_id,
            insurance_valid,booking_confirmed,booking_success,
            reminders_setup,form_sent,status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (appointment_id) DO UPDATE SET
            booking_confirmed = EXCLUDED.booking_confirmed,
            booking_success   = EXCLUDED.booking_success,
            status            = EXCLUDED.status
    """, (
        appt_id,
        state.get('patient_id',''),
        state.get('patient_name',''),
        state.get('patient_dob',''),
        state.get('patient_email',''),
        state.get('patient_phone',''),
        state.get('preferred_doctor',''),
        state.get('appointment_date',''),
        state.get('selected_time',''),
        state.get('appointment_duration', 60),
        state.get('patient_type','new'),
        state.get('insurance_carrier',''),
        state.get('insurance_member_id',''),
        state.get('insurance_group_id',''),
        bool(state.get('insurance_valid')),
        bool(state.get('booking_confirmed')),
        bool(state.get('booking_success')),
        bool(state.get('reminders_setup')),
        bool(state.get('form_sent')),
        state.get('status', 'confirmed' if state.get('booking_confirmed') else 'pending')
    ))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Appointment saved to PostgreSQL: {appt_id}")
    return appt_id


def get_all_appointments() -> list:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM appointments ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def export_appointments_excel(output_path: str) -> str:
    appointments = get_all_appointments()
    if not appointments:
        return None
    pd.DataFrame(appointments).to_excel(output_path, index=False)
    return output_path