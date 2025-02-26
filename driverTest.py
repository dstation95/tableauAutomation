#!/usr/bin/env python3

import os
import json
import openai  # Requires: pip install openai
import pandas as pd  # For reading CSV or XLSX
import sys
import time
import re

# Import your existing automation functions
from executeClick import executeClick
from executeDrag import executeDrag
from executeDouble import executeDouble
from executePixelClick import executePixelClick
from executePixelClick import executeRelativeClick
from executeCalculatedField import executeCalculatedField
from executeTitleChange import executeTitleChange
from navigateSheets import navigateSheets
from executeClickAndType import executeClickAndType
from executeDoubleClick import executeDoubleClick
from executeListClick import executeListClick
from findPixel import findPixel
from findPixel import findRelative
from executeExpandedClick import executeExpandedClick

from testAbstract import (
    findMarkSubOption, DragToX, DragToY, DragToColor, DragToSize, DragToLabel,
    DragToDetail, dimensionsFilterByFormula, createCalculatedField, newSheet,
    sortAscending, sortDescending, swapXandY, changeTitle, filterByTopDimension,
    dualAxis, changeAxisMeasure, showTrendLine, changeAxisMeasureToDiscrete,
    changeAxisDiscreteMeasureToContinious, changeDateType, switchGraph,
    changeAggregation, createBarChart, createScatterChart, createLineChart,
    navigateSheetsForwards, navigateSheetsBackwards
)

openai.api_key = "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"
MODEL_NAME = "o1-mini-2024-09-12"

def load_dataset_summary():
    dataset_path = os.path.join("dataHandling", "data_summary.xlsx")
    if os.path.exists(dataset_path):
        try:
            df = pd.read_excel(dataset_path)  # or pd.read_csv(dataset_path)
            print(f"Loaded dataset with shape: {df.shape}")
            return df.head().to_json(orient="split")
        except Exception as e:
            print(f"Warning: Could not load dataset: {e}")
            return ""
    else:
        print("Warning: Dataset file not found, continuing without data.")
        return ""

