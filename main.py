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


import pyautogui
import time



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


def DragToColor(variable_name, axis_name, index):
    """
    Drags the given variable to the Color shelf.
    - axis_name: the axis (or mark area) to click/activate before dragging.
    - index: if 0, it uses the "All" mark tab; if > 0, it selects the corresponding measure.
    """
    # Activate the specified axis (or mark area)
    executeClick(axis_name)
    if index > 0:
        # This simulates selecting a specific measure (using the pixel lookup)
        executePixelClick(axis_name, "axis", index, isAxis=True)
    # Now drag the variable to the Color button
    executeDrag("dragToColor", variable_name, "TableuButton:Color")


def DragToSize(variable_name, axis_name, index):
    """
    Drags the given variable to the Size shelf.
    - axis_name: the axis (or mark area) to click/activate before dragging.
    - index: used to select the appropriate measure tab if needed.
    """
    executeClick(axis_name)
    if index > 0:
        executePixelClick(axis_name, "axis", index, isAxis=True)
    executeDrag("dragToSize", variable_name, "TableuButton:size")


def DragToLabel(variable_name, axis_name, index):
    """
    Drags the given variable to the Label shelf.
    - axis_name: the axis (or mark area) to click/activate before dragging.
    - index: used to select the appropriate measure tab if needed.
    """
    executeClick(axis_name)
    if index > 0:
        executePixelClick(axis_name, "axis", index, isAxis=True)
    executeDrag("dragToLabel", variable_name, "TableuButton:Label")


def DragToDetail(variable_name, axis_name, index):
    """
    Drags the given variable to the Detail shelf.
    - axis_name: the axis (or mark area) to click/activate before dragging.
    - index: used to select the appropriate measure tab if needed.
    """
    executeClick(axis_name)
    if index > 0:
        executePixelClick(axis_name, "axis", index, isAxis=True)
    executeDrag("dragToDetails", variable_name, "TableuButton:details")

    

