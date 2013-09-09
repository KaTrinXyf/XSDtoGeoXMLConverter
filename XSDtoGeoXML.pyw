'''
XSD to GeoXML Converter

This script converts an XSD schema document into a GeoXML document.
The XSD files are dynamically pulled from "http://schemas.usgin.org/contentmodels.json" upon user selection.
The script requires the file mapping_file_template.xml to be in the same folder as the script.
Created GeoXML docuements are written to the same folder as the script.

Created on Jun 6, 2013
Written by Jessica Good Alisdairi at the Arizona Geological Survey
'''

from xml.dom.minidom import parse, parseString
from Tkinter import *
import os
import urllib2
import json
import time

def main(argv=None):
    print "Loading ..."

    # Get the info in json format about all the schemas on "http://schemas.usgin.org/contentmodels.json"
    url = "http://schemas.usgin.org/contentmodels.json"
    try:
        schemasInfo = json.load(urllib2.urlopen(url))
    except:
        print "Unable to reach " + url + " to read content model schemas."
        time.sleep(5.5)
        return
    else:
        readSchema(schemasInfo)
        return
        
def readSchema(schemasInfo):
    # Read the json to get the name of the all the schemas + version number + .xsd location
    schemasList = {}
    for rec in schemasInfo:
        t = rec['title']
        for v in rec['versions']:
            schemaName = t + v['version']
            schemaName = schemaName.replace(" ","").encode('UTF-8')
            schemasList[schemaName] = v['xsd_file_path'].encode('UTF-8')
            
#     for s in schemasList:
#         print s + "," + schemasList[s]

    root = Tk()
     
    returnValue = True
    while returnValue:
        returnValue = ListBoxChoice(root, "XSD to GeoXML", "Select one of the schemas below", schemasList.keys()).returnValue()
        if returnValue:
            createGeoXML(schemasList, returnValue)
            print "GeoXML created for " + returnValue
    return
     
def createGeoXML(schemasList, schemaFile):
    
    # Get the .xsd schema location for the user inputed schema name and read the schema       
    schemaUrl = schemasList[schemaFile]
    schema = urllib2.urlopen(schemaUrl).read()  
    domXSD = parseString(schema)  

    # Hardcoded files for testing
    path =  os.path.dirname(os.path.abspath(__file__))
#     path = "C:\\Users\\jalisdairi\\Desktop\\XSDtoGeoXML Test\\" # Path
#     xsd = path + "ActiveFaults_1.xsd"                      # Schema file
    xmlTemplate = path + "\\mapping_file_template.xml"            # Template file
#     output = open(path + '\\output.xml', 'w')                     # Create output file
    output = open(path + '\\' + str(schemaFile.replace("/","")) + '.xml', 'w')                     # Create output file

    # Read schema
#     domXSD = parse(xsd)
    
    schemaFields = []
    schemaTypes = []
    schemaReq = []
    
    # Get specific attributes
    for node in domXSD.getElementsByTagNameNS("http://www.w3.org/2001/XMLSchema", "schema"):
        schemaUri = node.getAttribute("xmlns:aasg")  

    # Get the values of the name, type and minOccurs attributes from the schema
    for node in domXSD.getElementsByTagNameNS("http://www.w3.org/2001/XMLSchema", 'element'):
        schemaFields.append(node.getAttribute('name'))
        schemaTypes.append(node.getAttribute('type'))
        schemaReq.append(node.getAttribute('minOccurs'))
    
    # Get the index of the OBJECTID field and remove that and any fields before it
    objectIDIndex = schemaFields.index("OBJECTID")
    layerNames = []
    i = 0
    while i < objectIDIndex:
        layerNames.append(schemaFields[0])
        schemaFields.pop(0)
        schemaTypes.pop(0)
        schemaReq.pop(0)
        i = i + 1
    del i

    # Remove the OBJECTID field
    schemaFields.pop(0)
    schemaTypes.pop(0)
    schemaReq.pop(0)
    
    # Remove any Shape fields
