# ------------------------------ Modules Imports ----------------------------- #
# Official modules:
import os
import csv
import pandas as pd
import dgl
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
# AIPDORCS modules:
from element import Element

# ------------------------- Get Elements Information ------------------------- #
def getElementsInfo(fileName: str):
    """Extracting structural elements information to 3 lists from a given filename.

    Parameters
    ----------
        ``fileName (str)``: A path to the file.

    Returns
    ----------
        ``elemIDs (list)``: A list of element IDs.
        ``elemConnections (list)``: A list of each element's connection lists.
        ``elemGeoFeatures (list)``: A list of each element's geometric features lists.
    """    
    # Dictionary of number of features for each element type:
    featuresDict = {'Beam': 4, 'Column': 4, 'Slab': 5, 'Wall': 4}
    
    # Lists of elements information:
    elemIDs = []
    elemConnections = []
    elemGeoFeatures = []
    tempList = []
    
    # Getting the number of geometric features in the given file:
    elementType = [item for item in featuresDict if item in fileName]
    featureCount = featuresDict[elementType[0]]
    
    # Getting element information from the database:
    with open(fileName, 'r') as csvFile:
        elementsFile = csv.reader(csvFile, delimiter=',')
        # Loop over lines in the file:
        for line in elementsFile:
            match line[0]:
                case 'Beam ID' | 'Column ID' | 'Slab ID' | 'Wall ID':
                    elemIDs.append(line[1])
                
                case 'Beam Connections' | 'Column Connections' | \
                    'Slab Connections' | 'Wall Connections':
                    elemConnections.append(line[1:])
                
                case other: # other = geometric features
                    tempList.append(line[1])
                    # Adding all elements' geometric features together:
                    if len(tempList) == featureCount:
                        elemGeoFeatures.append(tempList)
                        tempList = []
    
    return elemIDs, elemConnections, elemGeoFeatures

# ------------------ Check if a Graph's Edge Already Exists ------------------ #
def isEdgeAlreadyExists(allEdges: list, edge: list):
    """Returns 'True' if any sublist of 'allEdges' list contains the specified 'edge' list, Otherwise 'False'.

    Parameters
    ----------
    ``allEdges (list)``: A list of graph edges lists (2-dimensional list).
    ``edge (list)``: A list of one graph edge.

    Returns
    -------
    ``result (bool)``: A variable indicating whether the edge exists or not.
    
    Examples
    --------
    >>> # Given lists:
    >>> list1 = [['A1', 'A2'], ['A1', 'A3']]
    >>> list2 = ['A3', 'A1']
    >>> # Calling the function to see if list1 contains list2 in any order:
    >>> result = isEdgeAlreadyExists(list1, list2)
    >>> # result == True
    """
    result = False
    
    # Loop over sub-lists of 'allEdges' list:
    for i in range(len(allEdges)):
        if all(connection in allEdges[i] for connection in edge):
            result = True
            break
    
    return result

def elemConnectionsToEdges(allIDs: list, allConnections: list):
    """_summary_
    
    Parameters
    ----------
    ``allIDs (list)``: _description_
    ``allConnections (list)``: _description_
    
    Returns
    -------
    `` (_type_)``: _description_
    
    Examples
    --------
    >>> _codeExample_"""
    edgesList = []
    
    for i, elemConnections in enumerate(allConnections):
        elemID = allIDs[i]
        
        for connection in elemConnections:
            edge = [elemID, connection] # FIXME: add node ID instead of element ID
            if not isEdgeAlreadyExists(edgesList, edge):
                edgesList.append(edge)
    
    return edgesList

# ------------------ Build a Graph from Elements Information ----------------- #
def homoGraphFromElementsInfo(dataDir: str, modelCount: int, featureCount: int):
    # List of structural element types possible:
    elementTypes = ['Beam', 'Column', 'Slab', 'Wall']
    
    # Loop over models data from Dynamo:
    for model in range(1, modelCount+1):
        projectDir = f'{dataDir}\\Project {model:03d}'
        
        with open(f'{projectDir}\\Nodes.csv', 'w') as csvFile1, \
            open(f'{projectDir}\\Edges.csv', 'w') as csvFile2:
            nodes = csv.writer(csvFile1)
            edges = csv.writer(csvFile2)
            # Writing header to CSV files:
            nodes.writerow(['Node ID', 'Element ID', 'Dim 1', 'Dim 2', 'Dim 3', 'Volume'])
            edges.writerow(['Src ID', 'Dst ID'])
            
            allIDs = []
            allConnections = []
            allGeoFeatures = []
            
            # Loop over element types:
            for elementType in elementTypes:
                fileName = f'{projectDir}\\{elementType}sData.csv'
                elemIDs, elemConnections, elemGeoFeatures = getElementsInfo(fileName)
                
                # Slicing elemGeoFeatures to get only the given number of features for each element:
                for i in elemGeoFeatures:
                    if len(i) > featureCount:
                        del i[featureCount:]
                
                # Getting all elements' information from all element types:
                allIDs.extend(elemIDs)
                allConnections.extend(elemConnections)
                allGeoFeatures.extend(elemGeoFeatures)
            
            # Loop over elements in each CSV file:
            nodeIDs = []
            for i in range(0, len(allIDs)):
                nodes.writerow([i] + [allIDs[i]] + allGeoFeatures[i])
                nodeIDs.append(i)
                # FIXME: The dimension features are not in the same order for all elements
            
            # TODO: Write to edges file
            edgesList = elemConnectionsToEdges(nodeIDs, allConnections)
            intEdgesList = []
            # for i in edgesList:
                # intEdgesList[i] = list(map(int, i))
            edges.writerows(edgesList)
        
        nodesData = pd.read_csv(f'{projectDir}\\Nodes.csv')
        edgesData = pd.read_csv(f'{projectDir}\\Edges.csv')
        # src = edgesData['Src ID'].to_numpy()
        # dst = edgesData['Dst ID'].to_numpy()
        
        src = [0, 0, 1]
        dst = [1, 3, 2]
        
        nodeDict = {0: 'B9', 1: 'B10', 2: 'C24', 3: 'W76'}
        
        g = dgl.graph((src, dst))
        
        nxGraph = g.to_networkx()
        nx.draw_networkx(nxGraph, with_labels=True, arrowstyle='-', node_size=1000, \
                        node_color='#0091ea', edge_color='#607d8b', width=4.0, \
                        labels=nodeDict, label='Model Graph')
        plt.show()

# ------------------------------- Main Function ------------------------------ #
def main():
    # Inputting directory path and number of models:
    # print('Please type a directory path containing all projects data from Dynamo', 
    #       'or leave empty to use the default path "~\\..\\Dynamo".')
    # dataDir = input('Type a directory path here: ') or '~\\..\\Dynamo'
    # print('Please enter the number of models you have in this directory.')
    # modelCount = int(input('Type an integer number of models: '))
    workspace = os.getcwd()
    dataDir = f'{workspace}\\Dynamo'
    modelCount = 2
    featureCount = 4
    
    homoGraphFromElementsInfo(dataDir, modelCount, featureCount)

# ------------------------------- Run as Script ------------------------------ #
if __name__ == '__main__':
    main()