import os
import time
import json
import sys
from pynput import mouse, keyboard
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui

# ------------------------------------------------------------
# Production Setup: Create Base Folder Structure
# ------------------------------------------------------------
base_recordings_dir = os.path.join(os.getcwd(), "recordings")
clicks_dir = os.path.join(base_recordings_dir, "clicks")
os.makedirs(clicks_dir, exist_ok=True)

# ------------------------------------------------------------
# Step 1: Get the system prompt and derive file names
# ------------------------------------------------------------
prompt_text = input("Enter the system prompt for this recording (e.g., 'swap x and y'): ")
file_prefix = prompt_text.lower().replace(" ", "_")
input_filename = os.path.join(clicks_dir, f"{file_prefix}_input.json")
output_filename = os.path.join(clicks_dir, f"{file_prefix}_output.json")

def append_to_json_file(filename, data):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                arr = json.load(f)
            except Exception:
                arr = []
    else:
        arr = []
    arr.append(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2)
    print(f"Appended training example to {filename}")

# ------------------------------------------------------------
# Step 2: Connect to the Major "Tableau" Window
# ------------------------------------------------------------
time.sleep(2)
all_windows = Desktop(backend="uia").windows(visible_only=False)
# Select only those windows whose title is exactly "Tableau"
major_tableau_windows = [win for win in all_windows if win.window_text().strip() == "Tableau"]

if not major_tableau_windows:
    print("No major Tableau window found.")
    sys.exit(1)

def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

# Pick the largest "Tableau" window as the target.
target_window = max(major_tableau_windows, key=window_area)
print(f"Connected to major Tableau window: Handle {target_window.handle}, Title: {target_window.window_text()}")

app = Application(backend="uia").connect(handle=target_window.handle)
main_window = app.window(handle=target_window.handle)

# Use only these major Tableau windows for further processing.
all_tableau_windows = major_tableau_windows

# ------------------------------------------------------------
# Step 3: Capture the Entire Tableau UI Snapshot (All Elements)
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
    # Check for the toggle pattern availability.
    is_toggle = getattr(elem_info, "istogglepattern", False)
    return f"{control_type}|{class_name}|{auto_id}|{name}|{rect_str}|{rt_str}|istoggle:{is_toggle}"

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

# Build a composite snapshot for every valid Tableau window.
all_ui_snapshot = []
for win in all_tableau_windows:
    ui_tree = dump_ui_tree(win.element_info)
    all_ui_snapshot.append({
        "handle": win.handle,
        "title": win.window_text(),
        "ui_tree": ui_tree
    })

# Recursively collect all toggle-enabled elements from a dumped tree.
def collect_toggle_elements(tree):
    toggles = []
    if "istoggle:True" in tree.get("composite", ""):
        toggles.append(tree["composite"])
    for child in tree.get("children", []):
        toggles.extend(collect_toggle_elements(child))
    return toggles

toggle_elements = []
for win_snapshot in all_ui_snapshot:
    toggle_elements.extend(collect_toggle_elements(win_snapshot["ui_tree"]))

training_input = {
    "all_ui_snapshot": all_ui_snapshot,
    "toggle_elements": toggle_elements,
    "prompt": prompt_text
}

append_to_json_file(input_filename, training_input)
print("Full Tableau UI snapshot captured for recording (all elements, regardless of visibility).")
print(f"Collected {len(toggle_elements)} toggle-enabled elements.")

# ------------------------------------------------------------
# Step 4: Wait for the Backtick Key Press to Start Recording the Click
# ------------------------------------------------------------
print("Waiting for you to press the backtick key (`) to start recording the click...")

def on_key_press(key):
    try:
        if key.char == '`':
            print("Backtick key pressed. Now waiting for your next mouse click...")
            return False
    except AttributeError:
        pass

with keyboard.Listener(on_press=on_key_press) as k_listener:
    k_listener.join()

# ------------------------------------------------------------
# Step 5: Wait for a Mouse Click and Record the Output (Runtime ID)
# ------------------------------------------------------------
recorded_runtime_id = None

def point_in_any_window(x, y, windows_list):
    for win in windows_list:
        r = win.rectangle()
        if r.left <= x <= r.right and r.top <= y <= r.bottom:
            return True
    return False

def on_click(x, y, button, pressed):
    global recorded_runtime_id
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Mouse click detected at: {click_data}")
        # Verify that the click is inside one of the valid Tableau windows.
        if not point_in_any_window(x, y, all_tableau_windows):
            print("Click outside any valid Tableau window; ignoring.")
            return False
        # Allow time for any popup to appear after the click.
        time.sleep(0.5)
        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info:", e)
            return False
        composite = generate_composite_id(clicked_elem_info)
        print("Recorded composite ID:", composite)
        # Extract the runtime ID (assume it's the field before the istoggle flag).
        parts = composite.split("|")
        if len(parts) >= 7:
            recorded_runtime_id = parts[5]  # parts[5] holds the runtime ID.
        else:
            recorded_runtime_id = parts[-1]
        print("Extracted runtime ID:", recorded_runtime_id)
        return False

with mouse.Listener(on_click=on_click) as m_listener:
    m_listener.join()

time.sleep(1)
if recorded_runtime_id is None:
    print("No runtime ID recorded.")
    sys.exit(1)

training_output = {
    "runtime_id": recorded_runtime_id
}

append_to_json_file(output_filename, training_output)
print(f"Appended training output to {output_filename}")
