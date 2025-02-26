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

import pyautogui
import time




#helper
def findMarkSubOption(mark_index, suboption_index, axis_name=None):
    """
    Helper function to locate and return the pixel coordinate for a mark suboption.
    
    Parameters:
      mark_index (int): The index representing the marks tab category.
                        0 indicates the "All" section; any non-zero value represents a specific category.
      suboption_index (int): The index of the suboption within the selected marks category.
    
    Returns:
      tuple: (x, y) coordinates of the found suboption.
    
    Logic:
      - If mark_index is 0, the "All" marks tab is used.
      - Otherwise, the base coordinate is taken from a specific category (e.g., via the xAxis element).
      - Then, a relative offset is applied (via executeRelativeClick) using the suboption_index.
    """
    # Determine the base coordinate based on the marks tab category.
    if mark_index == 0:
        # For the "All" section, use the main marks tab.
        base_coord = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
        pyautogui.click(base_coord[0], base_coord[1])
    else:
        # For a specific category, use a different recorded element (for example, an axis element).
        base_coord = findPixel(axis_name, "axis", mark_index, True)
        pyautogui.click(base_coord[0], base_coord[1])
        base_coord = findPixel("marksTabsMain", "marksTabTop", mark_index + 1, False, True)
    
    # Apply the relative offset to find the suboption coordinate.
    # This assumes that executeRelativeClick returns the (x, y) coordinate without performing an actual click.

    # executeRelativeClick("markTabsMainTab", mark_index, value[0], value[1])
    # value = findPixel("markTabsMainTab", "markSubOptions", mark_index, False, True)
    suboption_coord = executeRelativeClick("markSubOptions", suboption_index, base_coord[0], base_coord[1])
    # suboption_coord = executeRelativeClick("zero", 1, base_coord[0], base_coord[1])
    
    return suboption_coord

# High-Level Tableau Automation Functions

def DragToX(variable_name):
    """
    Drags the given variable to the X axis.
    """
    executeDrag("dragToX", variable_name, "m_xAxisShelf")


def DragToY(variable_name):
    """
    Drags the given variable to the Y axis.
    """
    executeDrag("dragToY", variable_name, "m_yAxisShelf")


def DragToColor(variable_name, index, axis_name=None):
    """
    Drags a given variable to the Color mark.
    
    Usage: 
      - If index is 0, it uses the "All" marks card.
      - If index > 0, and axis_name is provided, it clicks on the specific measure/dimension.
      - If index is -1, no pre-click is done.
      
    Key Inputs:
      variable_name: The field to color by.
      index: 0 for "All", a positive integer for a specific measure, or -1 to skip activation.
      axis_name: The axis (e.g., "xAxis" or "yAxis") if a specific measure/dimension is targeted.
    """
    if index == -1:
        # Skip clicking; assume the drop target is already active.
        pass
    elif index > 0 and axis_name is not None:
        value = findPixel(axis_name, "axis", index, isAxis=True)
        pyautogui.click(value[0], value[1])
    else:
        value = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
        pyautogui.click(value[0], value[1])
    executeDrag("dragToColor", variable_name, "TableuButton:Color")


def DragToSize(variable_name, index, axis_name=None):
    """
    Drags a given variable to the Size mark.
    
    Usage:
      - If index is 0, it uses the "All" marks card.
      - If index > 0 with axis_name provided, it clicks on the corresponding measure.
      - If index is -1, it skips pre-clicking.
      
    Key Inputs:
      variable_name: The field for sizing.
      index: 0 for "All", positive integer for a specific measure, or -1 to skip activation.
      axis_name: The axis for the targeted measure if index > 0.
    """
    if index == -1:
        pass
    elif index > 0 and axis_name is not None:
        value = findPixel(axis_name, "axis", index, isAxis=True)
        pyautogui.click(value[0], value[1])
    else:
        value = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
        executeRelativeClick("zero", 1, value[0], value[1])
    executeDrag("dragToSize", variable_name, "TableuButton:size")


