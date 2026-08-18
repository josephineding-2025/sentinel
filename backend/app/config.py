import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data" / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# `or` (not the two-arg os.getenv form) so an empty "DATABASE_URL=" line in
# .env still falls through to the computed default instead of becoming "".
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATA_DIR / 'wellbeing.db'}"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # optional: on-demand profile explanation only
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # free tier, powers the live Student Chat demo

# Risk state thresholds — tuned against scripts/evaluate.py output on the
# synthetic dataset with the REAL HF models + blended conv_distress (mean +
# worst-message): peak risk_score for stable/volatile_but_ok students tops
# out around 5.9, while deteriorating students bottom out around 10.5. These
# sit in that gap. Re-run evaluate.py after regenerating data or changing
# evidence_fusion.py weights, and re-tune if the gap shifts.
RISK_THRESHOLDS = {
    "potential_concern": 7.0,   # risk_score >= this -> 🟠
    "high_priority": 12.0,      # risk_score >= this -> 🔴
}
MIN_CONVERSATION_DATA_POINTS = 3  # below this, state may become "insufficient evidence" (🔵)
