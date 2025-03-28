import os
import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui
import openai

from connectScreen import connect_to_tableau


# ============================================================
# Step 0: Set OpenAI API credentials and model name
# ============================================================

openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini-2024-07-18"
step_scroll_amount = -500

# ============================================================
# Helper Functions for UI Snapshot and Searching
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

def load_examples(filename):
    examples = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                examples = json.load(f)
            except Exception as e:
                print("Error loading JSON file:", e)
    return examples

# ============================================================
# Main Function: executeDrag(task_name, NAME, Location)
# ============================================================
def executeDrag(task_name, NAME, Location):
    """
    Executes a drag-and-drop task for the given task name.
    Reads the input/output example files from recordings/double,
    uses the extra parameters (NAME and Location) to build the prompt,
    and then simulates the drag-and-drop.

    New logic:
      1. Repeatedly (up to 4 times) capture a new UI snapshot,
         build a fresh ChatGPT prompt, and obtain predicted runtime IDs.
      2. If the hold element (found via its runtime ID) has an element_info.name
         that matches the expected NAME, proceed with the drag.
      3. Otherwise, retry the entire function.
    No PNG is saved.
    """
    # Normalize the task name.
    task_name = task_name.lower().replace(" ", "_")
    double_dir = os.path.join(os.getcwd(), "recordings", "double")
    input_examples_file = os.path.join(double_dir, f"{task_name}_input.json")
    output_examples_file = os.path.join(double_dir, f"{task_name}_output.json")
    input_examples = load_examples(input_examples_file)
    output_examples = load_examples(output_examples_file)
    example_text = ""
    for inp, out in zip(input_examples, output_examples):
        example_text += f"Example:\nInput: {json.dumps(inp, indent=2)}\nOutput: {json.dumps(out, indent=2)}\n\n"
    
    # Connect to the target application (e.g. Tableau)
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
    
    max_attempts = 4
    valid_hold_elem = None
    predicted_drop_rt = None
    finalAttemps = None
    
    for attempt in range(1, max_attempts+1):
        # print(f"\nAttempt {attempt} of {max_attempts}:")
        # Capture a new UI snapshot.
        new_ui_tree = dump_ui_tree(main_window.element_info)
        new_snapshot_str = json.dumps(new_ui_tree, indent=2)
        
        # Build the full inference prompt.
        full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for a drag-and-drop task.
{example_text}
Now, given the current UI snapshot, return ONLY a JSON object with two keys:
  "hold_runtime_id": <runtime ID of the UI element to drag from>,
  "drop_runtime_id": <runtime ID of the UI element to drop onto>.
