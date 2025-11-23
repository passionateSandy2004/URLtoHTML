# fixed_decodo_poll.py
import requests
import time

USERNAME = "U0000326616"
PASSWORD = "PW_1cbb25eb0fb4a38c0ba6a049c18da34be"

BATCH_URL = "https://scraper-api.decodo.com/v2/task/batch"
RESULT_URL = "https://scraper-api.decodo.com/v2/task/{task_id}/results"

# Example URLs
urls = [
    "https://www.sih.gov.in/",
    "https://www.python.org",
    "https://github.com",
]

payload = {
    # use "url" or "queries" depending on preferred format; here we use "url"
    "url": urls,
    "target": "universal",
    # Force JS rendering if desired:
    # "headless": True,
    "render_js": True,
    "device_type": "desktop"
}

# Submit batch
resp = requests.post(BATCH_URL, auth=(USERNAME, PASSWORD), json=payload)
resp.raise_for_status()
batch_resp = resp.json()
print("Batch submission response (top-level):")
print(batch_resp)

# --- Extract per-URL task ids (handle both "queries" and "tasks") ---
task_entries = []
if isinstance(batch_resp, dict):
    if "queries" in batch_resp and isinstance(batch_resp["queries"], list):
        task_entries = batch_resp["queries"]
    elif "tasks" in batch_resp and isinstance(batch_resp["tasks"], list):
        task_entries = batch_resp["tasks"]
    elif isinstance(batch_resp.get("id"), (str, int)) and "url" in batch_resp:
        # single-task response fallback
        task_entries = [batch_resp]
elif isinstance(batch_resp, list):
    task_entries = batch_resp

# Build mapping: task_id -> url (if available)
task_map = {}   # task_id (str) -> url (str or None)
for entry in task_entries:
    if isinstance(entry, dict):
        tid = entry.get("id") or entry.get("task_id") or entry.get("query_id")
        url_field = entry.get("url") or entry.get("query") or None
        if tid:
            task_map[str(tid)] = url_field
    elif isinstance(entry, str):
        # sometimes API returns list of ids as strings
        task_map[entry] = None

if not task_map:
    # if nothing found, fall back to batch id (helpful for debugging)
    print("Warning: no individual task ids found in the batch response.")
    if isinstance(batch_resp, dict) and "id" in batch_resp:
        print("Batch id:", batch_resp["id"])
    raise SystemExit("No per-task ids to poll. Inspect batch response above.")

print("\nTask mapping (task_id -> url):")
for k, v in task_map.items():
    print(f"{k} -> {v}")

# --- Poll results for each task id ---
def fetch_results(task_id):
    url = RESULT_URL.format(task_id=task_id)
    return requests.get(url, auth=(USERNAME, PASSWORD))

results = {}
max_wait = 180         # seconds total wait per task (tune as needed)
initial_interval = 2.0

for tid, original_url in task_map.items():
    print(f"\nPolling task {tid} (url: {original_url}) ...")
    waited = 0.0
    interval = initial_interval
    while waited < max_wait:
        try:
            r = fetch_results(tid)
            # If 404, treat as "not ready yet" and retry
            if r.status_code == 404:
                print(f"  {tid}: results not yet available (404). waiting {interval}s...")
                time.sleep(interval)
                waited += interval
                interval = min(interval * 1.5, 10)
                continue
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError as e:
            # For other HTTP errors, print and retry a few times
            print(f"  HTTP error for {tid}: {e} — waiting {interval}s and retrying...")
            time.sleep(interval)
            waited += interval
            interval = min(interval * 1.5, 10)
            continue
        except ValueError:
            # Non-JSON response; print raw text and break
            print(f"  Non-JSON response for {tid}:")
            print(r.text[:1000])
            results[tid] = r.text
            break

        # Check common "done" indicator (API responses vary)
        status = None
        if isinstance(data, dict):
            status = data.get("status") or data.get("state")
        # If the API returns actual result data fields, treat it as ready
        if status == "done" or "result" in data or "data" in data or data:
            print(f"  Task {tid} ready. Storing result.")
            results[tid] = data
            break

        # Not ready yet
        print(f"  Task {tid} status: {status} — waiting {interval}s...")
        time.sleep(interval)
        waited += interval
        interval = min(interval * 1.5, 10)
    else:
        print(f"  Timed out waiting for {tid} after {max_wait} seconds.")
        results[tid] = None

# --- Print summary ---
print("\n=== Results summary ===")
for tid, res in results.items():
    print(f"\n--- {tid} (url: {task_map.get(tid)}) ---")
    if res is None:
        print("No result (timed out or failed).")
        continue

    if isinstance(res, dict) and "results" in res:
        r0 = res["results"][0]  # first page of the result

        html = r0.get("content")
        status = r0.get("status")
        final_url = r0.get("url")

        print("Status:", status)
        print("Final URL:", final_url)

        if html:
            print("\n--- HTML PREVIEW (first 500 chars) ---")
            print(html[:500])
        else:
            print("No HTML content returned.")

    else:
        print("Unexpected result format:")
        print(str(res)[:500])
