import os
import time
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop
import openai

# Set OpenAI API credentials and model name
openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini-2024-07-18"

def executeDouble(base_filename):
    """
    Executes a two-click UI automation routine.
    
    Expects a single base file name. Four JSON files are expected in the 
    recordings/double folder:
      - <base_filename>_1_input.json
      - <base_filename>_1_output.json
      - <base_filename>_2_input.json
      - <base_filename>_2_output.json
      
    No PNG files are saved.
    """
    
    # -------------------------
    # Helper Functions
    # -------------------------
    def rectangle_to_str(rect):
        return f"{int(rect.left)}-{int(rect.top)}-{int(rect.right)}-{int(rect.bottom)}"

    def runtime_id_to_str(runtime_id):
        if runtime_id:
            return "_".join(str(item) for item in runtime_id)
        return "NoRuntimeID"

    def generate_composite_id(elem_info):
        control_type = elem_info.control_type or "UnknownControl"
        class_name = elem_info.class_name or "UnknownClass"
        auto_id = elem_info.automation_id if elem_info.automation_id else "NoAutomationId"
        name = elem_info.name if elem_info.name else "NoName"
        rect_str = rectangle_to_str(elem_info.rectangle)
        rt_str = runtime_id_to_str(elem_info.runtime_id)
        return f"{control_type}|{class_name}|{auto_id}|{name}|{rect_str}|{rt_str}"

    def dump_ui_tree(elem_info):
        tree = {"composite": generate_composite_id(elem_info), "children": []}
        try:
            children = elem_info.children()
        except Exception:
            children = []
        for index, child in enumerate(children, start=1):
            child_composite = f"[{index}] " + generate_composite_id(child)
            subtree = dump_ui_tree(child)
            subtree["composite"] = child_composite
            tree["children"].append(subtree)
        return tree

    def search_for_runtime_id(wrapper, target_rt):
        try:
            current_rt = runtime_id_to_str(wrapper.element_info.runtime_id)
        except Exception:
            current_rt = ""
        if current_rt == target_rt:
            return wrapper
        for child in wrapper.children():
            found = search_for_runtime_id(child, target_rt)
            if found is not None:
                return found
        return None

    def clean_response(text):
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    def capture_snapshot():
        ui_tree = dump_ui_tree(main_window.element_info)
        return json.dumps(ui_tree, indent=2)

    def openai_infer(prompt_text):
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a UI automation assistant. Return ONLY the runtime_id (as plain text) for the UI element to click."},
                {"role": "user", "content": prompt_text}
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()

    def load_examples(filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading JSON from {filename}: {e}")
        return []

    # -------------------------
    # Build File Paths from Provided Base Name
    # -------------------------
    base_path = os.path.join("recordings", "double")
    input_file_1 = os.path.join(base_path, f"{base_filename}_1_input.json")
    output_file_1 = os.path.join(base_path, f"{base_filename}_1_output.json")
    input_file_2 = os.path.join(base_path, f"{base_filename}_2_input.json")
    output_file_2 = os.path.join(base_path, f"{base_filename}_2_output.json")

    training_examples_first = load_examples(input_file_1)
    training_examples_first_out = load_examples(output_file_1)
    training_examples_second = load_examples(input_file_2)
    training_examples_second_out = load_examples(output_file_2)

    # -------------------------
    # Connect to the Target Application (Tableau)
    # -------------------------
    windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
    if not windows:
        print("No Tableau window found.")
        sys.exit(1)

    def window_area(win):
        rect = win.rectangle()
        return (rect.right - rect.left) * (rect.bottom - rect.top)

    target_window = max(windows, key=window_area)
    app = Application(backend="uia").connect(handle=target_window.handle)
    pid = target_window.element_info.process_id
    print(f"Connected to window: Handle {target_window.handle}, Process ID: {pid}, Title: {target_window.window_text()}")
    main_window = app.window(handle=target_window.handle)

    # -------------------------
    # First Click: Capture UI Snapshot and Build Inference Prompt
    # -------------------------
    new_ui_tree = dump_ui_tree(main_window.element_info)
    new_snapshot_str = json.dumps(new_ui_tree, indent=2)
    
    # (Optional debug snapshot; not saved to disk)
    print("Capturing UI snapshot for first click...")
    snapshot1_str = capture_snapshot()

    prompt1 = f"""
Below are training examples for the first click:
with the input snapshot being
{training_examples_first}
and the corresponding output snapshot to click based on the input should be
{training_examples_first_out}
Now, given the current UI snapshot and what was clicked on in the original training example, return ONLY the runtime_id (plain text) of the UI element to click for the FIRST click.
Ensure the runtime_id is in the format similar to '42_4066502_4_-2147478117'.
Current UI snapshot:
{new_snapshot_str}
"""
    print("Sending first click prompt to ChatGPT...")
    raw_response1 = openai_infer(prompt1)
    predicted_runtime_id1 = clean_response(raw_response1)
    print("Predicted runtime ID for first click:", predicted_runtime_id1)

    first_elem = search_for_runtime_id(main_window, predicted_runtime_id1)
    if first_elem is not None:
        rect1 = first_elem.rectangle()
        click_x1 = (rect1.left + rect1.right) // 2
        click_y1 = (rect1.top + rect1.bottom) // 2
        print(f"Simulating first click at ({click_x1}, {click_y1})")
        first_elem.click_input()
    else:
        print("Could not locate element for first click with runtime ID:", predicted_runtime_id1)
        sys.exit(1)

    print("First click complete.")

    # -------------------------
    # Second Click: Wait, Capture New Snapshot, and Build Inference Prompt
    # -------------------------
    time.sleep(2)
    print("Capturing UI snapshot for second click...")
    snapshot2_str = capture_snapshot()

    prompt2 = f"""
Below are training examples for the second click:
with the input snapshot being
{training_examples_second}
and the corresponding output snapshot to click based on the input should be
{training_examples_second_out}
Now, given the current UI snapshot and what was clicked on in the original training example, try to click a very similar component (with similar component names and details) and return ONLY the runtime_id (plain text) of the UI element to click for the SECOND click.
Ensure the runtime_id is in the format similar to '42_4066502_4_-2147478117'.
Current UI snapshot:
{snapshot2_str}
"""
    print("Sending second click prompt to ChatGPT...")
    raw_response2 = openai_infer(prompt2)
    predicted_runtime_id2 = clean_response(raw_response2)
    print("Predicted runtime ID for second click:", predicted_runtime_id2)

    second_elem = search_for_runtime_id(main_window, predicted_runtime_id2)
    if second_elem is not None:
        rect2 = second_elem.rectangle()
        click_x2 = (rect2.left + rect2.right) // 2
        click_y2 = (rect2.top + rect2.bottom) // 2
        print(f"Simulating second click at ({click_x2}, {click_y2})")
        second_elem.click_input()
    else:
        print("Could not locate element for second click with runtime ID:", predicted_runtime_id2)
        sys.exit(1)

    print("Double click simulation complete.")
