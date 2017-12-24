# -*- coding: utf-8 -*-

from urllib import request
import json
import xml.etree.ElementTree as ET
from datetime import date
import copy
import csv
import os

import Mappings as mappings
import DDIXMLTree


def urllister(addressbook):
    csv.register_dialect('semic', delimiter=';')
    urllist = []
    filereader = csv.reader(open(addressbook), dialect='semic')
    for row in filereader:

        if row is None:
            break

        else:

            # Append value in position [1] in rowlist

            newUrl = row[1].replace('http://ecds.se/dataset/', 'https://ecds.se/api/3/action/package_show?id=')
            urllist.append(newUrl)
    return urllist


# Imports JSON file from url and returns it as data object
def jsonImport(url):
    with request.urlopen(url) as url:
        data = json.loads(url.read())
        # print((data))
        return data


'''
class ECDS2SND:
    def __init__(self, JSONinput):
        self.outDict = {}
        self.studyTitleContents = {"titl" : JSONinput['result']['ECDS_identificationInfo_citation_title']}
        self.outDict.update(self.studyTitleContents)
    def returnDict(self):
        outDict = self.outDict
        print(outDict)
        return outDict
  '''


class DDIRoot:
    def __init__(self):
        self.tree = DDIXMLTree.DDITree()



    def mapECDSToDDI(self, JSONinput):


        varMap = mappings.varMap(JSONinput) # import mappings between xml tree and ecds fields as a dictionary

        for key, value in varMap.items():

            # print(key, self.tree.findall(key))
            elem = self.tree.findall(key)[0]  # find all elements using XPATH - returns list which shall only contain one result

            if type(value) is list:  # automatically longer than 1, so assume that list has at least 2 items

                elem.text = value[0]
                i = 1
                for e in value[1:]:
                    k = key.rfind("/")
                    parent = self.tree.findall(key[:k])
                    # print(parent[0])

                    parent[0].append(copy.deepcopy(elem))
                    new_elem = self.tree.findall(key)[0]

                    new_elem.text = e
                    # print ('elemcopy  ', new_elem)



                    # print(e)
            else:
                elem.text = value

        #Now to import keywords - separate instructions due to problems integrating import in above
        vocabelem = self.tree.findall('.//keyword')[0]

        tagslist = JSONinput['result']['tags'] #get list of tag dicts from JSON
        vocabelem.text = tagslist[0]['name'] #this gives the existing keywrod element an entry
        print(vocabelem.text)

        #Set depdate
        #'./stdyDscr/citation/distStmt/depDate': str(safeget(JSONinput, 'result', "ECDS_dateStamp").partition("T")[0])
        depdate = self.tree.findall( './stdyDscr/citation/distStmt/depDate')[0]
        depdate.set('date', JSONinput['result']["ECDS_dateStamp"].partition("T")[0])


        #the rest creates a new element for each vocabulary entry in the JSON dictionary list
        listlength = len(tagslist)
        listcounter = 1 #starts from 1 since 0 populates preexisting element
        parentelem = self.tree.findall('.stdyDscr/stdyInfo/subject')[0] #the actual subject element which is parent to the vocab dict
        print(parentelem)
        while listcounter < listlength:
            n = copy.deepcopy(vocabelem)
            n.text = tagslist[listcounter]['name']
            print(listcounter)

            parentelem.append(n)#findall('./stdyDscr/stdyInfo/subject/keyword[last()]')[0]
            listcounter += 1

        #Now to set accessibility level by checking if there is a download file available
        try:
            JSONinput['result']["ECDS_distributionInfo_distributor_distributorTransferOptions_onLine"] # if an error is given then switch to exception
            self.tree.findall('./stdyDscr/dataAccs/setAvail/avlStatus')[0].text = \
                '1a - Fritt tillgänglig utan registrering'
        except KeyError:
            self.tree.findall('./stdyDscr/dataAccs/setAvail/avlStatus')[0].text = \
                '3a - Data finns ej tillgängliga via SND. Kan laddas ner från extern hemsida' #3a by default.
            # 3b needs to be set manually

        # Here we set attribute 'date' to the timePrd element. Cleaner to do it here than within a dict...
        investigationperiods = self.tree.findall('./stdyDscr/stdyInfo/sumDscr/timePrd') # there should be 2 instances resulting
        investigationperiods[0].set('date', investigationperiods[0].text) # a copy of the element's text is added to a tag
        investigationperiods[1].set('date', investigationperiods[1].text)


        # ET.dump(self.tree)


        return self.tree

    def exportDDI(self, XMLTree, outFolder):

        outputTitle = self.tree.findall('./docDscr/docSrc/titlStmt/titl')[0].text + '.xml'
        outPath = os.path.join(outFolder, outputTitle)

        try:
            self.tree.write(outPath, encoding='utf-8', xml_declaration=True)

        except (OSError, AttributeError):
            for ch in ['\\', '/', ':', '*', '?', '\"', '<', '>', '|']:
                outputTitle = outputTitle.replace(ch, '_')
                print(outputTitle)

            outPath = os.path.join(outFolder, outputTitle)
            print(outPath)
            self.tree.write(outPath, encoding='utf-8', xml_declaration=True)


for url in urllister('ecds_smhi.csv'):
    print(url)
    try:
        jsonFile = jsonImport(url)
        DDIObj = DDIRoot()
        DDITree = DDIObj.mapECDSToDDI(jsonFile)
        # outputName = DDITree.findall('./docDscr/docSrc/titlStmt/titl')[0]  '.xml'
        outputPath = 'results'
        DDIObj.exportDDI(DDITree, outputPath)
    except ValueError:
        continue





# print the tree and save to output.xml
# ET.dump(DDITree)

