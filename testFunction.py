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

import time




def main():
    #################################
    # SHEET 1: Horizontal Bar Chart
    # Average Departure Delay by Airline
    # #################################

    # # Drag the dimension (OP_UNIQUE_CARRIER) to Rows (y-axis)
    # executeDrag("dragToY", "OP_UNIQUE_CARRIER", "m_yAxisShelf")

    # # Drag the measure (DEP_DELAY) to Columns (x-axis)
    # executeDrag("dragToX", "DEP_DELAY", "m_xAxisShelf")

    # # Change DEP_DELAY to Average instead of Sum on the x-axis
    # value = executePixelClick("xAxis", "axis", 1, True)


    # #change
    # hold1 = executeRelativeClick("axismeasureelement", 8, value[0], value[1])   # I HAVE CHAGNED THE VALUE FORM 8 TO 9< THE RECORDIN WAS MESSED UP


    # executeRelativeClick("measuresuboption", 2, hold1[0], hold1[1])
    # # exit()
    # # Use Show Me to pick the Horizontal Bar Chart (index 7)
    # executeClick("show")
    # executePixelClick("show", "showmegraphs", 7)

    # # Sort descending by Average(DEP_DELAY)
    # executeClick("sortDescend")

    # # Rename the sheet
    # executeTitleChange("title", "Average Departure Delay by Airline")
    # executeClick("closetitle")


    # #################################
    # # SHEET 2: Continuous Line Chart
    # # Average Arrival Delay by Day
    # #################################

    # # Create a new sheet
    # executeClick("newSheet")

    # # Drag FL_DATE to Columns (x-axis)
    # executeDrag("dragToX", "FL_DATE", "m_xAxisShelf")

    # # Convert FL_DATE to Day (Discrete) and then to Continuous
    # value2 = executePixelClick("xAxis", "axis", 1, True)
    # hold2 = executeRelativeClick("dateVariableOptions", 15, value2[0], value2[1])   # Day
    # executeRelativeClick("dateVariableOptions", 27, hold2[0], hold2[1])            # Continuous

    # # Drag ARR_DELAY to Rows (y-axis)
    # executeDrag("dragToY", "ARR_DELAY", "m_yAxisShelf")

    # # Change ARR_DELAY to Average
    # value3 = executePixelClick("yAxis", "axis", 1, True)
    # hold3 = executeRelativeClick("axismeasureelement", 9, value3[0], value3[1])
    # executeRelativeClick("measuresuboption", 2, hold3[0], hold3[1])

    # # Show Me -> Continuous Line Chart (index 13)
    # executeClick("show")
    # executePixelClick("show", "showmegraphs", 13)

    # # Rename the sheet
    # executeTitleChange("title", "Average Arrival Delay by Day")
    # executeClick("closetitle")


    # #################################
    # # SHEET 3: Filled Map
    # # Average Dep Delay by Origin State
    # #################################

    # # Create a new sheet
    # executeClick("newSheet")

    # # Drag the dimension (ORIGIN_STATE_ABR) to Details
    # executeDrag("dragToDetails", "ORIGIN_STATE_ABR", "TableuButton:details")

    # # Drag the measure (DEP_DELAY) to Color
    # executeDrag("dragToColor", "DEP_DELAY", "TableuButton:Color")

    # Change DEP_DELAY (on Color) to Average
    #   First click the measure in the Marks card listing (alphabetically, DEP_DELAY is index 6).
    # value4 = executePixelClick("clickMeasures", "measureValue", 6, False, True)
    # #   Then open measure aggregator options (option 7),
    # hold4 = executeRelativeClick("measureValueOptions", 7, value4[0], value4[1])
    # #   Then choose Average (index 2).
    # executeRelativeClick("measuresuboption", 2, hold4[0], hold4[1])

    # # Show Me -> Filled Map (index 5)
    # executeClick("show")
    # executePixelClick("show", "showmegraphs", 5)

    # # Rename the sheet
    # executeTitleChange("title", "Map - Average Dep Delay by Origin State")
    # executeClick("closetitle")

    # -----------------------------
    # Graph 1: Average Arrival Delay by Carrier
    # -----------------------------

    # Open a new sheet for Graph 1
    executeClick("newSheet")

    # Drag the dimension 'OP_UNIQUE_CARRIER' to the Columns shelf
    executeDrag("dragToX", "OP_UNIQUE_CARRIER", "m_xAxisShelf")

    # Drag the measure 'ARR_DELAY' to the Rows shelf
    executeDrag("dragToY", "ARR_DELAY", "m_yAxisShelf")

    # Set the aggregation of ARR_DELAY to Average (using measure options)
    value = executePixelClick("clickMeasures", "measureValue", 1, False, True)
    hold = executeRelativeClick("measureValueOptions", 2, value[0], value[1])  # '2' selects "Average"
    executeRelativeClick("measuresuboption", 2, hold[0], hold[1])

    # Update the chart title to "Average Arrival Delay by Carrier"
    executeClickAndType("title", "Average Arrival Delay by Carrier")
    executeClick("closetitle")

    # Apply a filter on ARR_DELAY to exclude extreme outliers
    executeDrag("dragToFilters", "ARR_DELAY", "Filters")
    executeClick("filterCondition", "Click the conditon tab")
    executeClickAndType("byFormula", "AVG(ARR_DELAY) > -50 AND AVG(ARR_DELAY) < 150")
    executeClick("closeFilter")

    # Change the view to a Horizontal Bar Chart using the Show Me panel (option index 7)
    executeClick("show")
    executePixelClick("show", "showmegraphs", 7)

    # -----------------------------
    # Graph 2: Flight Count by Origin State (Filtered to TX, CA, FL)
    # -----------------------------

    # Open a new sheet for Graph 2
    executeClick("newSheet")

    # Drag the dimension 'ORIGIN_STATE_ABR' to the Columns shelf
    executeDrag("dragToX", "ORIGIN_STATE_ABR", "m_xAxisShelf")

    # Create a calculated field "Flight Count" to count the number of flights (using FL_DATE)
    executeCalculatedField("calcFieldOpen", "Flight Count", "COUNT(FL_DATE)")
    executeClick("calcFieldClose")

    # Drag the calculated measure 'Flight Count' to the Rows shelf
    executeDrag("dragToY", "Flight Count", "m_yAxisShelf")

    # Filter the Origin State to only include TX, CA, and FL
    executeDrag("dragToFilters", "ORIGIN_STATE_ABR", "Filters")
    executeClick("clickNone")  # Clear any existing filter selections
    executeListClick("enterFilterSearch", "clickSearchFilterResult", ["TX", "CA", "FL"])
    executeClick("closeFilter")

    # Change the chart type to Horizontal Bar Chart using the Show Me panel
    executeClick("show")
    executePixelClick("show", "showmegraphs", 7)

    # Update the chart title to "Flight Count by Origin State"
    executeClickAndType("title", "Flight Count by Origin State")
    executeClick("closetitle")



if __name__ == "__main__":
    main()