def DragToLabel(variable_name, index, axis_name=None):
    """
    Drags a given variable to the Label mark.
    
    Usage:
      - If index is 0, it uses the "All" marks card.
      - If index > 0 with axis_name provided, it clicks the corresponding measure/dimension.
      - If index is -1, no pre-click is done.
      
    Key Inputs:
      variable_name: The field for labels.
      index: 0 for "All", positive integer for a specific measure, or -1 to skip activation.
      axis_name: The axis to target if a specific measure/dimension is desired.
    """
    if index == -1:
        pass
    elif index > 0 and axis_name is not None:
        value = findPixel(axis_name, "axis", index, isAxis=True)
        pyautogui.click(value[0], value[1])
    else:
        value = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
        executeRelativeClick("zero", 1, value[0], value[1])
    executeDrag("dragToLabel", variable_name, "TableuButton:Label")


def DragToDetail(variable_name, index, axis_name=None):
    """
    Drags a given variable to the Detail mark.
    
    Usage:
      - If index is 0, it uses the "All" marks card.
      - If index > 0 with axis_name provided, it clicks the corresponding measure/dimension.
      - If index is -1, no pre-click is performed.
      
    Key Inputs:
      variable_name: The field to add as detail.
      index: 0 for "All", positive integer for a specific measure, or -1 to skip activation.
      axis_name: The axis to target if a specific measure/dimension is intended.
    """
    if index == -1:
        pass
    elif index > 0 and axis_name is not None:
        value = findPixel(axis_name, "axis", index, isAxis=True)
        pyautogui.click(value[0], value[1])
    else:
        value = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
        executeRelativeClick("zero", 1, value[0], value[1])
    executeDrag("dragToDetails", variable_name, "TableuButton:details")


def dimensionsFilterByFormula(var_to_filter, formula):
    """
    Applies a custom formula filter on a dimension.

    Steps:
      1. Drag the dimension (var_to_filter) into the Filters shelf.
      2. Click on the "Condition" tab.
      3. Click the "By Formula" radio button.
      4. Type in the custom formula.
      5. Click OK to apply and close the filter.

    Parameters:
      var_to_filter (str): The name of the dimension to filter.
      formula (str): The custom filter formula, e.g., "(SUM(CarrierDelay) > 10000)".
    """
    # 1. Drag the dimension into the Filters shelf.
    executeDrag("dragtoFilter", var_to_filter, "m_filterShelf")
    
    # 2. Click the "Condition" tab.
    executeClick("filterCondition", "Click the condition tab")
    
    # 3. Click the "By Formula" radio button.
    executeClick("byFormula", "Click by formula")
    
    # 4. Type in the custom formula.
    executeClickAndType("byFormula", formula)
    
    # 5. Click OK to close the filter pane.
    executeClick("closeFilter", "Click OK to close filter")

def createCalculatedField(field_name, field_formula):
    """
    Wrapper function to create a calculated field.
    
    This function automatically opens the calculated field dialog using "calcFieldOpen",
    enters the provided field name and field formula (using the preexisting executeCalculatedField function),
    and then closes the dialog by calling executeClick("calcFieldClose").

    Parameters:
      field_name (str): The name for the calculated field.
      field_formula (str): The valid formula to be entered.
    """
    # Open dialog and type field name and formula.
    executeCalculatedField("calcFieldOpen", field_name, field_formula)
    # Ensure the dialog is closed.
    executeClick("calcFieldClose")

def newSheet():
    """
    Opens a new clean sheet for creating a new graph.
    """
    executeClick("newSheet")


def sortAscending():
    """
    Sorts the current graph in ascending order.
    """
    executeClick("sortAscend")


def sortDescending():
    """
    Sorts the current graph in descending order.
    """
    executeClick("sortDescend")


def swapXandY():
    """
    Swaps the x and y columns of the current graph.
    """
    executeClick("swapxandy")

def changeTitle(new_title):
    """
    Changes the title of the current sheet.
    
    Opens the title edit mode, changes the title to new_title,
    and then closes the title edit mode.
    
    Parameters:
      new_title (str): The new title for the current sheet.
    """
    executeTitleChange("title", new_title)
    executeClick("closetitle")