def main():
    # 1. Ask user for the initial prompt/instructions.
    initial_user_prompt = input("Please enter your prompt or instructions for ChatGPT:\n> ")

    # 2. (Optional) Load a local dataset and get a data summary.
    data_summary = load_dataset_summary()

    # 3. Build the function usage text to include in the system prompt.
    function_usage_text = """
Here are the usage details for each available function: MAKE SURE YOU GET THE VARIABLES EXACTLY RIGHT AND SHOULD BE EAXTLY WRITTEN EXACTLY AS SHONW
IN THE DATA SUMMARY

DragToX(variable_name)
- Usage: Drags a given variable (dimension or measure) to the X (columns) shelf.
- Key Inputs: variable_name

DragToY(variable_name)
- Usage: Drags a given variable (dimension or measure) to the Y (rows) shelf.
- Key Inputs: variable_name

DragToColor(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Color mark. 
- Key Inputs: variable_name, index (0 for "All" if there is 2 or more measures per axis or the index number of the variable you want to actually mark specifically
and if there is not 2 measures in any one axis use -1 as All doesn't show unless you have two or more measures in one of the axes), axis_name (if index>0)

DragToSize(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Size mark.
- Key Inputs: variable_name, index, axis_name

DragToLabel(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Label mark.
- Key Inputs: variable_name, index, axis_name

DragToDetail(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Detail mark.
- Key Inputs: variable_name, index, axis_name

dimensionsFilterByFormula(var_to_filter, formula)
- Usage: Applies a formula-based condition filter on a dimension and should be for tableau.
- Key Inputs: var_to_filter, formula

createCalculatedField(field_name, field_formula)
- Usage: Creates a new calculated field in Tableau.
- Key Inputs: field_name, field_formula

newSheet()
- Usage: Opens a fresh sheet.

sortAscending(), sortDescending()
- Usage: Sorts the current chart ascending or descending.

swapXandY()
- Usage: Swaps the X and Y shelves.

changeTitle(new_title)
- Usage: Edits the title of the current sheet.
- Key Inputs: new_title

filterByTopDimension(variable_name, direction, count, formula)
- Usage: Applies a Top or Bottom filter to a dimension.
- Key Inputs: variable_name, direction ("Top"/"Bottom"), count, formula
 - fomrula should be properly formatting and if its a variable it should be like [variable]

dualAxis(axis_name, index)
- Usage: Creates a dual axis by combining the measure at a given index with another measure on the same axis.
- Key Inputs: axis_name ("xAxis" or "yAxis"), index (1-based measure index)

changeAxisMeasure(axis_name, index, measure_type)
- Usage: Changes the aggregation of a measure (SUM, AVERAGE, etc.)
- Key Inputs: axis_name, index, measure_type

showTrendLine()
- Usage: Turns on a trend line in the current chart.

changeAxisMeasureToDiscrete(axis_name, index)
- Usage: Converts a measure on an axis to discrete or continuous.

changeAxisDiscreteMeasureToContinious(axis_name, index)
- Usage: Converts a discrete dimension on an axis to continuous.

changeDateType(axis_name, index, date_function, date_component)
- Usage: Changes a date field's grouping (DATEPART or DATETRUNC).
- Key Inputs: axis_name, index, date_function, date_component

switchGraph(graph_type)
- Usage: Changes the chart type using the Show Me menu.
- Key Inputs: graph_type (string or 1-24)

changeAggregation()
- Usage: Opens Analysis pane to toggle data aggregation.

Try to use these create functions before adding marks, Color, Label, Detail, but do it after filter and calculated field are called

createBarChart(x_vars, y_vars)
- Usage: Builds a horizontal bar chart with lists of x-vars and y-vars.

createScatterChart(x_vars, y_vars)
- Usage: Builds a scatter plot with x-vars and y-vars.

createLineChart(x_vars, y_vars, date_function="DATETRUNC", date_component="month")
- Usage: Builds a line chart with a time-based X var, measure Y var, plus optional date truncation.

Navigation Functions:
navigateSheetsForwards(quantity)
- Usage: Navigates forwards (Ctrl+Tab) 'quantity' times.
navigateSheetsBackwards(quantity)
- Usage: Navigates backwards (Ctrl+Shift+Tab) 'quantity' times.
"""

    # 4. Create the base system prompt.
    base_system_prompt = (
        "You are a specialized code generator for creating Tableau automation scripts. "
        "Below are the function definitions and their usage details, which you can call. "
        "You will be given a user prompt about building a good set of charts or code for data. "
        "Your job is to ONLY return JSON with the 'python_code' field containing the code, "
        "with no additional text or commentary. No other keys or text. "
        "Just the JSON object like:\n\n"
        "{\n  \"python_code\": \"THE CODE HERE...\"\n}\n\n"
        "So the user can copy and run it. MAKE SURE THERE IS NO JSON AT THE BEGINNING AND YOU DON'T RETURN THE WORD json before the JSON, "
        "no other discussion or commentary.\n\n"
        + function_usage_text
        + "Here is the needed information for the data and the data summary: " + data_summary
    )

    # Inform ChatGPT of the initial state if any code has already been executed.
    previous_code = ""
    if os.path.exists("generated_code.py"):
        with open("generated_code.py", "r", encoding="utf-8") as f:
            previous_code = f.read()
    if previous_code:
        base_system_prompt += "\n\nCurrent cumulative code state (already executed):\n" + previous_code

    # 5. Combine base system prompt with the initial user prompt.
    full_initial_prompt = f"{base_system_prompt}\n\nUser instructions:\n{initial_user_prompt}"

    # Send the initial prompt to ChatGPT
    print("Sending initial prompt to ChatGPT. Please wait...")
    response = openai.chat.completions.create(
         model=MODEL_NAME,
         messages=[
             {"role": "user", "content": full_initial_prompt}
         ],
         stream=False
    )
    assistant_msg = response.choices[0].message.content
    assistant_msg = re.sub(r"^```(?:json)?\s*", "", assistant_msg.strip())
    assistant_msg = re.sub(r"\s*```$", "", assistant_msg)
    tokens = response.usage

    print("Raw response from ChatGPT:\n", assistant_msg)
    print("TOKENS : ", tokens)

    try:
        response_json = json.loads(assistant_msg)
        python_code = response_json.get("python_code", None)
        if python_code:
            print("\n--- Extracted Python Code from ChatGPT (Initial) ---\n")
            print(python_code)
            # Save code to file
            output_file = "generated_code.py"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(python_code)
            print(f"\nPython code saved to {output_file}")
            # Execute the code (caution!)
            exec(python_code, globals())
        else:
            print("Did not find 'python_code' in the JSON response.")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Here is the raw output if you need to diagnose:\n", assistant_msg)

    # 6. Enter a continuous loop to accept new user instructions.
    while True:
        new_instruction = input("\nEnter your next instruction (or type 'quit' to exit):\n> ").strip()
        if new_instruction.lower() in ["quit", "exit"]:
            print("Exiting session.")
            break

        # Append the current cumulative code state to the system prompt.
        previous_code = ""
        if os.path.exists("generated_code.py"):
            with open("generated_code.py", "r", encoding="utf-8") as f:
                previous_code = f.read()
        current_system_prompt = base_system_prompt
        if previous_code:
            current_system_prompt += "\n\nCurrent cumulative code state (already executed):\n" + previous_code

        # Combine system prompt with the new user instruction.
        full_prompt = f"{current_system_prompt}\n\nUser instructions:\n{new_instruction}"

        print("Sending prompt to ChatGPT. Please wait...")
        response = openai.chat.completions.create(
             model=MODEL_NAME,
             messages=[
                 {"role": "user", "content": full_prompt}
             ],
             stream=False
        )
        assistant_msg = response.choices[0].message.content
        assistant_msg = re.sub(r"^```(?:json)?\s*", "", assistant_msg.strip())
        assistant_msg = re.sub(r"\s*```$", "", assistant_msg)
        tokens = response.usage

        print("Raw response from ChatGPT:\n", assistant_msg)
        print("TOKENS : ", tokens)

        try:
            response_json = json.loads(assistant_msg)
            python_code = response_json.get("python_code", None)
            if python_code:
                print("\n--- Extracted Python Code from ChatGPT ---\n")
                print(python_code)
                # Save the new cumulative code to file (overwriting previous code)
                output_file = "generated_code.py"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(python_code)
                print(f"\nPython code saved to {output_file}")
                # Execute the new code (caution!)
                exec(python_code, globals())
            else:
                print("Did not find 'python_code' in the JSON response.")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print("Here is the raw output if you need to diagnose:\n", assistant_msg)


if __name__ == "__main__":
    main()
