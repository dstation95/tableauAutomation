#!/usr/bin/env python3
import os
import re
import json
import logging
import subprocess
import openai
import pandas as pd
from scipy import stats
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

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
    navigateSheetsForwards, navigateSheetsBackwards, fullScreen, 
    changeMarkType, createAreaChart

)

# -------------------------------
# Configuration & Setup
# -------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set your OpenAI API key and model (adjust as needed)
openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = "o1-mini-2024-09-12"

# Global variable to hold the current state of the Tableau screen.
# STATE_FILE = os.path.join(UPLOAD_FOLDER, "current_state.json")
# if os.path.exists(STATE_FILE):
#     with open(STATE_FILE, "r", encoding="utf-8") as f:
#         CURRENT_STATE = f.read().strip()
# else:
#     CURRENT_STATE = ""  # start with an empty state

STATE_PATH = os.path.join(UPLOAD_FOLDER, "current_state.json")

def load_current_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading current state: {e}")
            return ""
    return ""

def save_current_state(state_str):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            f.write(state_str)
    except Exception as e:
        logger.error(f"Error saving current state: {e}")

CURRENT_STATE = load_current_state()
print(CURRENT_STATE)

# -------------------------------
# File and Message Handlers
# -------------------------------
class FileHandler:
    def __init__(self, upload_folder=UPLOAD_FOLDER):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        self._test_write_permissions()

    def _test_write_permissions(self):
        test_file_path = os.path.join(self.upload_folder, "test_permission.txt")
        try:
            with open(test_file_path, 'w') as f:
                f.write("Permission test file")
            os.remove(test_file_path)
            logger.info("Write permissions are fine in uploads folder.")
        except Exception as e:
            logger.error(f"Write permission error: {str(e)}", exc_info=True)

    def process_uploaded_file(self, filename):
        try:
            original_file_path = os.path.join(self.upload_folder, filename)
            summary_file_name = f"summary_of_{filename}.txt"
            summary_path = os.path.join(self.upload_folder, summary_file_name)
            logger.debug(f"Processing file: {filename}")

            if not os.path.exists(original_file_path):
                logger.error(f"File not found: {original_file_path}")
                return False

            file_size = os.path.getsize(original_file_path)
            with open(summary_path, 'w') as f:
                f.write("File Analysis Summary\n")
                f.write("===================\n")
                f.write(f"Original filename: {filename}\n")
                f.write(f"File size: {file_size} bytes\n")
                f.write("Status: Processing Complete\n")

            logger.info(f"Created summary file: {summary_path}")
            return True
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            return False

    def create_task_file(self, task_prompt):
        try:
            if not task_prompt or not isinstance(task_prompt, str):
                logger.error("Task prompt is empty or invalid")
                return False

            task_file_name = f"{task_prompt}-has been received.txt"
            task_file_path = os.path.join(self.upload_folder, task_file_name)
            logger.debug(f"Creating task file: {task_file_path}")

            with open(task_file_path, 'w') as f:
                f.write(f"Task: {task_prompt}\n")
                f.write("Status: Task has been received and processed")

            logger.info(f"Created task file: {task_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating task file: {str(e)}", exc_info=True)
            return False

class MessageHandler:
    def __init__(self, upload_folder=UPLOAD_FOLDER):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        self._test_write_permissions()

    def _test_write_permissions(self):
        test_file_path = os.path.join(self.upload_folder, "test_permission.txt")
        try:
            with open(test_file_path, 'w') as f:
                f.write("Permission test file")
            os.remove(test_file_path)
            logger.info("Write permissions are fine in uploads folder.")
        except Exception as e:
            logger.error(f"Write permission error: {str(e)}", exc_info=True)

    def create_message_file(self, message):
        try:
            if not message or not isinstance(message, str):
                logger.error("Message is empty or invalid")
                return False

            file_name = f"{message.replace(' ', '_')}-has_been_received.txt"
            file_path = os.path.join(self.upload_folder, file_name)
            logger.debug(f"Creating message file: {file_path}")

            with open(file_path, 'w') as f:
                f.write(f"Message: {message}\n")
                f.write("Status: Message has been received and processed")

            logger.info(f"Created message file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating message file: {str(e)}", exc_info=True)
            return False

