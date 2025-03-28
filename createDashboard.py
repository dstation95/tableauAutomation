#!/usr/bin/env python3
import os
import json
import time
import openai
from pywinauto import Desktop
from connectScreen import connect_to_tableau
from findElement import findElement  # make sure this exists
# from executeDrag import executeDrag  # expects three arguments

# ------------------------------------------------------------
# Set OpenAI API credentials for GPT-4o mini
# ------------------------------------------------------------
openai.api_key = "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"
MODEL_NAME = "gpt-4o-mini-2024-07-18"

# ------------------------------------------------------------
# Helper Functions for Dashboard Layout Extraction
# ------------------------------------------------------------
def executeDragByPixels(source, target):
    """
    Drags the mouse from the source pixel position to the target pixel position.
    Parameters:
      source (tuple): (x, y) coordinates to start dragging.
      target (tuple): (x, y) coordinates to end dragging.
    """
    import pyautogui
    # Move to the source position and perform a drag operation to the target position.
    pyautogui.moveTo(source[0], source[1], duration=0.2)
    pyautogui.dragTo(target[0], target[1], duration=0.5, button='left')

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
    try:
        rect_str = rectangle_to_str(elem_info.rectangle)
    except Exception:
        rect_str = ""
    rt_str = runtime_id_to_str(elem_info.runtime_id)
    return f"{control_type}|{class_name}|{auto_id}|{name}|{rect_str}|{rt_str}"

def parse_rectangle(rect_str):
    if not rect_str.strip():
        return None
    try:
        parts = rect_str.split("-")
        if len(parts) != 4:
            return None
        return tuple(int(part) for part in parts)
    except Exception as e:
        print("Error parsing rectangle:", e)
        return None

def extract_geometry_from_composite(composite):
    try:
        parts = composite.split("|")
        if len(parts) < 6:
            return None
        control_type, class_name, automation_id, name, rect_str, _ = parts
        rect = parse_rectangle(rect_str)
        if rect is None:
            return None
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        center_x = left + width // 2
        center_y = top + height // 2
        return {
            "control_type": control_type,
            "class_name": class_name,
            "automation_id": automation_id,
            "name": name,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "center_x": center_x,
            "center_y": center_y
        }
    except Exception as e:
        print("Error extracting geometry:", e)
        return None

def dump_ui_tree(elem_info):
    tree = {
        "composite": generate_composite_id(elem_info),
        "children": []
    }
    try:
        children = elem_info.children()
    except Exception:
        children = []
    for child in children:
        tree["children"].append(dump_ui_tree(child))
    return tree

def captureFullSnapshot():
    main_window = connect_to_tableau()
    return dump_ui_tree(main_window.element_info)

def is_inside(inner, outer):
    return (inner[0] >= outer[0] and inner[1] >= outer[1] and
            inner[2] <= outer[2] and inner[3] <= outer[3])

def extractDashboardElements(full_snapshot):
    dashboard_overlay = None
    def find_dashboard_node(node):
        nonlocal dashboard_overlay
        composite = node.get("composite", "")
        if "DashboardWidget.DashboardGridOverlayWidget" in composite:
            dashboard_overlay = node
            return True
        for child in node.get("children", []):
            if find_dashboard_node(child):
                return True
        return False

    find_dashboard_node(full_snapshot)
    if dashboard_overlay is None:
        print("Dashboard overlay element not found.")
        return []
    overlay_geo = extract_geometry_from_composite(dashboard_overlay["composite"])
    if overlay_geo is None:
        print("Could not parse dashboard overlay geometry.")
        return []
    collected = {}
    def traverse(node):
        geo = extract_geometry_from_composite(node.get("composite", ""))
        if geo:
            rect = (geo["left"], geo["top"], geo["right"], geo["bottom"])
            overlay_rect = (overlay_geo["left"], overlay_geo["top"], overlay_geo["right"], overlay_geo["bottom"])
            if geo["width"] > 0 and geo["height"] > 0 and is_inside(rect, overlay_rect):
                key = json.dumps(geo, sort_keys=True)
                collected[key] = geo
        for child in node.get("children", []):
            traverse(child)
    traverse(full_snapshot)
    elements = list(collected.values())
    elements.sort(key=lambda x: (x["top"], x["left"]))
    return elements

