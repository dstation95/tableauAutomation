import os
import json
from pywinauto import Desktop

def get_control_tree(control):
    """
    Recursively build a dictionary with details of the given control and its children.
    """
    try:
        children = control.children()
    except Exception:
        children = []
    
    return {
        "control_type": control.element_info.control_type,
        "name": control.element_info.name,
        "automation_id": control.element_info.automation_id,
        "rectangle": str(control.element_info.rectangle),
        "children": [get_control_tree(child) for child in children]
    }

def main():
    # Get all top-level windows using the UI Automation backend
    desktop = Desktop(backend="uia")
    windows = desktop.windows()

    # Filter windows that have a title containing "tableau" (case-insensitive)
    tableau_windows = [win for win in windows if win.window_text() and "tableau" in win.window_text().lower()]

    # Create a dictionary to hold the element tree for each window
    results = {}
    for win in tableau_windows:
        title = win.window_text()
        results[title] = get_control_tree(win)

    # Ensure the output directory exists
    output_dir = "test"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "elements.json")

    # Write the result to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Element tree saved to {output_file}")

if __name__ == '__main__':
    main()