# -------------------------------
# Data Handling Function
# -------------------------------
def run_data_handling(input_file):
    """
    Reads a CSV, creates a basic schema summary (saved as Excel),
    writes a new CSV for Tableau, and launches Tableau if available.
    Returns a simple string summary of the data.
    """
    try:
        if not input_file.lower().endswith(".csv"):
            logger.error("The input file must be a .csv file.")
            return ""
        df = pd.read_csv(input_file)

        # Create a basic schema summary
        schema_info = []
        for col in df.columns:
            dtype = df[col].dtype
            role = "Measure" if pd.api.types.is_numeric_dtype(df[col]) else "Dimension"
            schema_info.append({
                "Column": col,
                "Data Type": str(dtype),
                "Role": role,
                "Unique Values": int(df[col].nunique()),
                "Missing Values": int(df[col].isnull().sum()),
                "Sample Values": df[col].dropna().unique()[:5].tolist()
            })
        schema_df = pd.DataFrame(schema_info)
        summary_excel = os.path.join(UPLOAD_FOLDER, "data_summary.xlsx")
        schema_df.to_excel(summary_excel, index=False)
        logger.info(f"Basic schema summary saved to {summary_excel}")

        # Create a new CSV file for Tableau
        output_csv = os.path.join(UPLOAD_FOLDER, "Book3.csv")
        df.to_csv(output_csv, index=False)
        logger.info(f"New CSV file created: {output_csv}")

        # Launch Tableau Public if available
        TABLEAU_PATH = r"C:\Program Files\Tableau\Tableau Public 2024.3\bin\tabpublic.exe"
        csv_full_path = os.path.abspath(output_csv)
        if os.path.exists(TABLEAU_PATH):
            subprocess.Popen([TABLEAU_PATH, csv_full_path])
            logger.info("Tableau launched successfully.")
        else:
            logger.warning(f"Tableau executable not found at {TABLEAU_PATH}.")

        return f"Processed CSV with {df.shape[0]} rows and {df.shape[1]} columns."
    except Exception as e:
        logger.error(f"Data handling error: {str(e)}", exc_info=True)
        return ""

# -------------------------------
# Helper functions for UI Snapshot and State Management
# -------------------------------

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

def dump_ui_tree(elem_info):
    tree = {
        "composite": generate_composite_id(elem_info),
        "children": []
    }
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

def captureFullSnapshot():
    from connectScreen import connect_to_tableau
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

def extract_geometry_from_composite(composite):
    try:
        parts = composite.split("|")
        if len(parts) < 6:
            return None
        control_type, class_name, automation_id, name, rect_str, _ = parts
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

# -------------------------------
# State Management: load and save current state
# -------------------------------
# STATE_PATH = os.path.join(UPLOAD_FOLDER, "current_state.json")

# def load_current_state():
#     if os.path.exists(STATE_PATH):
#         with open(STATE_PATH, "r", encoding="utf-8") as f:
#             try:
#                 return f.read().strip()
#             except Exception as e:
#                 print("Error reading current state:", e)
#                 return ""
#     return ""

# def save_current_state(state_str):
#     with open(STATE_PATH, "w", encoding="utf-8") as f:
#         f.write(state_str)

# # Initialize current state
# CURRENT_STATE = load_current_state()

