# migrate.py
from alembic.config import Config
from alembic import command

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations()
