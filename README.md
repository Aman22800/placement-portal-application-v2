# Placement Portal Application (MAD-2 Project)

A role-based placement management web app (Admin, Company, Student) built with
Flask, Vue 3 (Vite), SQLite, and Celery + Redis for background jobs.

## Tech Stack
- **Backend:** Python 3.9, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS
- **Database:** SQLite (created programmatically)
- **Background jobs:** Celery, Redis
- **Frontend:** Vue 3, Vite, Vue Router, Axios, Bootstrap 5

## Setup & Run Instructions

### 1. Install backend dependencies
pip install -r requirements.txt

### 2. Set up environment variables
cp .env.example .env
Then fill in `JWT_SECRET_KEY` (generate one with `python3 -c "import secrets; print(secrets.token_hex(32))"`).
Mail settings are optional -- leave blank to keep interview reminders console-only.

### 3. Create the database (creates tables + a seeded admin)
python3 create_db.py

Seeded admin login: admin@placementportal.com / admin123

### 4. Build the frontend
cd frontend
npm install
npm run build
cd ..

(Skip this step if frontend/dist/ is already included in this submission.)

### 5. Start Redis
redis-server

(Or `brew services start redis` on macOS.)

### 6. Start the Flask app (serves both backend API and the built frontend)
python3 app.py

Visit http://127.0.0.1:5000/ -- this serves the full application.

### 7. Start the Celery worker (needed for the interview-reminder background job)
In a separate terminal:
celery -A app:celery worker --loglevel=info --pool=solo

(`--pool=solo` is required on macOS.)

## Roles
- **Admin** (seeded): approve/reject/blacklist companies, approve/close drives, trigger reminders
- **Company** (self-register, needs admin approval): post drives, view applicants, shortlist, schedule interviews, release offers
- **Student** (self-register): view eligible drives, apply, accept offers

## Background Job
POST /api/admin/trigger-reminders queues a Celery task that finds applications with an interview scheduled in the next 24 hours and sends a reminder (simulated via console print in this submission -- would be a real email in production).

## Running with Docker (alternative to the manual steps above)

### 1. Set up .env
Same as step 2 above -- cp .env.example .env and fill it in. docker-compose reads
this file automatically and overrides REDIS_URL to point at the redis container.

### 2. Build the images
docker compose build

### 3. Create the database (one-time, before first run)
docker compose run --rm web python3 create_db.py

### 4. Start everything (redis, flask app, celery worker)
docker compose up

Visit http://127.0.0.1:5000/

### To stop
docker compose down
(Add -v if you also want to remove the redis volume.)

Note: the SQLite database and uploaded resumes live in ./instance and
./static/resumes on your host machine (mounted into the containers), so
data survives `docker compose down` and image rebuilds.

