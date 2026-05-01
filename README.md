# Chat Trading Intent Extractor

Reads Bloomberg etc chat-room messages and extracts client order intent into a CSV/database-ready structure.

## Input

CSV columns:

```text
date,time,roomname,sender,participants,message
```

`participants` can be a JSON list, semicolon-separated list, comma-separated list, or plain text.

## Final Output

For the POC, the final output is a CSV file. The `--output` path should point to that CSV.

CSV columns:

```text
order_id,date,chat_timestamp,roomname,client_sender_id,product,side,quantity,order_type,price,event,order_message,order_time,close_reason,trigger_type,trigger_explanation,confidence_score
```

## Run Log

Each run also writes a CSV log next to the output CSV:

```text
out/orders.log.csv
```

The log identifies:

- each input CSV row analyzed in each context window
- token usage for each LLM prompt, when returned by the gateway
- every output order record created
- parse errors for a window, if any

Use `--log-file` to choose a different path.

## Traded Products

Maintain product normalization in:

```text
data/traded_products.csv
```

Format:

```text
Symbol
LULU
```

The LLM can return a partial product mention such as `lul`; the POC maps it to the canonical symbol `LULU` when the prefix uniquely matches one traded product.

## Client IDs

Maintain known client senders in:

```text
data/client_ids.csv
```

Format:

```text
client_sender_id
client_101
```

These IDs are passed into the LLM prompt so it can distinguish client instructions from trader responses. You can still add temporary IDs with `--client-ids`.

## Setup

```powershell
python -m pip install -r requirements.txt
```

Set your gateway credentials:

```text
.env
```

Use `.env.example` as the template:

```text
LLM_API_KEY=replace_with_api_key
LLM_BASE_URL=https://llmgateway.example.com
LLM_MODEL=Sonnet 4.6
```

The CLI loads `.env` automatically. If the same variable is already set in your shell, the shell value is used.

## Run The POC

Simple run using `.env`:

```powershell
python run.py
```

Configure these paths in `.env`:

```text
INPUT_CSV=data/sample_chat.csv
OUTPUT_CSV=out/orders.csv
LOG_CSV=out/orders.log.csv
CLIENT_IDS_CSV=data/client_ids.csv
TRADED_PRODUCTS_CSV=data/traded_products.csv
```

Advanced manual run:

```powershell
python -m src.cli --input data/sample_chat.csv --output out/orders.csv
```

For a first run on real data, use a small cap:

```powershell
python -m src.cli --input chats.csv --output out/orders.csv --max-windows 5
```

Useful options:

```powershell
python -m src.cli --input chats.csv --output out/orders.csv --room "EQUITY_ROOM_1"
python -m src.cli --input chats.csv --output out/orders.csv --client-ids "client_101,client_204"
python -m src.cli --input chats.csv --output out/orders.csv --clients data/client_ids.csv
python -m src.cli --input chats.csv --output out/orders.csv --products data/traded_products.csv
python -m src.cli --input chats.csv --output out/orders.csv --window-size 12 --overlap 4
python -m src.cli --input chats.csv --output out/orders.csv --log-file out/run_log.csv
python -m src.cli --input chats.csv --output out/orders.csv --dry-run
```

`--dry-run` skips the LLM call and prints the message windows that would be sent.
`--debug-dir` is optional and only stores prompt/response files for troubleshooting; it is not the final output. The final output remains the CSV passed to `--output`.

## Deployment Steps

For a dev or POC deployment:

1. Clone or copy this project to the target environment.

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Create `.env` from `.env.example` and set the gateway values:

```text
LLM_API_KEY=...
LLM_BASE_URL=https://llmgateway...
LLM_MODEL=Sonnet 4.6
```

5. Update reference CSVs:

```text
data/traded_products.csv
data/client_ids.csv
```

6. Run a smoke test without calling the LLM:

```powershell
# set DRY_RUN=true and MAX_WINDOWS=1 in .env
python run.py
```

7. Run a small real LLM test:

```powershell
# set DRY_RUN=false, MAX_WINDOWS=1, and DEBUG_DIR=out/debug in .env
python run.py
```

8. Run on real chat data:

```powershell
# set INPUT_CSV, OUTPUT_CSV, and LOG_CSV in .env
python run.py
```

9. Review outputs:

```text
out/orders.csv
out/orders.log.csv
out/debug/
```

For scheduled runs, use the same command from Task Scheduler, cron, or your orchestration tool, with a date-stamped output path such as `out/orders_2026-05-01.csv`.

## Design

The pipeline groups messages by room, sorts them by timestamp, builds overlapping context windows, and asks the LLM to return strict JSON order events. This handles multi-message intent, jargon, mixed-language phrasing, updates, confirmations, and time-dependent sequences better than single-message classification.

The LLM is instructed to extract only client intent and to include market/news triggers only when the chat context supports them.

If sender IDs do not make client/trader roles obvious, pass `--client-ids` with known client sender IDs. Otherwise the model will infer client intent from the chat context.