# -------------------------------
# Driver Function (ChatGPT Interaction)
# -------------------------------
def run_driver(prompt, data_summary, previous_code="", current_state=""):
    """
    Combines a base system prompt, the provided data summary, user instructions,
    previous executed code, and the current state of the Tableau workbench.
    Calls OpenAI to generate JSON (with a python_code field and a new state field),
    saves and executes the generated code, and updates the current state.
    """
    # If no current_state is provided, use the global CURRENT_STATE.
    global CURRENT_STATE
    if not current_state:
        current_state = CURRENT_STATE
    function_usage_text = """
Here are the usage details for each available function: MAKE SURE YOU GET THE VARIABLES EXACTLY RIGHT AND SHOULD BE EAXTLY WRITTEN EXACTLY AS SHONW
IN THE DATA SUMMARY

DragToX(variable_name)
- Usage: Drags a given variable (dimension or measure) to the X (columns) shelf.
- Key Inputs: variable_name
**State Update**: Append or set the specified variable in the current sheet’s "x_axis" array.

DragToY(variable_name)
- Usage: Drags a given variable (dimension or measure) to the Y (rows) shelf.
- Key Inputs: variable_name
- **State Update**: Append or set the specified variable in the current sheet’s "y_axis" array.

DragToColor(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Color mark. This colors the measure values (bars, etc.) based on the dragged variable.
- Key Inputs: variable_name, index, (axis_name if provided)
- **State Update**: In the current sheet’s "marks" entry, update the corresponding mark option (e.g., "All" if index is -1, or the appropriate tab if index is specified) by adding or updating an entry for the variable with role "color".

DragToSize(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Size mark, scaling the mark size by the measure.
- Key Inputs: variable_name, index, axis_name
- **State Update**: In the current sheet’s "marks" entry, update the mark option for size by adding or updating the variable with role "size".

DragToLabel(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Label mark, enabling labeling of graph measure values.
- Key Inputs: variable_name, index, axis_name
- **State Update**: In the current sheet’s "marks" entry, add or update the variable with role "label".

DragToDetail(variable_name, index, axis_name=None)
- Usage: Drags a variable to the Detail mark.
- Key Inputs: variable_name, index, axis_name
- **State Update**: In the current sheet’s "marks" entry, add or update the variable with role "detail".


 add color (DragToColor) or labels (DragToLabel) when it provides additional clarity (e.g., highlighting categories or numeric values).

 

for dragging  use the appropriate index argument if multiple measures exist on the same axis.

dimensionsFilterByFormula(var_to_filter, formula)
- Usage: Applies a formula-based condition filter on a dimension and should be for tableau.
- Key Inputs: var_to_filter, formula
**State Update**: Append an entry to the current sheet’s "filters" array with the variable name and filter type (e.g., "custom" with formula).

createCalculatedField(field_name, field_formula)
- Usage: Creates a new calculated field in Tableau. And make sures its properly formatted for tableau.
- Key Inputs: field_name, field_formula
Use createCalculatedField to combine or transform data where needed. If measuring performance over time or summing multiple delay factors, use an appropriate formula.
- **State Update**: (Usually no direct state update required, but may be referenced in other areas with the variable name be the one created here.)

newSheet()
- Usage: Opens a fresh sheet.
- **State Update**: Add a new sheet object to the "sheets" array in the state and update "current_sheet" to the new sheet’s name.

sortAscending(), sortDescending()
- Usage: Sorts the current chart ascending or descending.

swapXandY()
- Usage: Swaps the X and Y shelves.
- **State Update**: Swap the contents of the "x_axis" and "y_axis" arrays in the current sheet.

changeTitle(new_title)
- Usage: Edits the title of the current sheet.
- Key Inputs: new_title
THIS IS NOT THE SHEET NAME, do not chang ethe sheet name of the sate with this fucntions

filterByTopDimension(variable_name, direction, count, formula)
- Usage: Applies a Top or Bottom filter to a dimension.
- Key Inputs: variable_name, direction ("Top"/"Bottom"), count, formula
 - fomrula should be properly formatting and if its a variable it should be like [variable]
  If there's a large amount of data, filter it (e.g., filterByTopDimension or dimensionsFilterByFormula) to focus on key elements. Then sort (sortAscending / sortDescending) to make patterns more obvious.
  Filtering should make sense based on the data summary and data
  make sure it is an aggregate measure, like SUM([Variable])
  - **State Update**: Append or update the current sheet’s "filters" array with the specified filter details.


dualAxis(axis_name, index)
- Usage: Creates a dual axis by combining the measure at a given index with another measure on the same axis.
- Key Inputs: axis_name ("xAxis" or "yAxis"), index (1-based measure index)
dualAxis can combine multiple measures in one chart when it enhances the story.
make sure you call dual axis when there are at least 2 measures on the axis and call it on the second one
- **State Update**: Mark in the current sheet’s state that the specified axis now has dual measures.

changeAxisMeasure(axis_name, index, measure_type)
- Usage: Changes the aggregation of a measure (SUM, AVERAGE, etc.)
- Key Inputs: axis_name, index, measure_type

showTrendLine()
- Usage: Turns on a trend line in the current chart.
showTrendLine can reveal underlying patterns in line/scatter plots.
- **State Update**: Set the "trendline" key to true in the current sheet’s "extras" object.

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
Dont use this try to use changemark type to change graph type

changeAggregation()
- Usage: Opens Analysis pane to toggle data aggregation.

Try to use these create functions before adding marks, Color, Label, Detail, but do it after filter and calculated field are called
You do not have to drag the variables ot the axis with the create functions, they already do them and do the show when needed and use them on
a new sheet

createBarChart(x_vars, y_vars)
- Usage: Builds a horizontal bar chart with lists of x-vars and y-vars. 
- **State Update**: Create a new sheet object in the state with "x_axis" and "y_axis" set to the provided variables and mark type is Bar

createScatterChart(x_vars, y_vars)
- Usage: Builds a scatter plot with x-vars and y-vars.
- **State Update**: Create a new sheet object in the state with "x_axis" and "y_axis" set to the provided variables and the mark type is circle and should have a measure in each axis

createLineChart(x_vars, y_vars, date_function="DATETRUNC", date_component="month")
- Usage: Builds a line chart with a time-based X var, measure Y var, plus optional date truncation that would change the data appropriatly.
- **State Update**: Create a new sheet object and adds the varibels in axis and should be mark type of line for All

For instance, bar charts for discrete comparisons, scatter plots for correlations, line charts for trends, etc.
and you can figure this out based on the variables properities in the datasummary

    "The following function is used to change the mark type for a given mark option:\n\n"
    "changeMarkType(mark_type, mark_index=-1, axis_name='xAxis')\n"
    "  - mark_type (str): The desired mark type. For example: \"Bar\", \"Line\", \"area\", \"Square\", \"Circle\", "
    "\"Shape\", \"text\", \"Map\", \"Pie\", \"Gantt Bar\", \"Polygon\", \"Density\".\n"
    "  - mark_index (int, optional): If there are multiple measures that require distinct mark type changes, and the axis"
    "this index selects the specific instance. If mark_index is -1, it applies a general change (no more than 2 measures per axis). "
    "If mark_index is 0, it means an axis has 2 or more measures and you want to change the mark type for ALL the measures. "
    "If mark_index is any positive number, it indicates you want to change the mark type for one specific measure of an axis "
    "that first had 2 or more measures. The axis_name parameter specifies the axis of interest (e.g., the first axis that had 2 or more measures and should be xAxis or yAxis).\n\n"
    "When used, changeMarkType should update the state for the corresponding sheet by modifying its 'marks' entry with the new mark type for the given mark option.\n\n"
    Use this over changeSheets

fullScreen()
- Only use this in the begginign when explicitly states to do so

Navigation Functions:
navigateSheetsForwards(quantity)
- Usage: Navigates forwards (Ctrl+Tab) 'quantity' times.
navigateSheetsBackwards(quantity)
- Usage: Navigates backwards (Ctrl+Shift+Tab) 'quantity' times.


One of the question that may be givesn to you would be "Hey can you compare the different category sales for the stores, you should create 2 graphs one with a bar graph with both subcateg

If the prompt is askign us make a graph comparing discount sales and profit, what i want you to do is create a scatter plot with Sales and profit adn then add in discount to the color fo the graph.

One of the prompts is goign to be 

Can you compare the different categories sales for the store and our total profit through the years?

For this one I want you to create an area graph over time base don order date, in monrths and then have the other axis be the total sales and then splti it by colorbase don 
category. In addition you shoul dmake antoerh graph that would be profit ratio, whci hsia  calcutked field of sum of profit over the sum fo sales and then put thi sone a graph over tiem adn then color 
it by profiut ratio to see the dips in the profit. Make sure if they ask for this spieicf cresponse you make this graph adn name it appropartly.

Another prompt would be 
Also I want to see how discounting is effecting our margins

And this should create a scatter plot of Sales and Profit and then add in discount to color code it.

IN addition, it may ask you to change the color scheme from the profit ratio to the discount and you shoudl go back to tthe graph using profit ratio and just drag 
discoutn into the color box on that screen.

In addition make sure the index is not 0 for the  axis index to click, should be 1 for the axis click to change measure type

when it says can you show how the sales per category has changed over time

Can you amke it an area graph?

When it says can you compare our profit and sales in the store and how it has changed, can you make a custom calcaultion for profit ratio and then show it over time and color it based on total profit.
"""
    base_system_prompt = (
        "You are a specialized code generator for generating Tableau automation scripts. "
        "Your goal is to produce code that produces visually appealing, meaningful, and well-structured Tableau charts based on user instructions. "
        "The code must use the provided automation functions exactly as specified.\n\n"
        "Keep the following in mind:\n"
        "1. Use chart types and shelf placements (X, Y, Color, Label, etc.) that highlight data effectively.\n"
        "2. If relevant, apply sorting or filters (like top N) to focus on key insights.\n"
        "3. When dealing with date/time data, consider using date functions to create clear timelines and ensure that the date formatting is correct based on the data.\n"
        "4. Choose appropriate color schemes, detail levels, and mark types (like bars, lines, or points) to avoid clutter and make graphs look better.\n"
        "5. Use calculations (createCalculatedField) or trend lines (showTrendLine) as needed to add deeper insights relevant to the data.\n"
        "Exact Syntax: Use the functions verbatim as listed. Ensure you supply them with correct arguments (variable names, indices, etc.) based on the data summary.\n\n"
        "Below are the function definitions and usage details you can call. "
        "You will be given a user prompt about building charts or code for data. "
        "Your job is to ONLY return JSON with two fields: \n"
        "  \"python_code\": the code to be executed, and \n"
        "  \"state\": the updated current state of the Tableau workbench as a JSON string.\n\n"
        "The 'state' must be a JSON object with the following structure:\n\n"
        "  {\n"
        "    \"current_sheet\": \"SheetName\",  // The sheet that is currently active\n"
        "    \"sheets\": [\n"
        "      {\n"
        "        \"sheet_name\": \"Sheet1\",\n"
        "        \"x_axis\": [\"VarA\", \"VarB\"],\n"
        "        \"y_axis\": [\"VarC\"],\n"
        "        \"marks\": {\n"
        "          \"All\": {\n"
        "            \"mark_type\": \"Bar\",\n"
        "            \"variables\": [\n"
        "              {\"name\": \"VarColor\", \"role\": \"color\"},\n"
        "              {\"name\": \"VarLabel\", \"role\": \"label\"}\n"
        "            ]\n"
        "          },\n"
        "          \"MeasureValues\": {\n"
        "            \"mark_type\": \"Circle\",\n"
        "            \"variables\": [\n"
        "              {\"name\": \"Sale\", \"role\": \"size\"}\n"
        "            ]\n"
        "          }\n"
        "        },\n"
        "        \"filters\": [\n"
        "          {\"variable_name\": \"Profit\", \"type\": \"filterByTopDimension\", \"params\": {\"count\": 10, \"formula\": \"SUM([Profit])\"}}\n"
        "        ],\n"
        "        \"extras\": {\n"
        "          \"trendline\": true,\n"
        "          \"forecast\": false\n"
        "        }\n"
        "      }\n"
        "      // ... additional sheets as needed\n"
        "    ]\n"
        "  }\n\n"
        "Note: The state may be dynamic. For example, a sheet might have only an 'All' mark option if only one set of variables is used, "
        "or it might include additional mark tabs if there is an axis with 2 or more measures (in which case the first axis with 2 measures would be where the measures are taken). this ouwld add another object under Marks in addition to ALL with the variable names"
        "The 'extras' object should only include keys (such as trendline, forecast) if they are active.\n\n"
        "When responding, return only the JSON object with the two keys, and do not include any extra commentary. "
        "Also, include in the state a key 'current_sheet' that specifies which sheet is currently active.\n\n"
        "Current state of the Tableau workbench (as JSON):\n"
        f"{current_state}\n\n"
        + function_usage_text +
        "Here is the needed information for the data and the data summary: "
        + data_summary
    )

    logger.info("DATA SUMMARY " + json.dumps(data_summary))
    if previous_code:
        base_system_prompt += "\n\nCurrent cumulative code state (already executed):\n" + previous_code

    full_prompt = f"{base_system_prompt}\n\nUser instructions:\n{prompt}"
    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": full_prompt}],
            stream=False
        )
        assistant_msg = response.choices[0].message.content.strip()
        # Remove code block markers if present
        assistant_msg = re.sub(r"^```(?:json)?\s*", "", assistant_msg)
        assistant_msg = re.sub(r"\s*```$", "", assistant_msg)
        response_json = json.loads(assistant_msg)
        python_code = response_json.get("python_code", None)
        new_state = response_json.get("state", current_state)  # if no new state, keep current_state
        if python_code:
            with open("generated_code.py", "a", encoding="utf-8") as f:
                f.write(python_code)
            save_current_state(new_state)
            # global CURRENT_STATE
            CURRENT_STATE = new_state
            exec(python_code, globals())
            # Update global state

            return "Driver executed the generated code successfully."
        else:
            return "No 'python_code' field found in the response."
    except Exception as e:
        logger.error(f"Driver error: {str(e)}", exc_info=True)
        return f"Driver encountered an error: {str(e)}"


     # -------------------------------