#     foundAll = False
#     while foundAll == False:
#         try:
#             shapeIndex = schemaFields.index("Shape")
#             schemaFields.pop(shapeIndex)
#             schemaTypes.pop(shapeIndex)
#             schemaReq.pop(shapeIndex)
#         except:
#             foundAll = True
#     del foundAll
    
    # Read template
    dom = parse(xmlTemplate)
    
    # Modify template
    
    # Change the value of <uri> to the schemaURI
    elemSchemaURI = dom.getElementsByTagName("uri")[0].childNodes[0]
    elemSchemaURI.nodeValue = schemaUri
    
    # Change "LAYER_NAME" in <id> to the layerName in lowercase
    elemDataStoreID = dom.getElementsByTagName("id")[0].childNodes[0]
    elemDataStoreID.nodeValue = elemDataStoreID.nodeValue.replace("LAYER_NAME", layerNames[0].lower())
    
    # Change the value of <schemaUri> to the schemaURI
    elemSchemaURI = dom.getElementsByTagName("schemaUri")[0].childNodes[0]
    elemSchemaURI.nodeValue = schemaUrl
    
    # Change "LAYER_NAME" in <sourceDataStore> to the layerName in lowercase
    elemTargetAttribute = dom.getElementsByTagName("sourceDataStore")[0].childNodes[0]
    elemTargetAttribute.nodeValue = elemTargetAttribute.nodeValue.replace("LAYER_NAME", layerNames[0].lower())
    
    # Change "LAYER_NAME" in <targetElement> to the layerName
    elemTargetAttribute = dom.getElementsByTagName("targetElement")[0].childNodes[0]
    elemTargetAttribute.nodeValue = elemTargetAttribute.nodeValue.replace("LAYER_NAME", layerNames[0])
    
    # Get the nodes
    nodeAttributeMappings = dom.getElementsByTagName("attributeMappings")[0]
    nodeAttributeMapping = dom.getElementsByTagName("AttributeMapping")[0]

    # For each schema field in the schemaFields list
    for schemaField in schemaFields:
        # Make a copy of the <AttributeMapping> node
        nodeCopy = nodeAttributeMapping.cloneNode(True)
        
        # Change "LAYER_NAME" in <targetAttribute> to the schemaField
        elemTargetAttribute = nodeCopy.getElementsByTagName("targetAttribute")[0].childNodes[0]
        elemTargetAttribute.nodeValue = elemTargetAttribute.nodeValue.replace("LAYER_NAME", schemaField)
        
        # Change "LAYER_NAME" in <OCQL> to the schemaField in lowercase
        elemOCQL = nodeCopy.getElementsByTagName("OCQL")[0].childNodes[0]
        elemOCQL.nodeValue = schemaField.lower()
        
        # Append the modified <AttributeMapping> node to the end of <attributeMappings> node
        nodeAttributeMappings.appendChild(nodeCopy)
    
    # Change "LAYER_NAME" in the first <targetAttribute> to the layerName
    elemTargetAttribute = nodeAttributeMapping.getElementsByTagName("targetAttribute")[0].childNodes[0]
    elemTargetAttribute.nodeValue = elemTargetAttribute.nodeValue.replace("LAYER_NAME", layerNames[0])

    # Write modified template to new file
    output.write(dom.toxml())
    return

# From http://code.activestate.com/recipes/410646-tkinter-listbox-example/
class ListBoxChoice(object):
    def __init__(self, master=None, title=None, message=None, list=[]):
        self.master = master
        self.value = None
        self.list = list[:]
        
        self.modalPane = Toplevel(self.master)

        self.modalPane.transient(self.master)
        self.modalPane.grab_set()

        self.modalPane.bind("<Return>", self._choose)
        self.modalPane.bind("<Escape>", self._cancel)

        if title:
            self.modalPane.title(title)

        if message:
            Label(self.modalPane, text=message).pack(padx=5, pady=5)

        listFrame = Frame(self.modalPane)
        listFrame.pack(side=TOP, padx=5, pady=5)
        
        scrollBar = Scrollbar(listFrame)
        scrollBar.pack(side=RIGHT, fill=Y)
        self.listBox = Listbox(listFrame, selectmode=SINGLE, width=50)
        self.listBox.pack(side=LEFT, fill=Y)
        scrollBar.config(command=self.listBox.yview)
        self.listBox.config(yscrollcommand=scrollBar.set)
        self.list.sort()
        for item in self.list:
            self.listBox.insert(END, item)

        buttonFrame = Frame(self.modalPane)
        buttonFrame.pack(side=BOTTOM)

        chooseButton = Button(buttonFrame, text="Choose", command=self._choose)
        chooseButton.pack()

        cancelButton = Button(buttonFrame, text="Cancel", command=self._cancel)
        cancelButton.pack(side=RIGHT)

    def _choose(self, event=None):
        try:
            firstIndex = self.listBox.curselection()[0]
            self.value = self.list[int(firstIndex)]
        except IndexError:
            self.value = None
        self.modalPane.destroy()

    def _cancel(self, event=None):
        self.modalPane.destroy()
        
    def returnValue(self):
        self.master.wait_window(self.modalPane)
        return self.value

if __name__ == "__main__":
    main()