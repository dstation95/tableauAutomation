import os
import time
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui
import openai

# ============================================================
# Set OpenAI API credentials for GPT-4o mini
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

# ============================================================
# Main Function: executeExpandedClick(task_name, guide="")
# ============================================================
def executeExpandedClick(task_name, guide=""):
    """
    Performs a UI click based on a click recording specified by task_name.
    If task_name (i.e. the input prompt) is empty, then only the additional guide text
    is used for inference.
    
    Parameters:
      task_name (str): The task name used to locate JSON example files in the recordings/clicks folder.
      guide (str, optional): Additional text to be added into the ChatGPT prompt.
    
    Returns:
      tuple: The (x, y) coordinates of the center of the clicked UI element.
    """
    # Normalize the task name: lowercase and replace spaces with underscores.
    if (task_name):
        task_name = task_name.lower().strip()
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
    
    # ------------------------------------------------------------
    # Capture a New UI Snapshot (including popups) from the major "Tableau" window.
    # ------------------------------------------------------------
    time.sleep(2)
    all_windows = Desktop(backend="uia").windows(visible_only=True)
    if not all_windows:
        print("No windows found.")
        sys.exit(1)
    
    # Look for the window whose title is exactly "Tableau"
    major_tableau_windows = [w for w in all_windows if w.window_text().strip() == "Tableau"]
    if not major_tableau_windows:
        print("No major Tableau window found.")
        sys.exit(1)
    
    def window_area(win):
        rect = win.rectangle()
        return (rect.right - rect.left) * (rect.bottom - rect.top)
    
    target_window = max(major_tableau_windows, key=window_area)
    print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")
    
    app = Application(backend="uia").connect(handle=target_window.handle)
    main_window = app.window(handle=target_window.handle)
    
    composite_snapshot = {
        "main_window": dump_ui_tree(main_window.element_info),
        "popups": []
    }
    
    tableau_pid = main_window.process_id()
    
    # Look for additional visible windows that belong to the same process.
    for win in all_windows:
        if win.handle != target_window.handle and win.process_id() == tableau_pid:
            print(f"Found additional window: Handle {win.handle}, Title: {win.window_text()}")
            composite_snapshot["popups"].append({
                "handle": win.handle,
                "title": win.window_text(),
                "ui_tree": dump_ui_tree(win.element_info)
            })
    
    new_snapshot_str = json.dumps(composite_snapshot, indent=2)
    print("Composite UI Snapshot captured.")
    
    
    # ------------------------------------------------------------
    # Build the Full Prompt for Inference.
    # If the task_name is empty, use only the guide.
    # ------------------------------------------------------------
    if not task_name:
        full_prompt = f"""
        Follow these directions to figure out which element from the snapshot you need to find and return the runtimeID associted wiht the directions
        {additional_guide}\n
        {additional_guide}
        Now, given the current UI snapshot and following the examples, return ONLY the runtime_id of the UI element that should be clicked.
        and make the runtimeId returned be associted withe lement that fits the directions before
        Current UI snapshot:\n{new_snapshot_str}"""
    else:
        full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task.
{example_text}
{additional_guide}
Now, given the current UI snapshot and following the examples, return ONLY the runtime_id of the UI element that should be clicked.
Current UI snapshot:
{new_snapshot_str}
"""
    # ------------------------------------------------------------
    # Call the OpenAI Chat API for Inference.
    # ------------------------------------------------------------
    # print(full_prompt)
    predicted_runtime_id = openai_infer(full_prompt)
    print("Predicted runtime ID:", predicted_runtime_id)
    
    # ------------------------------------------------------------
    # Find the Element by Runtime ID and Click It.
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
        print(f"Element center: ({center_x}, {center_y})")
        return (center_x, center_y)
    else:
        print("Could not locate the element with the predicted runtime ID.")
        return None

# ============================================================
# Main Guard: call executeExpandedClick() with provided task name (and optional guide).
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        task_name = sys.argv[1]
    else:
        task_name = input("Enter the task name (or press Enter for none): ").strip()
    
    if len(sys.argv) > 2:
        guide = sys.argv[2]
    else:
        guide = input("Enter additional guide text (or press Enter for none): ").strip()
    
    center = executeExpandedClick(task_name, guide)
    if center:
        print("Returned element center:", center)
    else:
        print("Failed to get element center.")
