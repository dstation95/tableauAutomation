import os
import json
import openai  # Requires: pip install openai
import pandas as pd  # For reading CSV or XLSX
import sys
import time
import re
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui

MAIN_WINDOW = None

def connect_to_tableau():
    """
    Connects to the Tableau window only once and caches the connection.
    If accessing the element_info fails (e.g. due to COM errors), it retries the connection.
    Returns the main_window object.
    """
    global MAIN_WINDOW
    if MAIN_WINDOW is None:
        windows = Desktop(backend="uia").windows(title_re=".*Tableau Public - B.*", visible_only=True)
        if not windows:
            print("No Tableau window found!")
            sys.exit(1)
        def window_area(win):
            rect = win.rectangle()
            return (rect.right - rect.left) * (rect.bottom - rect.top)
        target_window = max(windows, key=window_area)
        print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")
        app = Application(backend="uia").connect(handle=target_window.handle)
        MAIN_WINDOW = app.window(handle=target_window.handle)
    # Test access to element_info with a retry mechanism
    try:
        _ = MAIN_WINDOW.element_info
    except Exception as e:
        print("Error accessing element_info, reinitializing connection:", e)
        MAIN_WINDOW = None
        return connect_to_tableau()
    return MAIN_WINDOW
