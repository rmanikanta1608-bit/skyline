# AuditMemory
Compliance audit agent for Legal Metrology (Packaged Commodities) Rules, 2011, powered by [Hindsight](https://github.com/vectorize-io/hindsight) agent memory.

## How Hindsight is used
- **retain**: every finding and every officer verdict (confirmed / false positive) per vendor.
- **recall**: before each check, past records for the vendor are recalled.
- **Behavior change**: repeat violations escalate severity; rules officers repeatedly mark false positive are downgraded; the summary cites vendor history.

## Run
```
pip install -r requirements.txt
# create a .env file with HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, GROQ_API_KEY
uvicorn main:app --reload
```
Open http://localhost:8000. Without keys it runs on a local memory fallback.

## Demo script (60 seconds)
1. Sample 1 (missing MRP + address) -> generic findings.
2. Run it 2 more times -> severity escalates, "Repeat offender" note appears.
3. Mark "Consumer care" false positive twice, re-check -> downgraded.
