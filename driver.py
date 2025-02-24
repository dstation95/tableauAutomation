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
    changeAggregation, createBarChart, createScatterChart, createLineChart
)

# --------------------------------------------------------------------------
# chatgpt_integration.py
#
# A script that:
#   1. Prompts the user for instructions to ChatGPT.
#   2. Loads a local dataset (optional).
#   3. Sends the system prompt + user prompt to ChatGPT.
#   4. Expects ChatGPT to return ONLY JSON with a "python_code" field.
#   5. Prints and optionally saves that code.
#
# Adjust as needed for your environment.
# --------------------------------------------------------------------------

openai.api_key = "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"
MODEL_NAME = "o1-mini-2024-09-12"

def main():
    # 1. Ask user for a prompt
    user_prompt = input("Please enter your prompt or instructions for ChatGPT:\n> ")

    # 2. (Optional) Load a local dataset
    dataset_path = os.path.join("dataHandling", "data_summary.xlsx")  # or a CSV
    if os.path.exists(dataset_path):
        try:
            df = pd.read_excel(dataset_path)  # or pd.read_csv(dataset_path)
            print(f"Loaded dataset with shape: {df.shape}")
            data_summary = df.head().to_json(orient="split")
        except Exception as e:
            print(f"Warning: Could not load dataset: {e}")
    else:
        print("Warning: Dataset file not found, continuing without data.")

    # 3. Build the function usage text to include in the system prompt:
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
- Key Inputs: variable_name, index (0 for "All" if there is 2 or more measures per axis or the index numebr of the vairable you want to actually mark specifcally
and if there is not 2 measures in any one axis use -1 as ALl doesnt show unless you have two or more measures in one fo the axis), axis_name (if index>0)

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
- Usage: Applies a formula-based condition filter on a dimension.
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


Try to use these create functions before adding marks, Color, Label, Detail, but do it after filter and calculated feild are called

createBarChart(x_vars, y_vars)
- Usage: Builds a horizontal bar chart with lists of x-vars and y-vars.

createScatterChart(x_vars, y_vars)
- Usage: Builds a scatter plot with x-vars and y-vars.

createLineChart(x_vars, y_vars, date_function="DATETRUNC", date_component="month")
- Usage: Builds a line chart with a time-based X var, measure Y var, plus optional date truncation.
"""

    # 4. Create the system prompt
    system_prompt = (
        "You are a specialized code generator for creating Tableau automation scripts. "
        "Below are the function definitions and their usage details, which you can call. "
        "You will be given a user prompt about building a good set of charts or code for data. "
        "Your job is to ONLY return JSON with the 'python_code' field containing the code, "
        "with no additional text or commentary. No other keys or text. "
        "Just the JSON object like:\n\n"
        '{\n  "python_code": "THE CODE HERE..."\n}\n\n'
        "So the user can copy and run it.MAKE SURE THERE IS NO JSON IN THE BEGGINGIN ADN YOU DONT return THE WROD json before the json, No other discussion or commentary.\n\n"
        + function_usage_text
        + "Here is the needed information for the data and the data summary" + 
        data_summary
    )

    # 5. Combine system prompt with user prompt
    full_prompt = f"{system_prompt}\n\nUser instructions:\n{user_prompt}"

    # 6. Send to ChatGPT
    print("Sending prompt to ChatGPT. Please wait...")
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": user_prompt}
    #     ]
    # )

    # # 7. Extract the response text
    # assistant_msg = response["choices"][0]["message"]["content"]

    # response = openai.chat.completions.create(
    #      model=MODEL_NAME,
    #      messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": user_prompt}
    #      ],
    #      stream=False
    # )
    user_prompt = system_prompt + user_prompt
    response = openai.chat.completions.create(
         model=MODEL_NAME,
         messages=[
        #     {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
         ],
         stream=False
    )
    assistant_msg = response.choices[0].message.content
    assistant_msg = re.sub(r"^```(?:json)?\s*", "", assistant_msg.strip())
    assistant_msg = re.sub(r"\s*```$", "", assistant_msg)

    print("Raw response from ChatGPT:\n", assistant_msg)

    try:
        response_json = json.loads(assistant_msg)
        python_code = response_json.get("python_code", None)
        if python_code:
            print("\n--- Extracted Python Code from ChatGPT ---\n")
            print(python_code)
            # Save code to file (optional)
            output_file = "generated_code.py"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(python_code)
            print(f"\nPython code saved to {output_file}")
        else:
            print("Did not find 'python_code' in the JSON response.")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Here is the raw output if you need to diagnose:\n", assistant_msg)

    # 8. Parse JSON to get python_code
    try:
        response_json = json.loads(assistant_msg)
        python_code = response_json.get("python_code", None)
        if python_code:
            print("\n--- Extracted Python Code from ChatGPT ---\n")
            print(python_code)

            # 9. (Optional) Save code to file
            output_file = "generated_code.py"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(python_code)
            print(f"\nPython code saved to {output_file}")

            # 10. (Optional) Execute the code (caution!)
            exec(python_code, globals())
        else:
            print("Did not find 'python_code' in the JSON response.")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:\n", assistant_msg)


if __name__ == "__main__":
    main()