def filterByTopDimension(variable_name, direction, count, formula):
    """
    Applies a Top or Bottom filter to a dimension.
    
    Steps:
      1. Drag the dimension into the Filters shelf.
      2. Click the "Condition" tab.
      3. Select either the Top or Bottom filter option based on the 'direction' input.
      4. Input the count for filtering.
      5. Enter the custom filter formula.
      6. Click OK to apply and close the filter.
    
    Parameters:
      variable_name (str): The name of the dimension to filter.
      direction (str): "Top" or "Bottom" (case-insensitive) specifying which filter to apply.
      count (int): The number of items to filter by.
      formula (str): The custom filter formula (e.g., "(SUM(CarrierDelay) > 10000)").
    """
    # 1. Drag the dimension into the Filters shelf.
    executeDrag("dragtoFilter", variable_name, "m_filterShelf")
    
    # # 2. Click the "Condition" tab.
    executeClick("filterTop", "Click the tab with the word  Top ")
    
    # # 3. Select the Top or Bottom option.
    
    executeClick("byFormulaTop", "Click by formula")
    executeClick("clickTopEntry", "Click automationid CategoricalFilterDialog.tabWidget.qt_tabwidget_stackedwidget.CategoricalFilterPageLimit.m_comboFormulaop")

    # # topBottomEntry

    if direction.lower() == "top":
        pyautogui.press("up")  # Press the Up arrow key to select "Top"
    elif direction.lower() == "bottom":
        pyautogui.press("down")  # Press the Down arrow key to select "Bottom"
    else:
        print("Invalid direction. Use 'Top' or 'Bottom'.")
        return


    pyautogui.press("enter")
    # # 4. Input the count (convert count to string for typing).

    executeClick("filterCount", "click autoatmtion id of CategoricalFilterDialog.tabWidget.qt_tabwidget_stackedwidget.CategoricalFilterPageLimit.m_formulaNumCombo")
    pyautogui.hotkey('ctrl', 'a')  # Select all text in the title field.
    pyautogui.press('backspace')   # Clear the field.
    pyautogui.write(str(count), interval=0.05)
    
    # # # 5. Enter the custom formula.
    executeClick("filterTextBox", "Make sure class name is ScintillaEditBox")
    # # executeClickAndType("byFormula", formula)ScintillaEditBox
    pyautogui.hotkey('ctrl', 'a')  # Select all text in the title field.
    pyautogui.press('backspace')   # Clear the field.
    pyautogui.write(str(formula), interval=0.05)
    
    # # 6. Click OK to close and apply the filter.
    executeClick("closeFilter", "Click OK to close filter")

def dualAxis(axis_name, index):
    """
    Performs a dual axis operation on the given axis by left-clicking the measure value
    at the specified index and then selecting the dual axis option.
    
    Parameters:
      axis_name (str): The identifier for the axis element (e.g., "xAxis" or "yAxis").
      index (int): The index of the measure value to click (based on the ordering on the axis).
      
    Process:
      1. Uses executePixelClick to left-click the measure value at the given index on the axis.
      2. Waits briefly for the measure options menu to appear.
      3. Uses executeRelativeClick to select the dual axis option (assumed to be at index 15).
      
    Returns:
      tuple: The (x, y) coordinate returned by the dual axis selection.
    """
    # Step 1: Left-click the measure value on the axis.
    measure_coord = executePixelClick(axis_name, "axis", index, True)
    time.sleep(0.2)  # Allow time for the measure options to appear

    # Step 2: Select the dual axis option.
    # According to your documentation, when two measures are present,
    # the dual axis option appears as option 15.
    dual_axis_coord = executeRelativeClick("axismeasureelement", 15, measure_coord[0], measure_coord[1])
    
    return dual_axis_coord



