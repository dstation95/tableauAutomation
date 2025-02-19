import time
import json
import os
import requests

# Configuration
API_KEY = "e06f4eeb-4aea-4116-9a46-c9079697e609"
BASE_URL = "https://v3.polymersearch.com/api/v1"
DATASET_ENDPOINT = f"{BASE_URL}/dataset"
TASK_ENDPOINT = f"{BASE_URL}/task"

# Local CSV file to upload
input_file = "FlightsOct25.csv"
dataset_name = "API Dataset Demo3"

# Check if file exists
if not os.path.exists(input_file):
    raise FileNotFoundError(f"File not found: {input_file}")

# Step 1: Upload the CSV file using multipart/form-data
print("Uploading CSV dataset...")

files = {
    "file": open(input_file, "rb")
}
# When uploading via form-data, include additional fields as strings.
data = {
    "name": dataset_name,
    "auto_generate_board": "true"
}

headers = {
    "x-api-key": API_KEY
    # Let requests set Content-Type automatically for multipart/form-data.
}

try:
    upload_response = requests.post(DATASET_ENDPOINT, headers=headers, data=data, files=files)
    print("Upload response status code:", upload_response.status_code)
    print("Upload response text:", upload_response.text)
    upload_response.raise_for_status()  # Raises an HTTPError for bad responses
except requests.exceptions.HTTPError as http_err:
    print("HTTP error occurred during CSV upload:", http_err)
    print("Response content:", upload_response.text)
    raise

upload_result = upload_response.json()
print("Upload response JSON:")
print(json.dumps(upload_result, indent=2))

# Step 2: Poll for the processing task completion.
task_id = upload_result.get("task_id")
if not task_id:
    print("No task_id returned; using the upload response as final result.")
    final_result = upload_result
else:
    print(f"Task ID received: {task_id}")
    task_url = f"{TASK_ENDPOINT}/{task_id}"
    dataset_ready = False
    max_retries = 30
    retry_count = 0

    while not dataset_ready and retry_count < max_retries:
        task_resp = requests.get(task_url, headers={"x-api-key": API_KEY})
        task_resp.raise_for_status()
        task_status = task_resp.json()
        status = task_status.get("status", "")
        print(f"Task status: {status}")
        if status == "done":
            dataset_ready = True
            final_result = task_status
            break
        elif status == "inprogress":
            time.sleep(5)
        else:
            raise Exception(f"Error processing dataset: {task_status.get('error')}")
        retry_count += 1

    if not dataset_ready:
        raise TimeoutError("Dataset processing did not complete in expected time.")

# Step 3: Display the final result from processing.
board_id = final_result.get("board_id")
file_id = final_result.get("file_id")
if board_id:
    print(f"\nDataset processing completed successfully.\nFile ID: {file_id}\nBoard ID: {board_id}")
    embed_url = f"https://v3.polymersearch.com/b/{board_id}?ptoken=YOUR_EMBED_TOKEN"
    print("Example embed URL (replace YOUR_EMBED_TOKEN with a valid token):")
    print(embed_url)
else:
    print("No board information returned. Check your API response for details.")

# Step 4: Save the initial processing result to a JSON file.
output_file = "polymer_dataset_analytics.json"
with open(output_file, "w") as f:
    json.dump(final_result, f, indent=2)

print(f"\nInitial analytics information saved to {output_file}")

# Step 5: (Additional) Fetch the full board details to access the insights configuration.
if board_id:
    board_details_url = f"{BASE_URL}/board/{board_id}"
    try:
        board_details_resp = requests.get(board_details_url, headers={"x-api-key": API_KEY})
        board_details_resp.raise_for_status()
        board_details = board_details_resp.json()
        print("\nFetched board details:")
        print(json.dumps(board_details, indent=2))
        # Save the detailed board info for further analysis.
        with open("polymer_board_details.json", "w") as f:
            json.dump(board_details, f, indent=2)
        print("Board details saved to polymer_board_details.json")
    except requests.exceptions.HTTPError as e:
        print("Error fetching board details:", e)
else:
    print("No board_id available; cannot fetch board details.")