# ------------------------------------------------------------
# Clear previous dashboard state (if any)
# ------------------------------------------------------------
def clear_previous_dashboard_state():
    prev_file = os.path.join(os.getcwd(), "previous_dashboard_commands.txt")
    if os.path.exists(prev_file):
        os.remove(prev_file)
    test_folder = os.path.join(os.getcwd(), "test")
    if os.path.exists(test_folder):
        for filename in os.listdir(test_folder):
            file_path = os.path.join(test_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    print("Previous dashboard state cleared.")

# ------------------------------------------------------------
# ChatGPT Agent Call for Dashboard Decisions
# ------------------------------------------------------------
def callDashboardAgent(dashboard_snapshot, dashboard_summary, previous_commands):
    print("commands", previous_commands, "end")
    prompt = f"""
You are a specialized dashboard design assistant for Tableau. The following is the current layout snapshot of the dashboard.
Each element is described by its UI properties and geometry (left, top, width, height, center_x, center_y).

Current Dashboard Layout (JSON array):
{json.dumps(dashboard_snapshot, indent=2)}

Dashboard summary:
{dashboard_summary}

Previous actions executed:
{previous_commands}

Based on effective dashboard design practices in Tableau:
- Existing sheets are represented by .VisualWidget elements and their boundaries.
- When placing a new sheet, it may be dragged into an empty area or split an existing widget.
- The new sheet should be placed so that the overall dashboard remains clear and visually appealing.
- In addition i beleive all target psostion should be within a rectange of dashboard zone widget after already placing the first sheet
 - The zone widges should be the exisitng grapsh adn you should palce on them on the sides of the graphs to split the widget and add the graph in that split
and make sure it looks good, make sure you dont drag to a small area and give good space to make sure the drag works

Decide on the next action. If further changes are needed, return a JSON object with:
{{
  "action": "drag",
  "sheet_name": "Sheet X", 
  "drag_variable": "Sheet X", 
  "target_position": {{"x": 123, "y": 456}},
  "status": "continue"
}}
If no further changes are required and the dashboard is complete, return: and only do this once the previous commands are enough to make a good dashboard and use multiple graphs and use ALL the sheets listed out once
{{"status": "finish"}}

Return only the JSON object. Please start with the curly brace and make sure you do not start with the word json a dn start withthe actual object and not the word json
"""
    response = openai.chat.completions.create(
         model=MODEL_NAME,
         messages=[
             {"role": "system", "content": "You are an expert dashboard designer for Tableau."},
             {"role": "user", "content": prompt}
         ],
         stream=False
    )
    agent_reply = response.choices[0].message.content.strip()
    print(agent_reply)
    try:
        result = json.loads(agent_reply)
        return result
    except Exception as e:
        print("Error parsing ChatGPT response:", e)
        print("Response received:", agent_reply)
        return None

# ------------------------------------------------------------
# Main Function: createDashboard
# ------------------------------------------------------------
def createDashboard(dashboard_summary):
    """
    Clears previous dashboard state, then continuously captures the current dashboard layout,
    calls the ChatGPT agent to decide on the next dashboard action, and performs that action.
    The process repeats until the agent returns {"status": "finish"}.
    """
    clear_previous_dashboard_state()
    previous_commands = ""
    iteration = 0

    while True:
        iteration += 1
        print(f"--- Dashboard iteration {iteration} ---")
        full_snapshot = captureFullSnapshot()
        dashboard_elements = extractDashboardElements(full_snapshot)
        
        snapshot_file = os.path.join(os.getcwd(), "test", f"dashboard_snapshot_iter_{iteration}.json")
        os.makedirs(os.path.join(os.getcwd(), "test"), exist_ok=True)
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(dashboard_elements, f, indent=2)
        print(f"Dashboard snapshot saved to {snapshot_file}")

        agent_decision = callDashboardAgent(dashboard_elements, dashboard_summary, previous_commands)
        if agent_decision is None:
            print("Agent returned no decision. Exiting loop.")
            break

        print("Agent decision:", agent_decision)
        previous_commands += json.dumps(agent_decision) + "\n"
        
        if str(agent_decision.get("status", "")).lower() == "finish":
            print("Dashboard creation complete per agent instruction.")
            break

        if str(agent_decision.get("action", "")).lower() == "drag":
            drag_variable = agent_decision.get("drag_variable")
            target_position = agent_decision.get("target_position", {})
            if not drag_variable or "x" not in target_position or "y" not in target_position:
                print("Incomplete drag instruction from agent. Skipping iteration.")
                continue

            source_position = findElement(drag_variable, "DO NOT RETURN SHEET 1 PLEASE DRAG SOMETHIGN THAT COTNAISN A NUMBER THAT IS NOt ONE, DONT FOLLOW THE TRAINIGN EXAMPLES EXACTLY AND DOTN JUST DRAG SHEET 1 DO NOT DRAG the one wiht the name sheet 1 and instead drag the one that contains that contains the name wiht the same sheet number as this {drag_variable} and it should be under sheets and should have the exact sheet name as sown before with the exact number, MAKE SURE THE NUMBER mathces, dont follow the recoridng exactly adn instead find the lement with the name that has the sheet number that i have given you", expected_sheet_name=f"{drag_variable}")
            if source_position is None:
                print(f"Could not find element for variable '{drag_variable}'. Skipping iteration.")
                continue

            print(f"Dragging '{drag_variable}' from {source_position} to target position ({target_position['x']}, {target_position['y']}).")
            try:
                # Pass source, target position tuple, and third parameter as a string representation of target.
                executeDragByPixels(source_position, (target_position['x'], target_position['y']))

                print("Drag action executed successfully.")
            except Exception as e:
                print("Error executing drag:", e)
        else:
            print("Agent did not specify a drag action. Exiting loop.")
            break

        time.sleep(3)
    
    return "Dashboard creation process concluded."

# ------------------------------------------------------------
# Temporary Main for Testing createDashboard
# ------------------------------------------------------------
if __name__ == "__main__":
    dashboard_summary = (
        "Sheet 2: Sales by Region colored (Bar Chart). "
        "Sheet 3: Profit Trend colored (Bar Chart). "
        "Sheet 4: Market Share (Bar Chart). "
        "Ignore Sheet1 as it is blank."
    )
    result = createDashboard(dashboard_summary)
    print(result)
