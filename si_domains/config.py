"""Configuration for the .si domain research pipeline."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
EVIDENCE_PATH = OUTPUT_DIR / "rdap_evidence.csv"

RDAP_BASE_URL = "https://rdap.register.si/domain/"
RDAP_TIMEOUT = (5.0, 15.0)
WHOIS_HOST = "whois.register.si"
WHOIS_PORT = 43
WHOIS_TIMEOUT = 10.0
WHOIS_MAX_BYTES = 64 * 1024

MIN_REQUEST_INTERVAL = 1.0
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_CAP_SECONDS = 120.0
MAX_RETRY_AFTER_SECONDS = 15 * 60
CIRCUIT_BREAKER_THRESHOLD = 5

USER_AGENT = "si-domain-research/1.0 (personal research)"
