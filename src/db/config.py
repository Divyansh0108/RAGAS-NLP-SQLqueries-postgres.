import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root regardless of where the script is run from
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "divyanshpandey"
    password: str = os.getenv("DB_PASSWORD", "")
    database: str = "dvdrental"

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


db_config = DatabaseConfig()
