from extend.db import LOCSESSION


def getDbSession():
    db = LOCSESSION()
    try:
        yield db
    finally:
        db.close()