def changeAxisMeasure(axis_name, index, measure_type):
    """
    Changes the measure type for a measure on the specified axis.
    
    This function:
      1. Left-clicks the measure value at the given index on the specified axis.
      2. Opens the measure options menu by using a relative click with option 9.
      3. Maps the provided measure_type (e.g., "Average") to its corresponding option index.
      4. Uses a second relative click to select that measure type.
    
    Parameters:
      axis_name (str): The identifier for the axis (e.g., "xAxis" or "yAxis").
      index (int): The 1-based index of the measure value on the axis.
      measure_type (str): The measure type to change to, such as "Average", "Sum", etc.
    
    Returns:
      tuple: The (x, y) coordinate where the final measure option was clicked.
    """
    # Mapping of measure type names to their corresponding indices.
    measure_mapping = {
        "sum": 1,
        "average": 2,
        "median": 3,
        "count": 4,
        "count (distinct)": 5,
        "minimum": 6,
        "maximum": 7,
        "percentile": 8,
        "std. dev": 9,
        "std. dev (pop)": 10,
        "variance": 11,
        "variance (pop)": 12
    }
    
    # Normalize measure_type input.
    mtype = measure_type.lower().strip()
    if mtype not in measure_mapping:
        print(f"Invalid measure type: {measure_type}.")
        return None
    
    # Step 1: Left-click the measure value on the specified axis.
    measure_coord = executePixelClick(axis_name, "axis", index, True)
    time.sleep(0.2)  # Allow time for the measure options to appear

    # Step 2: Open the measure options menu.
    # According to documentation, option 9 is used to bring up the measure options.
    options_coord = executeRelativeClick("axismeasureelement", 9, measure_coord[0], measure_coord[1])
    time.sleep(0.2)
    
    # Step 3: Use the mapping to select the desired measure type.
    option_index = measure_mapping[mtype]
    final_coord = executeRelativeClick("measuresuboption", option_index, options_coord[0], options_coord[1])
    
    return final_coord


def showTrendLine():
    """
    Adds a trend line by performing the following steps:
      1. Clicks on the Analysis pane.
      2. Clicks on the trend line option (index 10).
      3. Uses a relative click to select the "Show Trend Line" submenu option (index 1).
    """
    # Step 1: Click the Analysis pane.
    base_coord = executeClick("analysisPane", "Click Analysis menu button")
    time.sleep(0.2)
    
    # Step 2: Click the trend line option (index 10).
    # executeClick("analysisPaneSuboptions", "Click trend line - index 10")

    base_coord = executeRelativeClick("analysisPaneSuboptions", 10, base_coord[0], base_coord[1])
    time.sleep(0.2)
    
    # Step 3: Click the "Show Trend Line" submenu option.
    # First, get the base coordinate for the submenu.
    # base_coord = findPixel("trendLineSubMenu", "trendLineSubMenu", 1, False, True)
    # Then, click the submenu option using a relative click (index 1).
    base_coord = executeRelativeClick("trendLineSubMenu", 1, base_coord[0], base_coord[1])
    time.sleep(0.5)


def changeAxisMeasureToDiscrete(axis_name, index):
    """
    Changes the measure type on the specified axis to either discrete or continuous.
    
    Process:
      1. Left-clicks the measure value at the given index on the axis.
      2. Uses a relative click (option 9) to open the measure options menu.
      3. Maps the provided measure_format ("discrete" or "continuous") to the correct option:
            - "discrete"   -> option index 10
            - "continuous" -> option index 11
      4. Uses another relative click to select the desired measure format.
      
    Parameters:
      axis_name (str): The identifier for the axis (e.g., "xAxis" or "yAxis").
      index (int): The 1-based index of the measure value on the axis.
      measure_format (str): The desired format ("discrete" or "continuous").
      
    Returns:
      tuple: The (x, y) coordinate of the final click, or None if an invalid format is provided.
    """
    # Normalize the measure_format string.
    
    
    # Step 1: Left-click the measure value on the axis.
    measure_coord = executePixelClick(axis_name, "axis", index, True)
    time.sleep(0.2)  # Allow time for the measure options to appear

    # Step 2: Open the measure options menu by clicking on the axis measure element.
    # option_index = format_mapping[mformat]
    options_coord = executeRelativeClick("axismeasureelement", 10, measure_coord[0], measure_coord[1])
    time.sleep(0.2)

    # Step 3: Map the measure format string to its corresponding option index.
    
    return options_coord


