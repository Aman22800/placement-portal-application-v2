from datetime import datetime, timedelta
from app import celery, db, mail
from flask_mail import Message
from models import Application

from datetime import datetime, timedelta
from app import celery, db, mail
from flask_mail import Message
from models import Application


@celery.task
def send_email_task(subject, recipient, body):
    """Generic reusable task: send ONE email asynchronously. Routes call this
    with .delay() so the HTTP response returns immediately without waiting
    for the actual SMTP send to complete."""
    try:
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail.send(msg)
        return f"Email sent to {recipient}"
    except Exception as e:
        print(f"[MAIL ERROR] Could not send to {recipient}: {e}")
        return f"Failed to send to {recipient}: {e}"


@celery.task
def send_interview_reminders():
    """Finds every application with an interview scheduled in the next 24 hours
    and sends a real reminder email via Flask-Mail."""

    now = datetime.utcnow()
    cutoff = now + timedelta(hours=24)

    upcoming = Application.query.filter(
        Application.status == 'Interview Scheduled',
        Application.interview_datetime >= now,
        Application.interview_datetime <= cutoff
    ).all()

    count = 0
    for app_row in upcoming:
        student_email = app_row.student.user.email
        job_title = app_row.drive.job_title
        interview_time = app_row.interview_datetime
        link = app_row.interview_link or 'No link provided'

        msg = Message(
            subject=f"Interview Reminder: {job_title}",
            recipients=[student_email],
            body=(
                f"Hi {app_row.student.name},\n\n"
                f"This is a reminder that your interview for '{job_title}' "
                f"is scheduled at {interview_time}.\n"
                f"Meeting link: {link}\n\n"
                f"Good luck!\nPlacement Portal Team"
            )
        )

        try:
            mail.send(msg)
            count += 1
        except Exception as e:
            # Don't let one failed email crash the whole batch -- log and continue
            print(f"[MAIL ERROR] Could not send to {student_email}: {e}")

    return f"Sent {count} interview reminder(s)"