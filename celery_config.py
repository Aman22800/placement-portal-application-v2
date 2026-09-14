from celery import Celery
import os

def make_celery(app):
    """Creates a Celery instance wired to use Redis, and configured so
    tasks can access Flask's app context (needed to query the database).
    REDIS_URL defaults to localhost for local dev; in Docker Compose it's
    set to redis://redis:6379/0 so it resolves to the redis service."""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    celery = Celery(
        app.import_name,
        broker=redis_url,
        backend=redis_url,
        include=['tasks']   # tells the Celery WORKER process to import tasks.py itself
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Wraps every task so it runs inside Flask's app context --
        without this, tasks couldn't use db.session or query models."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery