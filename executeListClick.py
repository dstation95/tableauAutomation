import os
import time
import json
import sys
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui
import openai
from executeClick import executeClick
from getElementCenter import getElementCenter
from executePixelClick import executeRelativeClick


# ------------------------------------------------------------
# New function: executeListClick
# ------------------------------------------------------------
def executeListClick(task_name1, task_name2, items):
    """
    Loops over a list of items. For each item:
      1. Clicks a button determined by task_name1 (via executeClick).
      2. Types in the current item.
      3. Clicks another button determined by task_name2 (via executeClick),
         passing a guide string that references the just-typed item.

    Args:
      task_name1 (str): The name of the first button/click action. (e.g., "open_input_dialog")
      task_name2 (str): The name of the second button/click action. (e.g., "submit_form")
      items (list of str): The list of strings to be typed/processed.

    Example usage:
      executeListClick("open_input_dialog", "submit_form", ["hello", "world", "test"])
    """
    value = None
    for index, item in enumerate(items, start=1):
        print(f"\nProcessing item {index}/{len(items)}: {item}")

        # 1) Click the first button (task_name1).
        print(f"Clicking task_name1: {task_name1}")
        if(not value):
            value = executeClick(task_name1, "should have LineEdit option to find the element to click")  
        else:
            executeRelativeClick("zero", 1, value[0], value[1])


        # 2) Type in the current item.
        time.sleep(0.3)  # Brief pause to ensure UI is ready for typing.
        print(f"Typing: {item}")
        pyautogui.hotkey('ctrl', 'a')  # Select all text in the title field.
        pyautogui.press('backspace')   # Clear the field.
        pyautogui.write(item, interval=0.05)

        # 3) Click the second button (task_name2).
        # Optionally, pass a guide referencing the typed item.
        guide_text = f"Processing item '{item}' just typed should be asscoited wiht that is clicked and be the first one that is found ."
        print(f"Clicking task_name2: {task_name2} with guide='{guide_text}'")
        # pyautogui.hotkey('ctrl', 'a')  # Select all text in the title field.
        # pyautogui.press('backspace')   # Clear the field.
        # value = getElementCenter(task_name2, guide=guide_text)
        # executeRelativeClick("searchedoption", 1, value[0], value[1] )
        # print(value)
        time.sleep(1)
        executeRelativeClick("searchedoption", 1, value[0], value[1])
        


        # Add any additional waits/logging if desired.
        time.sleep(0.3)

    print("\nAll items have been processed and the second task has been executed for each.")


# ------------------------------------------------------------
# Optional: Main guard for testing executeListClick
# ------------------------------------------------------------
if __name__ == "__main__":
    # Example usage: python this_script.py "open_input_dialog" "submit_form" "one,two,three"
    if len(sys.argv) >= 4:
        task_name1_arg = sys.argv[1]
        task_name2_arg = sys.argv[2]
        items_str = sys.argv[3]
        # Suppose we pass the list items as a comma-separated string.
        items_list = items_str.split(",")
    else:
        task_name1_arg = input("Enter the first task name: ").strip()
        task_name2_arg = input("Enter the second task name: ").strip()
        # Enter items as comma separated
        items_list = input("Enter comma-separated items: ").split(",")

    # Trim whitespace
    items_list = [x.strip() for x in items_list if x.strip()]

    executeListClick(task_name1_arg, task_name2_arg, items_list)