def changeAxisDiscreteMeasureToContinious(axis_name, index):
    """
    Changes the dimension on the specified axis to continuous.
    
    Process:
      1. Left-clicks the dimension value at the given index on the axis.
      2. Uses a relative click to open the dimension options menu.
      3. Selects the "Convert to Continuous" option (assumed to be recorded as option index 11).
      
    Parameters:
      axis_name (str): The identifier for the axis (e.g., "xAxis" or "yAxis").
      index (int): The 1-based index of the dimension on the axis.
      
    Returns:
      tuple: The (x, y) coordinate of the final click.
    """
    # Step 1: Left-click the dimension value on the axis.
    dimension_coord = executePixelClick(axis_name, "axis", index, True)
    time.sleep(0.2)  # Allow time for the dimension options to appear

    # Step 2: Open the dimension options menu.
    # Here, "axisdimensionelement" is assumed to be the recorded identifier for dimension options.
    options_coord = executeRelativeClick("axisdiscretemeasureelement", 13, dimension_coord[0], dimension_coord[1])
    time.sleep(0.2)
    
    return options_coord

import time

def changeDateType(axis_name, index, date_function, date_component):
    """
    Changes the date type of the variable on the given axis.
    
    Parameters:
      axis_name (str): The identifier for the axis (e.g., "xAxis").
      index (int): The 1-based index of the date variable on the axis.
      date_function (str): The function to use, either "DATEPART" or "DATETRUNC".
      date_component (str): One of "year", "quarter", "month", "week number", or "day".
    
    Process:
      1. Left-click the date variable on the specified axis.
      2. Wait briefly for the options menu to appear.
      3. Map the combination of date_function and date_component to an option index:
           - For DATEPART:
                "year"    -> index 12
                "quarter" -> index 13
                "month"   -> index 14
                "day"     -> index 15
                (Note: "week number" is not available for DATEPART.)
           - For DATETRUNC:
                "year"        -> index 17
                "quarter"     -> index 18
                "month"       -> index 19
                "week number" -> index 20
                "day"         -> index 21
      4. Use executeExpandedClick with a dynamic guide prompt that instructs to click the correct element.
      
    Returns:
      tuple: The (x, y) coordinate of the final click, or None if inputs are invalid.
    """
    # Step 1: Left-click the date variable on the axis.
    date_coord = executePixelClick(axis_name, "axis", index, True)
    time.sleep(0.2)  # Allow time for the date options to appear

    # Normalize the date_component string.
    dc = date_component.lower().strip()
    
    # Define mappings based on your provided JSON.
    mapping_datepart = {
        "year": 12,
        "quarter": 13,
        "month": 14,
        "day": 15
        # Note: "week number" is not available for DATEPART.
    }
    mapping_datetrunc = {
        "year": 17,
        "quarter": 18,
        "month": 19,
        "week number": 20,
        "day": 21
    }
    
    # Step 2: Determine which mapping to use.
    if date_function.upper() == "DATEPART":
        if dc not in mapping_datepart:
            print("Invalid date component for DATEPART. Choose from: year, quarter, month, or day.")
            return None
        option_index = mapping_datepart[dc]
        ordinal = "first"  # for DATEPART, click the first matching element.
    elif date_function.upper() == "DATETRUNC":
        if dc not in mapping_datetrunc:
            print("Invalid date component for DATETRUNC. Choose from: year, quarter, month, week number, or day.")
            return None
        option_index = mapping_datetrunc[dc]
        ordinal = "second"  # for DATETRUNC, click the second matching element.
    else:
        print("Invalid date function. Use DATEPART or DATETRUNC.")
        return None
    
    # Step 3: Build a dynamic guide prompt for the click inference.
    guide_prompt = (f"CLICK THE {ordinal.upper()} {dc.upper()} ELEMENT, i.e. click the {ordinal} element in the list of options that has the name '{dc}'.")
    
    # Execute the expanded click using only the guide (since prompt input is None).
    final_coords = executeExpandedClick(None, guide_prompt)
    time.sleep(0.2)
    
    return final_coords


