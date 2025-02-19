import pyautogui
import time
import sys

def navigateSheets(task_name, quantity):
    """
    Navigates between sheets within an application (such as Tableau) based on the specified task.

    Parameters:
      task_name (str): A string specifying the navigation task. Valid values are:
                       - "forwards": navigates forward through sheets.
                       - "backwards": navigates backward through sheets.
                       - "new": opens a new sheet.
      quantity (int): For "forwards" and "backwards", the number of times to send the navigation keystroke.
                      For "new", this parameter is ignored.
    
    Behavior:
      - If task_name is "new", the function simulates pressing Ctrl+M.
      - If task_name is "forwards", it simulates pressing Ctrl+Tab 'quantity' times.
      - If task_name is "backwards", it simulates pressing Ctrl+Shift+Tab 'quantity' times.
    """
    task_name = task_name.lower()
    
    if task_name == "new":
        print("Navigating to a new sheet by pressing Ctrl+M")
        pyautogui.hotkey('ctrl', 'm')
    elif task_name == "forwards":
        print(f"Navigating forwards {quantity} times using Ctrl+Tab")
        for i in range(quantity):
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(0.1)  # brief pause between keystrokes
    elif task_name == "backwards":
        print(f"Navigating backwards {quantity} times using Ctrl+Shift+Tab")
        for i in range(quantity):
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            time.sleep(0.1)  # brief pause between keystrokes
    else:
        print("Invalid task_name. Valid inputs are: 'forwards', 'backwards', or 'new'.")

if __name__ == "__main__":
    # For testing purposes: accept command-line arguments.
    if len(sys.argv) >= 3:
        task_name_input = sys.argv[1]
        try:
            quantity_input = int(sys.argv[2])
        except ValueError:
            print("Quantity must be an integer. Defaulting to 1.")
            quantity_input = 1
    else:
        task_name_input = input("Enter task_name (forwards, backwards, new): ").strip()
        try:
            quantity_input = int(input("Enter quantity (ignored for 'new'): ").strip())
        except ValueError:
            print("Quantity must be an integer. Defaulting to 1.")
            quantity_input = 1

    navigateSheets(task_name_input, quantity_input)
