from datetime import datetime
from pathlib import Path
import shutil

from app.core.config import DATA_DIR


class BackupService:
    def __init__(self) -> None:
        self.db_path = DATA_DIR / "app.db"
        self.backup_dir = DATA_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Path:
        if not self.db_path.exists():
            raise FileNotFoundError("Database file not found.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"app_backup_{timestamp}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path
