import os
import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui

# ------------------------------------------------------------
# Production Setup: Create Base Folder Structure for Double Click Recordings
# ------------------------------------------------------------
base_recordings_dir = os.path.join(os.getcwd(), "recordings")
double_dir = os.path.join(base_recordings_dir, "double")
os.makedirs(double_dir, exist_ok=True)

# ------------------------------------------------------------
# Step 1: Get Task Prompt and Derive File Names
# ------------------------------------------------------------
task_prompt = input("Enter the system prompt for this double click recording (e.g., 'menu double click'): ").strip()
file_prefix = task_prompt.lower().replace(" ", "_")

input_file_1 = os.path.join(double_dir, f"{file_prefix}_1_input.json")
output_file_1 = os.path.join(double_dir, f"{file_prefix}_1_output.json")
input_file_2 = os.path.join(double_dir, f"{file_prefix}_2_input.json")
output_file_2 = os.path.join(double_dir, f"{file_prefix}_2_output.json")

# A helper to load existing examples from a JSON file (expects a JSON array)
def load_examples(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading JSON from", filename, ":", e)
    return []

# A helper to append one example (dictionary) to a JSON file (as an array).
def append_example(filename, example):
    examples = load_examples(filename)
    examples.append(example)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    print(f"Appended training example to {filename}")

# ------------------------------------------------------------
# Step 2: Connect to Target Application (e.g., Tableau)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Step 3: Helper Functions for Snapshot and Runtime ID
# ------------------------------------------------------------
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
        subtree = dump_ui_tree(child)
        subtree["composite"] = f"[{index}] " + subtree["composite"]
        tree["children"].append(subtree)
    return tree

# ------------------------------------------------------------
# Step 4: Take a Live Snapshot and Save Training Input for a Click
# ------------------------------------------------------------
def take_snapshot_and_save_input(input_filename, prompt):
    ui_tree = dump_ui_tree(main_window.element_info)
    training_input = {
        "ui_snapshot": ui_tree,
        "prompt": prompt
    }
    append_example(input_filename, training_input)
    return ui_tree

print("Taking snapshot for first click (INPUT 1)...")
snapshot1 = take_snapshot_and_save_input(input_file_1, task_prompt)
# Optionally, save a screenshot (disabled for production)
# screenshot1_filename = os.path.join(double_dir, f"{file_prefix}_1_current.png")
# main_window.capture_as_image().save(screenshot1_filename)
# print(f"Screenshot for first click saved as {screenshot1_filename}")

# ------------------------------------------------------------
# Step 5: Wait for First Click and Record its Runtime ID (Output 1)
# ------------------------------------------------------------
recorded_runtime_id1 = None

def on_click_first(x, y, button, pressed):
    global recorded_runtime_id1
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"First click detected at: {click_data}")
        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Click outside window; ignoring.")
            return False
        time.sleep(0.5)
        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info for first click:", e)
            return False
        composite = generate_composite_id(clicked_elem_info)
        recorded_runtime_id1 = composite.split("|")[-1]
        print("First click recorded, runtime ID:", recorded_runtime_id1)
        return False

with mouse.Listener(on_click=on_click_first) as listener:
    listener.join()

time.sleep(1)
if not recorded_runtime_id1:
    print("No runtime ID recorded for first click.")
    sys.exit(1)

output1 = {"runtime_id": recorded_runtime_id1}
append_example(output_file_1, output1)

# ------------------------------------------------------------
# Step 6: Take a New Snapshot for the Second Click (INPUT 2)
# ------------------------------------------------------------
print("Taking snapshot for second click (INPUT 2)...")
time.sleep(2)
snapshot2 = take_snapshot_and_save_input(input_file_2, task_prompt)
# Optionally, save a screenshot (disabled for production)
# screenshot2_filename = os.path.join(double_dir, f"{file_prefix}_2_current.png")
# main_window.capture_as_image().save(screenshot2_filename)
# print(f"Screenshot for second click saved as {screenshot2_filename}")

# ------------------------------------------------------------
# Step 7: Wait for Second Click and Record its Runtime ID (Output 2)
# ------------------------------------------------------------
recorded_runtime_id2 = None

def on_click_second(x, y, button, pressed):
    global recorded_runtime_id2
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Second click detected at: {click_data}")
        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Click outside window; ignoring.")
            return False
        time.sleep(0.5)
        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info for second click:", e)
            return False
        composite = generate_composite_id(clicked_elem_info)
        recorded_runtime_id2 = composite.split("|")[-1]
        print("Second click recorded, runtime ID:", recorded_runtime_id2)
        return False

with mouse.Listener(on_click=on_click_second) as listener:
    listener.join()

time.sleep(1)
if not recorded_runtime_id2:
    print("No runtime ID recorded for second click.")
    sys.exit(1)

output2 = {"runtime_id": recorded_runtime_id2}
append_example(output_file_2, output2)

print("Double click recording complete.")
print("First click runtime ID:", recorded_runtime_id1)
print("Second click runtime ID:", recorded_runtime_id2)