def switchGraph(graph_type):
    """
    Switches the current graph to the specified graph type.

    Parameters:
      graph_type (str or int): Either the name of the graph type (e.g., "Pie Chart", "Heat Map", etc.)
                               or an integer (1 to 24) representing the graph type index in the Show Me menu.

    Process:
      1. Clicks the "show" button to open the "Show Me" interface.
      2. If a string is provided, looks it up in a mapping dictionary to determine the correct index.
         If an integer is provided, validates it.
      3. Uses executePixelClick to select the graph type from the "Show Me" menu.
    
    Returns:
      tuple: The (x, y) coordinate from the executePixelClick for the selected graph type,
             or None if an invalid graph type is provided.
    """
    # Mapping of graph type names to their corresponding index in the Show Me menu.
    graph_mapping = {
        "text table (crosstab)": 1,
        "heat map": 2,
        "highlight table": 3,
        "symbol map": 4,
        "filled map": 5,
        "pie chart": 6,
        "horizontal bar chart": 7,
        "stacked bar chart": 8,
        "side-by-side bar chart": 9,
        "tree map": 10,
        "circle view": 11,
        "side-by-side circle view": 12,
        "continuous line chart": 13,
        "discrete line chart": 14,
        "dual-line chart": 15,
        "area chart (continuous)": 16,
        "area chart (discrete)": 17,
        "dual combination chart": 18,
        "scatter plot": 19,
        "histogram": 20,
        "box-and-whisker plot": 21,
        "gantt chart": 22,
        "bullet graph": 23,
        "packed bubbles": 24
    }
    
    # Determine the option index from the input.
    option_index = None
    if isinstance(graph_type, int):
        if 1 <= graph_type <= 24:
            option_index = graph_type
        else:
            print("Invalid graph index. Must be an integer between 1 and 24.")
            return None
    elif isinstance(graph_type, str):
        graph_key = graph_type.lower().strip()
        if graph_key in graph_mapping:
            option_index = graph_mapping[graph_key]
        else:
            print(f"Invalid graph type name: '{graph_type}'.")
            return None
    else:
        print("Graph type must be either a string (graph name) or an integer (graph index).")
        return None

    # Step 1: Click the "show" button to open the Show Me interface.
    executeClick("show", "Click Show Me to open graph options")
    
    # Allow a brief delay for the menu to open.
    import time
    time.sleep(0.5)
    
    # Step 2: Click the desired graph type using a pixel click.
    final_coord = executePixelClick("show", "showmegraphs", option_index)
    executeClick("show", "Click Show Me to open graph options")
    return final_coord

def changeAggregation():
    base_coord = executeClick("analysisPane", "Click Analysis menu button")
    time.sleep(0.2)
    
    # Step 2: Click the trend line option (index 10).
    # executeClick("analysisPaneSuboptions", "Click trend line - index 10")

    base_coord = executeRelativeClick("analysisPaneSuboptions", 2, base_coord[0], base_coord[1])
    time.sleep(0.2)

def createBarChart(x_vars, y_vars):
    """
    Creates a basic horizontal bar chart.
    
    Parameters:
      x_vars (list of str): List of variables to be placed on the X axis.
      y_vars (list of str): List of variables to be placed on the Y axis.
    
    Process:
      1. Opens a new sheet.
      2. For each variable in x_vars, drags it to the X axis.
      3. For each variable in y_vars, drags it to the Y axis.
      4. Opens the "Show Me" menu and selects the horizontal bar chart option 
         (assumed to be mapped to index 7).
    """
    # newSheet()
    # Drag all provided variables to X axis.
    for var in x_vars:
        DragToX(var)
        time.sleep(0.1)
    
    # Drag all provided variables to Y axis.
    for var in y_vars:
        DragToY(var)
        time.sleep(0.1)
    
    # Switch to the horizontal bar chart view (index 7 as per mapping).
    switchGraph(7)
    

