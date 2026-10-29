import sys
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "client"))

from app.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
