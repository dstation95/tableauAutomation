import os
import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui
import openai

# ============================================================
# Step 0: Configuration and Folder Setup for Drag Recordings
# ============================================================
openai.api_key = "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"
MODEL_NAME = "gpt-4o-mini-2024-07-18"

# Prompt for task and derive file prefix.
task_prompt = input("Enter the task prompt for drag-and-drop (e.g., 'drag order id'): ").strip()
file_prefix = task_prompt.lower().replace(" ", "_")

# Create folder structure: recordings/drag
base_recordings_dir = os.path.join(os.getcwd(), "recordings")
drag_dir = os.path.join(base_recordings_dir, "drag")
os.makedirs(drag_dir, exist_ok=True)

# Define training file names (read-only: if they exist, do not modify them)
input_examples_file = os.path.join(drag_dir, f"{file_prefix}_input.json")
output_examples_file = os.path.join(drag_dir, f"{file_prefix}_output.json")

# ============================================================
# Step 1: Helper Functions for UI Snapshot and Runtime ID Extraction
# ============================================================
def rectangle_to_str(rect):
    return f"{int(rect.left)}-{int(rect.top)}-{int(rect.right)}-{int(rect.bottom)}"

def runtime_id_to_str(runtime_id):
    if isinstance(runtime_id, str):
        return runtime_id
    try:
        return "_".join(str(item) for item in runtime_id)
    except Exception:
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
        subtree = dump_ui_tree(child)
        subtree["composite"] = f"[{index}] " + subtree["composite"]
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

def capture_snapshot():
    ui_tree = dump_ui_tree(main_window.element_info)
    return json.dumps(ui_tree, indent=2)

# ============================================================
# Step 2: Read-Only Training Files Loader (if they exist)
# ============================================================
def load_examples(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {filename}: {e}")
    return []

input_examples = load_examples(input_examples_file)
output_examples = load_examples(output_examples_file)

# ============================================================
# Step 3: Connect to Target Application (Tableau)
# ============================================================
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

# ============================================================
# Step 4: Capture a Live Snapshot and Save It (Input Training Example)
# ============================================================
new_ui_tree = dump_ui_tree(main_window.element_info)
new_snapshot_str = json.dumps(new_ui_tree, indent=2)
# Screenshot saving is disabled for production (commented out)
# screenshot_filename = os.path.join(drag_dir, f"{file_prefix}_current.png")
# main_window.capture_as_image().save(screenshot_filename)
# print(f"New screenshot saved as {screenshot_filename}")

training_input = {
    "ui_snapshot": new_ui_tree,
    "prompt": task_prompt
}
if not os.path.exists(input_examples_file):
    with open(input_examples_file, "w", encoding="utf-8") as f:
        json.dump([training_input], f, indent=2)
    print(f"Training input saved to {input_examples_file}")
else:
    print(f"Training input file {input_examples_file} exists (read-only).")

# ============================================================
# Step 5: Record Drag-and-Drop Gesture (Training Output)
# ============================================================
hold_runtime_id = None
drop_runtime_id = None

def on_drag(x, y, button, pressed):
    global hold_runtime_id, drop_runtime_id
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Drag start detected at: {click_data}")
        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Press outside window; ignoring.")
            return
        time.sleep(0.5)
        try:
            hold_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving hold element info:", e)
            return
        composite_hold = generate_composite_id(hold_info)
        hold_runtime_id = composite_hold.split("|")[-1]
        print("Recorded hold runtime ID:", hold_runtime_id)
    else:
        if hold_runtime_id is not None and drop_runtime_id is None:
            click_data = {"x": x, "y": y, "button": str(button)}
            print(f"Drag end detected at: {click_data}")
            rect = main_window.rectangle()
            if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
                print("Release outside window; ignoring.")
                return
            time.sleep(0.5)
            try:
                drop_info = UIAElementInfo.from_point(x, y)
            except Exception as e:
                print("Error retrieving drop element info:", e)
                return
            composite_drop = generate_composite_id(drop_info)
            drop_runtime_id = composite_drop.split("|")[-1]
            print("Recorded drop runtime ID:", drop_runtime_id)
            return False  # Stop the listener

with mouse.Listener(on_click=on_drag) as listener:
    listener.join()

time.sleep(1)
if hold_runtime_id is None or drop_runtime_id is None:
    print("Did not record both hold and drop runtime IDs.")
    sys.exit(1)

training_output = {
    "hold_runtime_id": hold_runtime_id,
    "drop_runtime_id": drop_runtime_id
}
if not os.path.exists(output_examples_file):
    with open(output_examples_file, "w", encoding="utf-8") as f:
        json.dump([training_output], f, indent=2)
    print(f"Training output saved to {output_examples_file}")
else:
    print(f"Training output file {output_examples_file} exists (read-only).")

print("Drag-and-drop training recording complete.")
print("Hold runtime ID:", hold_runtime_id)
print("Drop runtime ID:", drop_runtime_id)
