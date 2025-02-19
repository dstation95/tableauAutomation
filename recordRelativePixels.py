import os
import time
import json
import pyautogui
from pynput import keyboard
from pywinauto import Desktop

# ------------------------------------------------------------
# Production Setup: Create Base Folder Structure for Pixel Recordings
# ------------------------------------------------------------
base_recordings_dir = os.path.join(os.getcwd(), "recordings")
pixel_dir = os.path.join(base_recordings_dir, "pixel")
os.makedirs(pixel_dir, exist_ok=True)

# Prompt for the origin element name (this will be used as the output file name)
origin_name = input("Enter the origin element name: ").strip()

# Global variables to store the anchor (first backtick release) and the relative click positions.
anchor_center = None
relative_distances = []

# Timestamp to help debounce repeated recordings.
last_record_time = 0

def on_release(key):
    """
    Keyboard release handler:
      - When the backtick key (`) is released:
          * If the anchor is not set, record the current mouse position as the anchor.
          * Otherwise, record the current mouse position relative to the anchor.
      - When the ESC key is released, end the recording.
    """
    global anchor_center, relative_distances, last_record_time
    try:
        # Check if backtick key was released.
        if key.char == '`':
            current_time = time.time()
            # Debounce: only record if at least 0.2 seconds have passed since the last record.
            if current_time - last_record_time < 0.2:
                return
            last_record_time = current_time

            # Get the current mouse position.
            current_pos = pyautogui.position()
            print(f"Backtick released. Current mouse position: {current_pos}")
            if anchor_center is None:
                anchor_center = current_pos
                print(f"Anchor set at (raw screen position): {anchor_center}")
            else:
                dx = current_pos[0] - anchor_center[0]
                dy = current_pos[1] - anchor_center[1]
                relative_distances.append({"dx": dx, "dy": dy})
                print(f"Recorded relative distance: dx = {dx}, dy = {dy}")
    except AttributeError:
        # Check for special keys.
        if key == keyboard.Key.esc:
            print("ESC pressed. Ending recording.")
            return False  # Stop the listener

def compute_relative_point(anchor, relative):
    """
    Computes a new point by adding the relative dx and dy to the anchor coordinates.
    """
    new_x = anchor[0] + relative["dx"]
    new_y = anchor[1] + relative["dy"]
    return (int(round(new_x)), int(round(new_y)))

def click_relative_point(anchor, relative):
    """
    Computes the target point from the anchor and relative offset, then simulates a click.
    """
    target = compute_relative_point(anchor, relative)
    print(f"Clicking at computed target: {target}")
    pyautogui.click(target[0], target[1])

def main():
    global anchor_center, relative_distances

    print("Starting recording of relative positions...")
    print(" • Press the backtick key (`) and release it to record a position relative to the anchor.")
    print("   (The very first backtick release sets the anchor; subsequent releases record offsets.)")
    print(" • Press ESC to end recording and save the data.")

    # Start the keyboard listener (using on_release).
    with keyboard.Listener(on_release=on_release) as listener:
        listener.join()

    # Add an index field to each relative recording.
    for idx, rel in enumerate(relative_distances, start=1):
        rel["index"] = idx

    # Save the relative distances to a JSON file named after the origin element in recordings/pixel.
    output_file = os.path.join(pixel_dir, f"{origin_name.lower().replace(' ', '_')}.json")
    try:
        with open(output_file, "w") as f:
            json.dump(relative_distances, f, indent=4)
        print(f"Relative distances saved to {output_file}")
    except Exception as e:
        print(f"Error writing file: {e}")

    # Optional: Test clicking at each recorded relative position.
    # if anchor_center and relative_distances:
    #     print("\nTesting clicks based on recorded relative positions...")
    #     for idx, relative in enumerate(relative_distances, start=1):
    #         print(f"Test click {idx}:")
    #         click_relative_point(anchor_center, relative)
    #         time.sleep(1)  # Pause between clicks to observe the behavior.

if __name__ == "__main__":
    main()
