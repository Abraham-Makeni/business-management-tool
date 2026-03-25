from datetime import datetime
from pathlib import Path

import pandas as pd

from app.core.config import DATA_DIR


class ExportService:
    def __init__(self) -> None:
        self.export_dir = DATA_DIR / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_to_excel(self, rows: list, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.export_dir / f"{prefix}_{timestamp}.xlsx"

        df = pd.DataFrame(rows)
        if df.empty:
            df = pd.DataFrame([{"message": "No data available"}])

        df.to_excel(file_path, index=False)
        return file_path
