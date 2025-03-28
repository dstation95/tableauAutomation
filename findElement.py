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
# Main Function: executeClick(task_name, guide="")
# ============================================================
def findElement(task_name, guide="", expected_sheet_name=None):
    """
    Returns the (x, y) coordinates of the center of the UI element corresponding to task_name.
    If expected_sheet_name is provided, the function will iterate over the element's siblings to find one whose name
    (ignoring spaces and case) contains the expected_sheet_name.
    """
    # Normalize the task name: lowercase and replace spaces with underscores.
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
    
    main_window = connect_to_tableau()
    new_ui_tree = dump_ui_tree(main_window.element_info)
    new_snapshot_str = json.dumps(new_ui_tree, indent=2)
    
    full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task.
{example_text}
important information:
{additional_guide}
Now, given the current UI snapshot and following the examples and extra information, return ONLY the runtime_id of the UI element that should be clicked.
Current UI snapshot:
{new_snapshot_str}
"""
    predicted_runtime_id = openai_infer(full_prompt)
    print("Predicted runtime ID:", predicted_runtime_id)
    
    target_elem = search_for_runtime_id(main_window, predicted_runtime_id)
    if expected_sheet_name and target_elem is not None:
        norm_expected = expected_sheet_name.lower().replace(" ", "")
        found_name = target_elem.element_info.name.lower().replace(" ", "") if target_elem.element_info.name else ""
        if norm_expected not in found_name:
            print("Initial element does not match expected sheet name. Searching siblings.")
            parent = target_elem.parent()
            if parent:
                for sibling in parent.children():
                    sib_name = sibling.element_info.name.lower().replace(" ", "") if sibling.element_info.name else ""
                    if norm_expected in sib_name:
                        target_elem = sibling
                        print("Found sibling matching expected sheet name:", sibling.element_info.name)
                        break
    if target_elem is not None:
        rect = target_elem.rectangle()
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        print(f"Element center: ({center_x}, {center_y})")
        return (center_x, center_y)
    else:
        print("Could not locate the element with the predicted runtime ID.")
        return None