# Flask Endpoints
# -------------------------------
@app.route('/receive-file', methods=['POST'])
def receive_file():
    """
    Accepts a file upload, processes it, runs data handling (if CSV),
    and then triggers the initial driver run.
    """
    print(request)
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file received'}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    logger.info(f"Received file: {file.filename}, saved to {file_path}")

    file_handler = FileHandler(UPLOAD_FOLDER)
    if not file_handler.process_uploaded_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Error processing file'}), 500

    data_summary = ""
    if file.filename.lower().endswith(".csv"):
        data_summary = run_data_handling(file_path)

    initial_prompt = "just create a new sheet and then call the fullscreen function"

    time.sleep(30)
    driver_result = run_driver(initial_prompt, data_summary)
    time.sleep(7)
    return jsonify({
        'status': 'success',
        'message': f'File {file.filename} received and processed.',
        'driver_result': driver_result
    })

@app.route('/submit-task', methods=['POST'])
def submit_task():
    """
    Receives a task prompt, creates a task file,
    and then triggers the driver to generate and execute new code.
    """
    data = request.get_json()
    if not data or 'task_prompt' not in data:
        logger.error("No task prompt provided")
        return jsonify({"error": "No task prompt provided"}), 400

    task_prompt = data['task_prompt']
    file_handler = FileHandler(UPLOAD_FOLDER)
    if not file_handler.create_task_file(task_prompt):
        return jsonify({'status': 'error', 'message': 'Failed to create task file'}), 500

    previous_code = ""
    if os.path.exists("generated_code.py"):
        with open("generated_code.py", "r", encoding="utf-8") as f:
            previous_code = f.read()

    data_summary = ""
    data_summary_file = os.path.join(UPLOAD_FOLDER, "data_summary.xlsx")
    if os.path.exists(data_summary_file):
        try:
            df_summary = pd.read_excel(data_summary_file)
            data_summary = df_summary.to_json(orient="split")
        except Exception as e:
            logger.error("Error reading uploaded file: " + str(e))
            data_summary = ""

    driver_result = run_driver(task_prompt, data_summary, previous_code, CURRENT_STATE)
    return jsonify({'status': 'success', 'driver_result': driver_result})

@app.route('/task_completed', methods=['POST'])
def task_completed():
    """
    Endpoint for receiving notifications from the driver when a task is completed.
    """
    data = request.get_json()
    logger.info("Task completed notification received: " + json.dumps(data))
    return jsonify({'status': 'success', 'message': 'Task completion acknowledged'})

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

def clean_uploads_and_generated_code():
    gen_code_path = "generated_code.py"
    if os.path.exists(gen_code_path):
        os.remove(gen_code_path)
    for f in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
    logger.info("Cleaned generated_code.py and all files in the uploads folder.")

@app.route('/clean', methods=['POST'])
def clean_route():
    clean_uploads_and_generated_code()
    return jsonify({"status": "success", "message": "Cleaned generated code and uploads folder."})

# -------------------------------
# Main
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
