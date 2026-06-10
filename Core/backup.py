import os
import shutil
from datetime import datetime


BACKUP_DIR = "backup"


def create_backup():

    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists("output/all.txt"):
        return

    name = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    shutil.copy(
        "output/all.txt",
        f"{BACKUP_DIR}/{name}.txt"
    )
