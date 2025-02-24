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
# Function: executePixelClick
# ============================================================
def findPixel(task_name, origin_element, index, isAxis=False, isMeasure=False):
    """
    Executes a two-step UI click that adds an offset based on an origin element.
    
    Parameters:
      task_name (str): The task name used to load training examples from recordings/clicks.
      origin_element: A UI element (or its name as a string) used to determine the origin for the offset lookup.
      index (int): The index to look up in the offset file (recordings/pixel/{ORIGIN_NAME}.json).
      isAxis (bool, optional): If True, the target click location uses the leftmost edge (with vertical centering).
      isMeasure (bool, optional): If True, the target click location uses the topmost edge (with horizontal centering).
                                  If both are False, the element's center is used.
    
    Behavior:
      - Loads input/output training examples from recordings/clicks.
      - Connects to the target application window.
      - Captures the current UI snapshot and builds a prompt.
      - Uses OpenAI to infer the runtime_id of the target element.
      - Searches for the UI element with that runtime_id.
      - Loads a relative pixel offset (dx, dy) from recordings/pixel/{ORIGIN_NAME}.json.
      - Computes the click coordinates:
            • If isAxis is True: uses the leftmost edge (x coordinate) and vertical center.
            • If isMeasure is True: uses the topmost edge (y coordinate) and horizontal center.
            • Otherwise: uses the center of the target element.
      - The final click coordinates are adjusted by the loaded offset.
      - Simulates a click at the computed coordinates.
      - Returns the final click coordinates as (x, y).
    """
    # Normalize the task name.
    task_name = task_name.lower().replace(" ", "_")
    
    # Define the recordings/clicks folder and build full paths for example files.
    clicks_dir = os.path.join(os.getcwd(), "recordings", "clicks")
    input_examples_file = os.path.join(clicks_dir, f"{task_name}_input.json")
    output_examples_file = os.path.join(clicks_dir, f"{task_name}_output.json")
    
    # Load training examples.
    input_examples = load_json_examples(input_examples_file)
    output_examples = load_json_examples(output_examples_file)
    
    example_text = ""
    for inp, out in zip(input_examples, output_examples):
        example_text += f"Example:\nInput: {json.dumps(inp, indent=2)}\nOutput: {json.dumps(out, indent=2)}\n\n"
    
    # ------------------------------------------------------------
    # Connect to the Target Application (e.g., Tableau)
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
    # Capture a New UI Snapshot (without saving any PNG)
    # ------------------------------------------------------------
    new_ui_tree = dump_ui_tree(main_window.element_info)
    new_snapshot_str = json.dumps(new_ui_tree, indent=2)
    
    # ------------------------------------------------------------
    # Build the Full Prompt for Inference
    # ------------------------------------------------------------
    full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task.
{example_text}
Now, given the current UI snapshot and following the examples, return ONLY the runtime_id of the UI element that should be clicked.
Current UI snapshot:
{new_snapshot_str}
"""
    # ------------------------------------------------------------
    # Call the OpenAI Chat API for Inference
    # ------------------------------------------------------------
    predicted_runtime_id = openai_infer(full_prompt)
    print("Predicted runtime ID:", predicted_runtime_id)
    
    # ------------------------------------------------------------
    # Find the Target Element by Runtime ID
    # ------------------------------------------------------------
    target_elem = search_for_runtime_id(main_window, predicted_runtime_id)
    if target_elem is None:
        print("Could not locate the element with the predicted runtime ID.")
        sys.exit(1)
    
    # Compute the target click location.
    rect = target_elem.rectangle()
    if isAxis:
        # Leftmost edge with vertical center.
        target_x = rect.left
        target_y = (rect.top + rect.bottom) // 2
    elif isMeasure:
        # Topmost edge with horizontal center.
        target_x = (rect.left + rect.right) // 2
        target_y = rect.top
        print("workin ")
    else:
        # Center of the element.
        target_x = (rect.left + rect.right) // 2
        target_y = (rect.top + rect.bottom) // 2
    print("Found target element. Element rectangle:", rect)
    
    # ------------------------------------------------------------
    # Load the Pixel Offset from the recordings/pixel folder.
    # ------------------------------------------------------------
    # Derive origin name from the origin_element (assumed provided as a string OR its name).
    origin_name = origin_element.lower().replace(" ", "_")
    pixel_dir = os.path.join(os.getcwd(), "recordings", "pixel")
    offset_file = os.path.join(pixel_dir, f"{origin_name}.json")
    
    offsets = load_json_examples(offset_file)
    if not offsets:
        print(f"No pixel offset data found in {offset_file}.")
        sys.exit(1)
    
    # Look up the offset with the matching index.
    dx, dy = None, None
    for entry in offsets:
        if entry.get("index") == index:
            dx = entry.get("dx")
            dy = entry.get("dy")
            break
    if dx is None or dy is None:
        print(f"No offset found for index {index} in {offset_file}.")
        sys.exit(1)
    
    print(f"Using offset: dx = {dx}, dy = {dy} from {offset_file} for index {index}.")
    
    # ------------------------------------------------------------
    # Compute the final click coordinates and simulate the click.
    # ------------------------------------------------------------
    new_click_x = target_x + dx
    new_click_y = target_y + dy
    print(f"Simulating click at offset coordinates: ({new_click_x}, {new_click_y})")
    # if(isAxis == True):
    #     pyautogui.rightClick(new_click_x, new_click_y)
    # elif(isMeasure == True):
    #     pyautogui.rightClick(new_click_x, new_click_y)
    # else:
    #     pyautogui.click(new_click_x, new_click_y)
    # print("Pixel click simulation complete.")
    
    # Return the final click coordinates.
    return new_click_x, new_click_y

# ============================================================
# Function: executeRelativeClick
# ============================================================
def findRelative(origin_name, index, current_x, current_y):
    """
    Executes a relative click based on a provided base (x, y) location.
    
    Parameters:
      origin_name (str): The ORIGIN_NAME used to look up a relative pixel offset 
                         from recordings/pixel/{origin_name}.json.
      index (int): The numerical index to look up in the offset file.
      current_x (int): The current x-coordinate from which to compute the new click location.
      current_y (int): The current y-coordinate from which to compute the new click location.
    
    Behavior:
      - Loads a relative pixel offset (dx, dy) from recordings/pixel/{origin_name}.json.
      - Computes the final click coordinates as (current_x + dx, current_y + dy).
      - Simulates a click at the computed coordinates.
      - Returns the final click coordinates as (x, y).
    """
    # Normalize the origin name.
    origin_name = origin_name.lower().replace(" ", "_")
    pixel_dir = os.path.join(os.getcwd(), "recordings", "pixel")
    offset_file = os.path.join(pixel_dir, f"{origin_name}.json")
    
    offsets = load_json_examples(offset_file)
    if offsets is None or len(offsets) == 0:
        print(f"No pixel offset data found in {offset_file}.")
        sys.exit(1)
    
    # Look up the offset for the given index.
    dx, dy = None, None
    for entry in offsets:
        if entry.get("index") == index:
            dx = entry.get("dx")
            dy = entry.get("dy")
            break
    if dx is None or dy is None:
        print(f"No offset found for index {index} in {offset_file}.")
        sys.exit(1)
    
    print(f"Using relative offset: dx = {dx}, dy = {dy} from {offset_file} for index {index}.")
    
    new_click_x = current_x + dx
    new_click_y = current_y + dy
    print(f"Simulating relative click at coordinates: ({new_click_x}, {new_click_y})")
    pyautogui.moveTo(new_click_x, new_click_y)
    # pyautogui.click(new_click_x, new_click_y)
    print("Relative click simulation complete.")
    
    return new_click_x, new_click_y

# ============================================================
# Main Guard: Call executePixelClick() or executeRelativeClick() if run directly.
# ============================================================
if __name__ == "__main__":
    # For testing, you can supply command-line arguments.
    # Example for executePixelClick:
    #   python script.py pixel TASK_NAME ORIGIN_NAME INDEX [isAxis]
    #
    # Example for executeRelativeClick:
    #   python script.py relative TASK_NAME ORIGIN_NAME INDEX CURRENT_X CURRENT_Y
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "pixel":
            task_name = sys.argv[2]
            origin_element = sys.argv[3]  # For testing, provided as a string ORIGIN_NAME.
            index = int(sys.argv[4])
            isAxis = sys.argv[5].lower() == "true" if len(sys.argv) > 5 else False
            
            # Connect to target window to use as placeholder origin element.
            windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
            if not windows:
                print("No Tableau window found for obtaining an origin element.")
                sys.exit(1)
            def window_area(win):
                rect = win.rectangle()
                return (rect.right - rect.left) * (rect.bottom - rect.top)
            target_window = max(windows, key=window_area)
            app = Application(backend="uia").connect(handle=target_window.handle)
            origin_elem = app.window(handle=target_window.handle)  # Placeholder element.
            
            final_coords = executePixelClick(task_name, origin_element, index, isAxis)
            print("executePixelClick returned coordinates:", final_coords)
        elif mode == "relative":
            task_name = sys.argv[2]
            origin_name = sys.argv[3]
            index = int(sys.argv[4])
            current_x = int(sys.argv[5])
            current_y = int(sys.argv[6])
            
            final_coords = executeRelativeClick(task_name, origin_name, index, current_x, current_y)
            print("executeRelativeClick returned coordinates:", final_coords)
        else:
            print("Invalid mode. Use 'pixel' or 'relative'.")
    else:
        # For interactive testing, you can prompt the user.
        mode = input("Enter mode ('pixel' or 'relative'): ").strip().lower()
        if mode == "pixel":
            task_name = input("Enter the task name (e.g., 'swap_x_and_y'): ").strip()
            origin_element = input("Enter the ORIGIN_NAME for offset lookup: ").strip()
            index = int(input("Enter the numerical index for offset lookup: ").strip())
            isAxis_input = input("Should the click use the leftmost edge instead of the center? (True/False): ").strip().lower()
            isAxis = isAxis_input == "true"
            
            windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
            if not windows:
                print("No Tableau window found for obtaining an origin element.")
                sys.exit(1)
            def window_area(win):
                rect = win.rectangle()
                return (rect.right - rect.left) * (rect.bottom - rect.top)
            target_window = max(windows, key=window_area)
            app = Application(backend="uia").connect(handle=target_window.handle)
            origin_elem = app.window(handle=target_window.handle)
            
            final_coords = executePixelClick(task_name, origin_element, index, isAxis)
            print("executePixelClick returned coordinates:", final_coords)
        elif mode == "relative":
            task_name = input("Enter the task name (for context, e.g., 'relative_click'): ").strip()
            origin_name = input("Enter the ORIGIN_NAME for offset lookup: ").strip()
            index = int(input("Enter the numerical index for offset lookup: ").strip())
            current_x = int(input("Enter the current x-coordinate: ").strip())
            current_y = int(input("Enter the current y-coordinate: ").strip())
            
            final_coords = executeRelativeClick(task_name, origin_name, index, current_x, current_y)
            print("executeRelativeClick returned coordinates:", final_coords)
        else:
            print("Invalid mode entered.")