def createScatterChart(x_vars, y_vars):
    """
    Creates a basic scatter plot.
    
    Parameters:
      x_vars (list of str): List of variables to be placed on the X axis.
      y_vars (list of str): List of variables to be placed on the Y axis.
    
    Process:
      1. Opens a new sheet.
      2. Drags the variables in x_vars to the X axis.
      3. Drags the variables in y_vars to the Y axis.
      4. Switches to a scatter plot view (assumed to be mapped to "scatter plot").
    """
    # newSheet()
    # Drag X axis variables.
    for var in x_vars:
        DragToX(var)
        time.sleep(0.1)
    
    # Drag Y axis variables.
    for var in y_vars:
        DragToY(var)
        time.sleep(0.1)
    
    # Switch to scatter plot view (e.g., "scatter plot" which maps to index 19).
    switchGraph("scatter plot")

    changeAggregation()

    

def createLineChart(x_vars, y_vars, date_function="DATETRUNC", date_component="month"):
    """
    Creates a basic continuous line chart.
    
    Parameters:
      x_vars (list of str): List of variables for the X axis. The first should be a time-based variable.
      y_vars (list of str): List of variables for the Y axis.
      date_function (str): Either "DATEPART" or "DATETRUNC" to format the time variable.
      date_component (str): One of "year", "quarter", "month", "week number", or "day".
    
    Process:
      1. Opens a new sheet.
      2. Drags the first variable in x_vars (assumed time variable) to the X axis.
      3. Drags the first variable in y_vars (assumed measure) to the Y axis.
      4. Switches to a continuous line chart view (assumed index 13).
      5. Adjusts the date display on the X axis via changeDateType.
    """
    # newSheet()
    if not x_vars or not y_vars:
        print("Both an X-axis (time-based) variable and a Y-axis variable must be provided.")
        return
    
    # Drag the first X variable (time-based) and first Y variable.
    DragToX(x_vars[0])
    DragToY(y_vars[0])
    time.sleep(0.2)

    changeDateType("xAxis", 1, date_function, date_component)
    
    # Switch to continuous line chart view.
    switchGraph("continuous line chart")
    
    # Adjust the X-axis date display.
    # Here, we assume the time variable is the first element on the X axis.

def navigateSheetsForwards(quantity):
    """
    Navigates forwards by simulating the 'Ctrl+Tab' keystroke a given number of times.
    
    Parameters:
      quantity (int): The number of times to move forward.
    """
    navigateSheets("forwards", quantity)

def navigateSheetsBackwards(quantity):
    """
    Navigates backwards by simulating the 'Ctrl+Shift+Tab' keystroke a given number of times.
    
    Parameters:
      quantity (int): The number of times to move backward.
    """
    navigateSheets("backwards", quantity)


