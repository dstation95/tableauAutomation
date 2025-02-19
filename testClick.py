import pyautogui 


# windows = Desktop(backend="uia").windows(title_re=".*Tableau - B.*", visible_only=True)
# # app = Application(backend="uia").connect(process=24008)
# # windows = app.windows()
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


pyautogui.click(1377,  -831)