You should select the hold element whose composite ID or name EXACTLY MATCHES THIS "{NAME}", dont pick sometign similair pick somethign that is exactly this name, and should be a tree ekement located similair to the example above.
For the drop element, choose the one whose composite ID or name includes the tag "{Location}".
Return only the JSON with those two keys. No extra formatting.
Current UI snapshot:
{new_snapshot_str}
"""
        # print("Full prompt being sent to ChatGPT:")
        # print(full_prompt)
        
        # Call the OpenAI API for inference.
        response = openai.chat.completions.create(
             model=MODEL_NAME,
             messages=[
                 {"role": "system", "content": "You are a UI automation assistant. Based on the given UI snapshot and instructions, return ONLY a JSON object with two keys: 'hold_runtime_id' and 'drop_runtime_id'."},
                 {"role": "user", "content": full_prompt}
             ],
             stream=False
        )
        try:
            predicted_text = response.choices[0].message.content
            # print("Model response:", predicted_text)
            predicted = json.loads(predicted_text)
        except Exception as e:
            print("Error parsing response as JSON:", e)
            predicted = {}
        
        predicted_hold_rt = predicted.get("hold_runtime_id")
        predicted_drop_rt = predicted.get("drop_runtime_id")
        if not predicted_hold_rt or not predicted_drop_rt:
            print("Model did not return both runtime IDs. Retrying...")
            time.sleep(0.1)
            continue
        
        # Find the UI elements by runtime ID.
        hold_elem = search_for_runtime_id(main_window, predicted_hold_rt)
        drop_elem = search_for_runtime_id(main_window, predicted_drop_rt)
        
        if hold_elem is None or drop_elem is None:
            print("Could not locate one or both elements. Retrying...")
            time.sleep(0.1)
            continue
        
        print(f"Found hold element with name: '{hold_elem.element_info.name}'")

        def normalize(name):
            return name.strip().lower().replace('_', ' ')

        if normalize(hold_elem.element_info.name.strip()) == normalize(NAME.strip()):
            print("Hold element name matches expected NAME.")
            valid_hold_elem = hold_elem
            finalAttemps = attempt
            break
        else:
            print(f"Hold element name '{hold_elem.element_info.name}' does not match expected '{NAME}'. Retrying...")
            final_rect = hold_elem.rectangle()
            final_center_x = (final_rect.left + final_rect.right) // 2
            final_center_y = (final_rect.top + final_rect.bottom) // 2
            
            pyautogui.moveTo(final_center_x, final_center_y, duration=0.2)
            time.sleep(0.1)
            pyautogui.scroll(-600)  
            time.sleep(0.3)
    
    if valid_hold_elem is None:
        print("Could not find a valid hold element after multiple attempts.")
        sys.exit(1)
    
    # Use the valid hold element and previously predicted drop element.
    drop_elem = search_for_runtime_id(main_window, predicted_drop_rt)
    if drop_elem is None:
        print("Drop element not found.")
        sys.exit(1)
    
    hold_rect = valid_hold_elem.rectangle()
    drop_rect = drop_elem.rectangle()
    hold_x = (hold_rect.left + hold_rect.right) // 2
    hold_y = (hold_rect.top + hold_rect.bottom) // 2

    # Adjust drop coordinates based on the target Location.
    if Location == "m_filterShelf":
        # For dragtoFilter, position the drop 10 pixels above the bottom of the target element,
        # and centered horizontally.
        drop_x = (drop_rect.left + drop_rect.right) // 2
        drop_y = drop_rect.bottom - 10
    elif Location in ["m_xAxisShelf", "m_yAxisShelf"]:
        drop_x = drop_rect.left + 30
        drop_y = (drop_rect.top + drop_rect.bottom) // 2
    else:
        drop_x = (drop_rect.left + drop_rect.right) // 2
        drop_y = (drop_rect.top + drop_rect.bottom) // 2

    print(f"Dragging from ({hold_x}, {hold_y}) to ({drop_x}, {drop_y})")
    
    pyautogui.moveTo(hold_x, hold_y, duration=0.3)
    pyautogui.mouseDown()
    pyautogui.moveTo(drop_x, drop_y, duration=0.5)
    pyautogui.mouseUp()
    pyautogui.moveTo(hold_x, hold_y, duration=0.3)

    
    # pyautogui.moveTo(hold_x, hold_y, duration=0.3)
    # pyautogui.mouseDown()
    # pyautogui.moveTo(drop_x, drop_y, duration=0.5)
    # pyautogui.mouseUp()
    # pyautogui.moveTo(hold_x, hold_y, duration=0.3)
    # pyautogui.scroll(-600)
    if finalAttemps > 0:
        print(f"Reverting scroll: scrolling up {finalAttemps} time(s).")
        for _ in range(finalAttemps):
            pyautogui.scroll(600)  # Reverse scroll amount (since step_scroll_amount is negative)
            time.sleep(0.3)
    print("Drag-and-drop operation completed.")

if __name__ == "__main__":
    if len(sys.argv) > 3:
        task_name = sys.argv[1]
        NAME = sys.argv[2]
        Location = sys.argv[3]
    else:
        task_name = input("Enter the drag task name (e.g., 'drag_order_id'): ").strip()
        NAME = input("Enter the NAME tag to match for the hold element: ").strip()
        Location = input("Enter the Location tag to match for the drop element: ").strip()
    executeDrag(task_name, NAME, Location)
