
from flask import Flask, request, render_template, jsonify
import requests
import logging
from flask_cors import CORS  

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_task', methods=['POST'])
def submit_task():
    vm_url = 'http://18.222.157.2:5000/receive-task' 
    """Handles task-prompt submission"""
    try:
        data = request.form  # Log received form data
        logging.debug(f"Received form data: {data}")

        task_prompt = data.get('task_prompt')  # Fetch the task prompt
        logging.debug("The task is " + task_prompt)
        if not task_prompt:
            return jsonify({"error": "No task prompt provided"}), 400

        # Send the task to the VM
        try:
            response = requests.post(vm_url, json={"task_prompt": task_prompt})
            if response.status_code == 200:
                logging.debug("Task sent to VM successfully")
                return render_template('index.html')
            else:
                logging.debug("Failed to send task to VM")
                return render_template('index.html')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending task to VM: {str(e)}")
            return render_template('index.html')
    except Exception as e:
        logger.error(f"Error handling task-prompt submission: {str(e)}", exc_info=True)
        return render_template('index.html')
    return render_template('./templates/index.html')
@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    file = request.files['file']
    
    files = {'file': (file.filename, file.stream, file.mimetype)}
    vm_url = 'http://18.222.157.2:5000/receive-file'  # Adjust VM URL as needed

    response = requests.post(vm_url, files=files)
    return response.json()
def send_to_vm(task_prompt):
    vm_url = 'http://18.222.157.2:5000/receive-task'  # Use the public IP of your VM
    payload = {'task-prompt': task_prompt}
    response = requests.post(vm_url, data=payload)
    return response.json()

@app.route('/task_completed', methods=['POST'])
def task_completed():
    """Receives task completion notification from VM"""
    print("working2S")
    data = request.json  # Get data from the VM
    if not data or 'task_prompt' not in data:
        return jsonify({"error": "Invalid notification data"}), 400  # Return error if data is missing

    task_prompt = data['task_prompt']  # Extract the task name
    logger.info(f"Task '{task_prompt}' completed on VM.")  # Log the completion
    print(f"✅ Task '{task_prompt}' completed on VM.")  # Print confirmation

    return jsonify({"message": "Task completion received"}), 200  # Send response back to VM

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