def main():
    print("Main controller for execute functions.")
    # Example usage:
    # DragToX("Cancelled")
    # DragToY("Origin")
    # DragToColor("Fl_Date", 2, "xAxis")
    # dimensionsFilterByFormula("Origin", "FLOAT([Origin])>0")
    # findMarkSubOption(0,5, "xAxis")
    # filterByTopDimension("Regional Manager", "top", 2, "sum([Profit])" )
    # executeClick("filterTop", "Click the top tab")
    # dualAxis("xAxis", 2)
    # changeAxisMeasure("xAxis", 2, "count (distinct)")
    # showTrendLine()
    # changeAxisMeasureToDiscrete("yAxis", 1)
    # time.sleep(0.2)
    # changeAxisDiscreteMeasureToContinious("yaxis", 1)
    # changeDateType("xAxis", 2, "DATEPART", "year")
    # switchGraph("continuous line chart")

    # filterByTopDimension("Regional Manager", "top", 2, "sum([Profit])" )
    # filterByTopDimension("Segment", "top", 2, "sum([Profit])" )
    # filterByTopDimension("Returned", "top", 2, "sum([Profit])" )


    # dimensions = ["Origin", "Dest", "Origin City Name", "Dest City Name", "Op Unique Carrier"]
    # measures = ["Arr Del 15", "Arr Delay", "Cancelled", "Carrier Delay", "Dep Delay", "Late Aircraft Delay", "Weather Delay"]
    
    # Test Case 1: Horizontal Bar Chart
    # Requirements for a horizontal bar chart: 0 or more dimensions, 1 or more measures.
    # Example: Use two measures and one dimension.
    # print("=== Creating Horizontal Bar Chart ===")
    # createBarChart(x_vars=["Dep Delay", "Arr Delay"], y_vars=["Origin"])
    # time.sleep(2)  # Pause between charts

    # # Test Case 2: Scatter Plot
    # # Requirements for a scatter plot: 0 or more dimensions, 2 measures.
    # # Example: Use "Dep Delay" for X and "Arr Delay" for Y.
    # print("=== Creating Scatter Plot ===")
    # createScatterChart(x_vars=["Dep Delay"], y_vars=["Arr Delay"])
    # time.sleep(2)  # Pause between charts

    # # Test Case 3: Continuous Line Chart
    # # Requirements for a line chart: a time-based variable on the X axis and a measure on the Y axis.
    # # Example: Use "Fl Date" (a time variable) for X and "Arr Delay" for Y.
    # # (Even if "Fl Date" is not among the provided variables, we assume it exists for testing.)
    # print("=== Creating Continuous Line Chart ===")
    # createLineChart(x_vars=["Fl Date"], y_vars=["Arr Delay"], date_function="DATETRUNC", date_component="day")
    # # changeDateType("xAxis", 1, "DATETRUNC", "day")
    # # time.sleep(1)
    # # executeExpandedClick(None, "CLICK THE SECOND DAY ELEMENT, click the second element in the index with the name of day")
    
    # createCalculatedField("Total Delay", "[Dep Delay] + [Arr Delay] + [Late Aircraft Delay]")
    # time.sleep(0.5)

    # value = findPixel("marksTabsMain", "zero", 1, False, True)
    # pyautogui.click(value[0], value[1])
    
    # Drag the calculated field "Total Delay" to the Color shelf.
    # We assume that after creation, "Total Delay" is available as a field.
    # DragToSize("Total Delay", 1, "xAxis")
    # time.sleep(0.5)

    #Sheet 1: Daily Flight Delays (Line Chart with Trend Lines)
    # newSheet()
    # changeTitle("Daily Flight Delays");
    # createLineChart(["FL_DATE"], ["DEP_DELAY", "ARR_DELAY"], date_function="DATETRUNC", date_component="day")
    # #Optionally, add a trend line for insight:
    # showTrendLine()

    # #Sheet 2: Carrier Performance (Bar Chart of Average Delays by Carrier)
    # newSheet()
    # changeTitle("Carrier Performance")
    # createBarChart(["OP_UNIQUE_CARRIER"], ["DEP_DELAY", "ARR_DELAY"]);
    # #Sort carriers by delay magnitude (largest delays first)
    # sortDescending()

    # #Sheet 3: Delay Scatter Analysis (Scatter Plot of Departure vs. Arrival Delays)
    # newSheet()
    # changeTitle("Delay Scatter Analysis")
    # createScatterChart(["DEP_DELAY"], ["ARR_DELAY"])
    # #Color-code by carrier to highlight performance differences:
    # DragToColor("OP_UNIQUE_CARRIER", 0)
    # DragToLabel("OP_UNIQUE_CARRIER", 0)

    # #Sheet 4: Total Delay by Cancellation Code (Bar Chart of Combined Delay Causes)
    # #First, create a calculated field to sum all delay types:
    # createCalculatedField("Total Delay", "[CARRIER_DELAY] + [WEATHER_DELAY] + [NAS_DELAY] + [SECURITY_DELAY] + [LATE_AIRCRAFT_DELAY]")

    # newSheet()
    # changeTitle("Total Delay by Cancellation Code")
    # createBarChart(["CANCELLATION_CODE"], ["Total Delay"])
    # sortDescending()

    # value = findPixel("marksTabsMain", "zero", 1, False, True)
    # executeClick("marksTabsMain")
    # pyautogui.click(value[0], value[1])
    # createLineChart(x_vars=["FL_DATE"], y_vars=["FlightCount"], date_function="DATETRUNC", date_component="month")
    # changeDateType("xAxis", 1, "DATETRUNC", "month")

if __name__ == "__main__":
    main()
