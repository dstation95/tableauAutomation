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
# Create a new worksheet
    # executeClick("newSheet")

    # Rename the sheet’s title
    executeTitleChange("title", "Arrival Delay by Carrier")
    executeClick("closetitle")

    # Drag the Dimension 'Op Unique Carrier' to the Y-axis (rows)
    executeDrag("dragCarrierY", "Op Unique Carrier", "m_yAxisShelf")

    # Drag the Measure 'Arr Delay' to the X-axis (columns)
    executeDrag("dragArrDelayX", "Arr Delay", "m_xAxisShelf")

    # Optionally color the bars by another measure or dimension (e.g., Cancelled)
    executeDrag("dragCancelColor", "Cancelled", "TableuButton:Color")

    # Sort the bars descending so that the carrier with the highest arrival delay is on top
    executeClick("sortDescend")



    # Create a second sheet
    navigateSheets("new", 0)

    # Rename the sheet’s title
    executeTitleChange("title", "Departure Delay by Origin")
    executeClick("closetitle")

    # Drag 'Origin' (Dimension) to the Y-axis
    executeDrag("dragOriginY", "Origin", "m_yAxisShelf")

    # Drag 'Dep Delay' (Measure) to the X-axis
    executeDrag("dragDepDelayX", "Dep Delay", "m_xAxisShelf")

    # Sort ascending if desired
    executeClick("sortAscend")

    # (Optional) Filter out flights that were cancelled (keep Cancelled == 0 only)

    # 1. Drag the 'Cancelled' measure to Filters
    executeDrag("dragCancelledFilter", "Cancelled", "Filters")

    # 2. Click the "None" button to deselect all
    executeClick("clickNone")

    # 3. Use the multi-select function to pick only "0" from Cancelled
    executeListClick("enterFilterSearch", "clickSearchFilterResult", ["0"])

    # 4. Confirm the filter
    executeClick("closeFilter")



    # Create a third sheet
    navigateSheets("new", 0)

    # Rename the sheet’s title
    executeTitleChange("title", "Arr vs Dep Delay by Origin")
    executeClick("closetitle")

    # Drag 'Origin' to the Rows shelf (for a vertical grouping)
    executeDrag("dragOriginToRows", "Origin", "m_yAxisShelf")

    # Next, we will create a side-by-side bar chart by using Measure Names / Measure Values:

    # 1. Drag "Measure Values" to the X-axis shelf
    executeDrag("dragMeasureValuesX", "Measure Values", "m_xAxisShelf")

    # 2. Filter which measures appear in “Measure Values”:
    #    We'll keep only 'Arr Delay' and 'Dep Delay' for instance.
    executeDrag("dragMeasureNamesFilter", "Measure Names", "Filters")
    executeClick("clickNone")
    executeListClick("enterFilterSearch", "clickSearchFilterResult", ["Arr Delay", "Dep Delay"])
    executeClick("closeFilter")

    # 3. Place "Measure Names" on color (optional)
    executeDrag("dragMeasureNamesColor", "Measure Names", "TableuButton:Color")

    # Sort if you wish:
    executeClick("sortDescend")





if __name__ == "__main__":
    main()
