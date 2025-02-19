import os
import time
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui
import openai

# ============================================================
# Step 0: Set OpenAI API credentials for GPT-4o mini
# ============================================================
openai.api_key = "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"
MODEL_NAME = "gpt-4o-mini-2024-07-18"

# ============================================================
# Helper Functions for UI Snapshot and Runtime ID Extraction
# ============================================================
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
    tree = {}
    tree["composite"] = generate_composite_id(elem_info)
    tree["children"] = []
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

def load_json_examples(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading JSON from", filename, ":", e)
            return []
    else:
        return []

def openai_infer(prompt_text):
    response = openai.chat.completions.create(
         model=MODEL_NAME,
         messages=[
             {"role": "system", "content": "You are a UI automation assistant. Based on the given UI snapshot and instruction, return ONLY the runtime_id (as plain text) of the UI element to click."},
             {"role": "user", "content": prompt_text}
         ],
         stream=False
    )
    return response.choices[0].message.content

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

# ============================================================
# New Function: getElementCenter(task_name, guide="")
# ============================================================
def getElementCenter(task_name, guide=""):
    """
    Captures a UI snapshot, uses ChatGPT to infer the runtime_id of the UI element 
    (based on JSON examples and optional guide), and returns the center coordinates (x, y)
    of that element.
    
    Parameters:
      task_name (str): The task name used to locate JSON example files in the recordings/clicks folder.
      guide (str, optional): Additional text to be appended into the ChatGPT prompt.
      
    Returns:
      tuple: (center_x, center_y) coordinates of the found UI element.
    """
    # Normalize the task name.
    task_name = task_name.lower().replace(" ", "_")
    clicks_dir = os.path.join(os.getcwd(), "recordings", "clicks")
    input_examples_file = os.path.join(clicks_dir, f"{task_name}_input.json")
    output_examples_file = os.path.join(clicks_dir, f"{task_name}_output.json")
    
    input_examples = load_json_examples(input_examples_file)
    output_examples = load_json_examples(output_examples_file)
    
    example_text = ""
    for inp, out in zip(input_examples, output_examples):
        example_text += f"Example:\nInput: {json.dumps(inp, indent=2)}\nOutput: {json.dumps(out, indent=2)}\n\n"
    
    additional_guide = ""
    if guide.strip():
        additional_guide = f"\nAdditional Guide:\n{guide}\n"
    
    # Connect to the target application window (e.g., Tableau)
    windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
    if not windows:
        print("No Tableau window found.")
        sys.exit(1)
    
    def window_area(win):
        rect = win.rectangle()
        return (rect.right - rect.left) * (rect.bottom - rect.top)
    
    target_window = max(windows, key=window_area)
    print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")
    
    app = Application(backend="uia").connect(handle=target_window.handle)
    main_window = app.window(handle=target_window.handle)
    
    new_ui_tree = dump_ui_tree(main_window.element_info)
    new_snapshot_str = json.dumps(new_ui_tree, indent=2)
    
    # Build the full inference prompt.
    full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task.
{example_text}
{additional_guide}
Now, given the current UI snapshot and following the examples, return ONLY the runtime_id of the UI element that should be clicked.
Current UI snapshot:
{new_snapshot_str}
"""
    print("Full prompt being sent to ChatGPT:")
    # print(full_prompt)  # Uncomment to view the prompt if needed.
    
    predicted_runtime_id = openai_infer(full_prompt)
    print("Predicted runtime ID:", predicted_runtime_id)
    
    target_elem = search_for_runtime_id(main_window, predicted_runtime_id)
    if target_elem is not None:
        rect = target_elem.rectangle()
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        print(f"Element center: ({center_x}, {center_y})")
        return center_x, center_y
    else:
        print("Could not locate the element with the predicted runtime ID.")
        return None

# ============================================================
# Main Guard: Test getElementCenter
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_name = sys.argv[1]
    else:
        task_name = input("Enter the task name (e.g., 'swap_x_and_y'): ").strip()
    
    guide = ""
    if len(sys.argv) > 2:
        guide = sys.argv[2]
    else:
        guide = input("Enter additional guide text (or press Enter for none): ").strip()
    
    center = getElementCenter(task_name, guide)
    if center:
        print("Returned element center:", center)
    else:
        print("Failed to get element center.")
