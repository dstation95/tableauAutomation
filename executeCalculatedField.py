import os
import time
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui
import openai

from connectScreen import connect_to_tableau

# ============================================================
# Set OpenAI API credentials and model name
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

# ------------------------------------------------------------
# Load examples from a JSON file (expected to be a JSON array)
# ------------------------------------------------------------
def load_examples(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading JSON from", filename, ":", e)
    return []

# ------------------------------------------------------------
# OpenAI Inference helper
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Recursively search for a UI element by runtime ID.
# ------------------------------------------------------------
def search_for_runtime_id(wrapper, target_rt):
    try:
        _ = generate_composite_id(wrapper.element_info)
    except Exception:
        pass
    current_rt = runtime_id_to_str(wrapper.element_info.runtime_id)
    if current_rt == target_rt:
        return wrapper
    for child in wrapper.children():
        found = search_for_runtime_id(child, target_rt)
        if found is not None:
            return found
    return None

# ------------------------------------------------------------
# Helper to click at a relative offset from a base point.
# ------------------------------------------------------------
def click_relative_point(base, relative):
    new_x = base[0] + relative['dx']
    new_y = base[1] + relative['dy']
    point_int = (int(round(new_x)), int(round(new_y)))
    print(f"Clicking at computed point: {point_int}")
    pyautogui.click(point_int[0], point_int[1])

# ============================================================
# Main Function: executeCalculatedField(task_name, field_name, field_formula)
# ============================================================
def executeCalculatedField(task_name, field_name, field_formula):
    """
    Uses UI snapshot examples and OpenAI inference to identify the UI element to click,
    then simulates the click (with an additional relative offset) and types in a calculated field's details.

    Args:
      task_name (str): The task prompt (e.g., "swap x and y") used to find the JSON example files.
      field_name (str): The calculated field name to be typed.
      field_formula (str): The calculated field formula to be typed.
    """
    # Normalize the task name for file naming.
    file_prefix = task_name.lower().replace(" ", "_")
    # input_examples_file = f"{file_prefix}_input.json"
    # output_examples_file = f"{file_prefix}_output.json"

    clicks_dir = os.path.join(os.getcwd(), "recordings", "clicks")
    # Build full paths for the input and output examples files.
    input_examples_file = os.path.join(clicks_dir, f"{task_name}_input.json")
    output_examples_file = os.path.join(clicks_dir, f"{task_name}_output.json")
    
    input_examples = load_examples(input_examples_file)
    output_examples = load_examples(output_examples_file)
    
    example_text = ""
    for inp, out in zip(input_examples, output_examples):
        example_text += f"Example:\nInput: {json.dumps(inp, indent=2)}\nOutput: {json.dumps(out, indent=2)}\n\n"
    
    # Use the task_name as the instruction prompt.
    task_prompt = task_name
    
    # ------------------------------------------------------------
    # Connect to the Target Application Window (e.g., Tableau)
    # ------------------------------------------------------------
    # windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
    # if not windows:
    #     print("No Tableau window found.")
    #     sys.exit(1)
    
    # def window_area(win):
    #     rect = win.rectangle()
    #     return (rect.right - rect.left) * (rect.bottom - rect.top)
    
    # target_window = max(windows, key=window_area)
    # print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")
    
    # app = Application(backend="uia").connect(handle=target_window.handle)
    # main_window = app.window(handle=target_window.handle)
    main_window = connect_to_tableau()
    
    # ------------------------------------------------------------
    # Capture a New UI Snapshot and Screenshot
    # ------------------------------------------------------------
    new_ui_tree = dump_ui_tree(main_window.element_info)
    new_snapshot_str = json.dumps(new_ui_tree, indent=2)
    
    # Save a screenshot (for debugging, if desired)
    new_screenshot = main_window.capture_as_image()
    # new_screenshot_filename = f"{file_prefix}_current.png"
    # new_screenshot.save(new_screenshot_filename)
    # print(f"New screenshot saved as {new_screenshot_filename}")
    
    # ------------------------------------------------------------
    # Build the Full Prompt for Inference
    # ------------------------------------------------------------
    full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task. an
{example_text}
Now, given the current UI snapshot and based on what was clicked in the example, return ONLY the runtime_id of the UI element that should be clicked.
YOU SHOULD click the one with an automation ID of m_menuBtn
Current UI snapshot:
{new_snapshot_str}
"""
    predicted_runtime_id = openai_infer(full_prompt)
    print("Predicted runtime ID:", predicted_runtime_id)
    
    # ------------------------------------------------------------
    # Find the Target Element and Simulate Click (with a relative offset)
    # ------------------------------------------------------------
    target_elem = search_for_runtime_id(main_window, predicted_runtime_id)
    if target_elem is not None:
        print("Found target element.")
        rect = target_elem.rectangle()
        print("Element rectangle:", rect)
        print("Element control type:", target_elem.element_info.control_type)
        
        try:
            print("Attempting target_elem.click_input()")
            target_elem.click_input()
        except Exception as e:
            print("click_input() failed with error:", e)
        
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        anchor = (center_x, center_y)
        # Using a fixed relative offset; adjust dx and dy as needed.
        relative_offset = {"dx": -50, "dy": 15}
        time.sleep(0.5)
        click_relative_point(anchor, relative_offset)
    else:
        print("Could not locate the element with the predicted runtime ID.")
        sys.exit(1)
    
    # ------------------------------------------------------------
    # Type the Calculated Field Details
    # ------------------------------------------------------------
    time.sleep(0.5)  # Brief pause to ensure the field is focused
    print(f"Typing calculated field name: {field_name}")
    pyautogui.write(field_name, interval=0.05)
    pyautogui.press('tab')
    print(f"Typing calculated field formula: {field_formula}")
    pyautogui.hotkey('ctrl', 'a')  # Select all text in the title field.
    pyautogui.press('backspace')   # Clear the field.
    pyautogui.write(field_formula, interval=0.05)
    pyautogui.hotkey('ctrl', 'enter')
    print("Calculated field entry complete.")

# ============================================================
# Main Guard: Call executeCalculatedField() if run directly.
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) >= 4:
        task_name_arg = sys.argv[1]
        field_name_arg = sys.argv[2]
        field_formula_arg = sys.argv[3]
    else:
        task_name_arg = input("Enter the task prompt (e.g., 'swap x and y'): ").strip()
        field_name_arg = input("Enter the Calculated Field Name: ").strip()
        field_formula_arg = input("Enter the Calculated Field Function: ").strip()
    
    executeCalculatedField(task_name_arg, field_name_arg, field_formula_arg)