def main():
    print("Main controller for execute functions.")
    # Prompt for the task name (e.g., 'swap_x_and_y')
    # task_name = input("Enter the task name (e.g., 'swap_x_and_y'): ").strip()
    
    # Call executeClick for that task
    
    # executeDrag("dragOrigintoX", "origin", "m_xAxisShelf")
    # executeClick("swaps")
    # executeDouble("showmark")
    # executeClick("show")
    # executePixelClick("show", "show", 7)
    # executeClick("show")
    # executeCalculatedField("calcFieldOpen", "test6","[Weather Delay]+[Dep Delay]" )
    # executeClick("CalcFieldClose")
    # executeTitleChange("title", "Example Title2")
    # executeClick("closetitle")
    # executeDrag("dragtox","Origin" ,"m_xAxisShelf")

    # executeTitleChange("title", "Arr Delay by Origin City")
    # executeClick("closetitle")
    # executeDrag("dragToY", "Origin City Name", "m_yAxisShelf")
    # executeDrag("dragToX", "Arr Delay", "m_xAxisShelf")
    # executeClick("show")
    # executePixelClick("show", "show", 1)   
    # executeClick("show")

    # navigateSheets("new", 0)
    # executeTitleChange("title", "Heatmap of Delays")
    # executeClick("closetitle")
    # executeDrag("dragToX", "Dest City Name", "m_xAxisShelf")
    # executeDrag("dragToY", "Origin City Name", "m_yAxisShelf")
    # executeDrag("dragToColor", "Arr Delay", "TableuButton:Color")
    # executeClick("show")
    # executePixelClick("show", "show", 2)   
    # executeClick("show")
    # navigateSheets("new", 0)
    # executeTitleChange("title", "Highlight of Weather Delay")
    # executeClick("closetitle")
    # executeDrag("dragToX", "Origin City Name", "m_xAxisShelf")
    # executeDrag("dragToY", "Dest City Name", "m_yAxisShelf")
    # executeDrag("dragToColor", "Weather Delay", "TableuButton:Color")
    # executeClick("show")
    # executePixelClick("show", "show", 3)   
    # executeClick("show")
    # navigateSheets("new", 0)
    # executeTitleChange("title", "Total Delay by Carrier")
    # executeClick("closetitle")
    # executeCalculatedField("calcFieldOpen", "Total Delay2", "[Carrier Delay] + [Weather Delay] + [Late Aircraft Delay] + [Dep Delay]")
    # executeClick("calcFieldClose")
    # executeDrag("dragToX", "Op Unique Carrier", "m_xAxisShelf")
    # executeDrag("dragToY", "Total Delay2", "m_yAxisShelf")
    # executeClick("show")
    # executePixelClick("show", "show", 6)   
    # executeClick("show")
    # executeDrag("dragToFilters", "Origin City Name", "m_filterShelf")
    # executeClick("filterCondition", "Click the conditon tab")
    # executeClickAndType("byFormula", "NOT ISNULL([Origin City Name])")
    # executeClick("closeFilter")
    # executeDoubleClick("yAxisClick", "Make sure you are clicking a scene margin widget and it should be a very long vertical rectangle box")
    # executeDrag("dragToDetails", "Dest City Name", "detail")
    # executeDrag("dragToSize", "Total Delay", "size")

    executeClick("xAxis")

    value = executePixelClick("xAxis", "axis", 2, True)
    time.sleep(0.2)
    print(value[1])
    hold1 = executeRelativeClick("axismeasureelement", 9, value[0], value[1])
    executeRelativeClick("measuresuboption", 3, hold1[0], hold1[1])
    # executeDrag("dragtoFilter", "Origin State Abr", "m_filterShelf")
    # executeClick("clickNone", "should click the button with the None label")
    # executeListClick("enterFilterSearch", "clickSearchFilterResult", ["CO","NM", "HI"])
    # executeClick("closeFilter")
    # value = executePixelClick("clickMeasures", "measureValue", 2, False, True)
    # hold2 = executeRelativeClick("measureValueOptions", 7, value[0], value[1])
    # executeClick("remove")
    # executeRelativeClick("measuresuboption", 3, hold2[0], hold2[1])

    # executeRelativeClick("test", 1, value[0], value[1])
    # time.sleep(1)
    # executeRelativeClick("test", 2, value[0], value[1])
    # time.sleep(1)
    # executeRelativeClick("test", 3, value[0], value[1])
    # time.sleep(1)
    # executeRelativeClick("test", 4, value[0], value[1])
    # time.sleep(1)
    # executeRelativeClick("test", 5, value[0], value[1])
    # time.sleep(1)
    # executeRelativeClick("test", 6, value[0], value[1])
        # time.sleep(0.2)

    # value = executePixelClick("xAxis", "axis", 1, True)
    # hold1 = executeRelativeClick("dateVariableOptions", 15, value[0], value[1])
    # executeRelativeClick("measuresuboption", 3, hold1[0], hold1[1])

    # executeClick("show")
    # executePixelClick("show", "showmegraphs", 16)
    # executeClick("show")
    # time.sleep(4)
    # executeClick("show")
    # executePixelClick("show", "showmegraphs", 17)
    # executeClick("show")

    # value = executePixelClick("xAxis", "axis", 1, True)
    # hold1 = executeRelativeClick("axismeasureelement", 8, value[0], value[1])
    # executeClick("marksTabsMain")
    # value = findPixel("marksTabsMain", "marksTabTop", 1, False, True)
    # executeRelativeClick("zero", 1, value[0], value[1] )
    # value = executePixelClick("marksTabOrdering", "marksTabTop", 2, False, True)
    # executeRelativeClick("zero", 1, value[0], value[1] )
    # value = executePixelClick("marksTabOrdering", "marksTabTop", 1, False, True)
    # executeRelativeClick("zero", 1, value[0], value[1] )
    # value = executePixelClick("marksTabOrdering", "marksTabTop", 3, False, True)
    # executeRelativeClick("zero", 1, value[0], value[1] )

    # value = findPixel("xAxis", "axis", 2, True)
    # executeRelativeClick("zero", 1, value[0], value[1] )

    # value = findPixel("xAxis", "axis", 1, True)
    # pyautogui.click(value[0],  value[1])
    # time.sleep(0.5)
    # pyautogui.click(value[0],  value[1])
    # executePixelClick()
    # executeClick("remove1")
    # executePixelClick("marksMarkdown", "marksMarkdown", 8)
    # value = findPixel("marksTabsMain", "markTabs1", 2, False, True)
    # pyautogui.click(value[0], value[1])

    # value = findPixel("markTabsMainTab", "markSubOptions", 5, False, True)
    # value = executeRelativeClick("markTabsMainTab", 2,value[0], value[1]  )
    # pyautogui.rightClick(value[0], value[1])
    # hold = findRelative("markvariableoptions", 8, value[0], value[1] )
    # # time.sleep(2)
    # print(pyautogui.pixel(hold[0], hold[1]))
    # pixel_color = pyautogui.pixel(hold[0], hold[1])
    # pyautogui.moveTo(401, 550)
    # if(pixel_color == (144, 200, 246) or (240, 240, 240)):
    #     value = executeRelativeClick("markvariableoptions", 8, value[0], value[1] )
    # else:
    #     value = executeRelativeClick("oppositemarkvariableoptions", 8, value[0], value[1])



    # executeClick("remove")
    # value = executeRelativeClick("markvariableoptions", 8, value[0], value[1] )
    # pixel_color = pyautogui.pixel(value[0], value[1])
    # executeRelativeClick("measureSubOption", 3, value[0], value[1] )



    

#NOT ISNULL([Origin City Name])
    # executeClick("filterCondition", "Click the conditon tab")
    # Future: You can call additional execute functions here.
    # For example:
    # from executeDouble import executeDouble
    # executeDouble(task_name)
    # from executeDrag import executeDrag
    # executeDrag(task_name)

if __name__ == "__main__":
    main()
