import os
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop

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

def capture_ui_snapshot(output_filename):
    # Connect to the Tableau - B window.
    windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
    if not windows:
        print("No Tableau window found.")
        return
    def window_area(win):
        rect = win.rectangle()
        return (rect.right - rect.left) * (rect.bottom - rect.top)
    target_window = max(windows, key=window_area)
    app = Application(backend="uia").connect(handle=target_window.handle)
    main_window = app.window(handle=target_window.handle)
    # Capture the UI tree.
    ui_tree = dump_ui_tree(main_window.element_info)
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(ui_tree, f, indent=2)
    print(f"UI snapshot saved to {output_filename}")

if __name__ == "__main__":
    output_filename = "tableau_ui_snapshot.json"
    capture_ui_snapshot(output_filename)
