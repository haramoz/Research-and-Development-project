import copy
import csv
from sklearn import tree
import numpy as np
from sklearn import cross_validation
from sklearn.externals.six import StringIO
import pydot
import os
import matplotlib.pyplot as plt
import glob
import math

''' Here the turbulent flow is represented by 2, separation as 3 and Laminar as 1'''
class processRealData:
    
    def __init__(self,learningProblem,seriesLengthInSeconds,readPath,writePath,slidingWindow=False):
        self.frameRatePerSecond = 120
        self.seriesLengthInSeconds = seriesLengthInSeconds #0.5 #0.0625
        self.featuresPerSeries = self.seriesLengthInSeconds * self.frameRatePerSecond
        self.framesInTheSlidingWindow = int(self.featuresPerSeries/3)
        self.learningProblem = learningProblem
        #This is the path from where the experiment results will be read
        self.readPath = readPath
        self.writePath = writePath
        self.slidingWindow = slidingWindow
        print 2*self.featuresPerSeries

    def outlierDetection(self,listItem):
        #Reference http://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm
        listItem = copy.deepcopy(listItem)
        #Step1: Sort the list
        sortedListItem = sorted(listItem)
        #Step2: Find the median value
        medianValue = self.calculateMedian(sortedListItem)
        #Step3: Find the lower quartile
        lowerQuartile = sortedListItem[:len(listItem)//2]
        lowerQuartileValue = self.calculateMedian(lowerQuartile)
        #Step4: Find the upper quartile
        upperQuartile = sortedListItem[len(listItem)//2:]
        upperQuartileValue = self.calculateMedian(upperQuartile)
        #Step5 find interquartile range
        interquartileRange = (upperQuartileValue - lowerQuartileValue)*1.5
        innerFences = ((lowerQuartileValue - interquartileRange),(upperQuartileValue + interquartileRange)) 
        #Step6 find outerquartile range
        interquartileRange2 = (upperQuartileValue - lowerQuartileValue)*3.0
        outerFences = ((lowerQuartileValue - interquartileRange2),(upperQuartileValue + interquartileRange2)) 
        
        #Step7 Calculate the major and minor outliers
        majorOutliers = []
        minorOutliers = []
        #print "outerFences",outerFences
        for i in listItem:
            if i < outerFences[0] or i > outerFences[1]:
                majorOutliers.append(i)
            if (i < innerFences[0] or i > innerFences[1]) and i not in majorOutliers:
                minorOutliers.append(i) 
        #print "majorOutliers",majorOutliers
        #print "minorOutliers",minorOutliers
        #print "number of majorOutliers",len(majorOutliers)
        #print "number of minorOutliers",len(minorOutliers)
        return majorOutliers,minorOutliers

    def calculateMedian(self,listItem2):
        listItem2 = copy.deepcopy(listItem2)
        if len(listItem2) == 0:
            print "Empty array"
            return None
        if len(listItem2)%2 == 0:
            middleValue = len(listItem2)//2
            medianValue = (listItem2[middleValue] + listItem2[middleValue+1])/2.0
        else:
            medianValue = (listItem2[len(listItem2)//2])
        #print medianValue
        return medianValue

    def rangeFinder(self,listItem3,outliers):
        listItem3 = copy.deepcopy(listItem3)
        outliers = copy.deepcopy(outliers)
        withoutOutliersList = []
        if len(outliers) > 0:
            for v in listItem3:
                if v not in outliers:
                    withoutOutliersList.append(v)
            valueRange = (min(withoutOutliersList),max(withoutOutliersList))
        else:
            valueRange = (min(listItem3),max(listItem3))
            withoutOutliersList = listItem3

        print "range",valueRange[0],valueRange[1]
        medianValue = self.calculateMedian(withoutOutliersList)
        return valueRange,medianValue

    '''This function reads files and creates a feature list which are sent to 
    writeFeatures() function which creates .csv files contaning features and
    separate files contaning related labels'''

    def processFiles(self):

        list_of_files = glob.glob(self.readPath+'*.txt')
        #list_of_files = glob.glob('./tuft_real_data/22April/*.txt')
        colorCode = -1
        colors = ["ro","bo","mo","go","yo"]
        numberOfFiles = 1
        #For median Plot
        mediansX = []
        mediansY = []
        speeds = []
        averagesX = []
        averagesY = []
        '''For the speed vs outlier analysis'''
        speedsStack = []
        outlierStackX = []
        outlierStackY = []
        for fileName in list_of_files:
            print os.path.splitext(fileName)[0].split("/")[-1]
            #data_list = open( fileName, "r" ).readlines()
        
            featureSet = []
            #endpointX = []
            #endpointY = []
            typeOfFlow = None
            speed = 0.0
            #Saving x and y coordinates separately for range analysis
            xValues = []
            yValues = []
            colorCode += 1 
            xDiff = []
            yDiff = []
            #For one file should be one origin x and y
            originX = None
            originY = None
            flagOrigin = True
            with open(fileName,'r') as f:
                for line in f:
                    if "TYPE" in line and line != "":
                        typeOfFlow = line.split()
                        typeOfFlow = typeOfFlow[1]
                        #print typeOfFlow 
                    elif "SPEED" in line and line != "":
                        speed = line.split()
                        speed = speed[1]   
                        #print speed
                    elif "VECTOR" in line and line != "":
                        coordinates = line.split()
                        #print coordinates[0]
                        if flagOrigin:
                            originX = float(coordinates[1])
                            originY = float(coordinates[2])
                            flagOrigin = False
                        #xDiff.append(float(coordinates[3]) - float(coordinates[1]))
                        #yDiff.append(float(coordinates[4]) - float(coordinates[2]))
                        #xValues.append(coordinates[1])
                        xValues.append(float(coordinates[3]))
                        #yValues.append(coordinates[2])
                        yValues.append(float(coordinates[4]))
                        #featureSet.append(endpointX)
                        #featureSet.append(endpointY)
                '''make it more readable please'''
                featureFileName = os.path.splitext(fileName)[0].split("/")[-1]
            
                        
            numberOfFiles += 1

            #Calculating the outliers
            majorOutliersX,minorOutliersX = self.outlierDetection(xValues)
            majorOutliersY,minorOutliersY = self.outlierDetection(yValues)

            speeds.append(speed)
            
            
            '''Note: The way this logic is implemented the outliers in y 
            does not come into play at all'''

            withoutOutliersListX = []
            withoutOutliersIndex = []
            for i in range(len(xValues)):
                if xValues[i] not in majorOutliersX:
                    withoutOutliersListX.append(xValues[i])
                    withoutOutliersIndex.append(i)
            withoutOutliersListY = []
            for i in range(len(yValues)):
                if i in withoutOutliersIndex:
                    withoutOutliersListY.append(yValues[i])
                    xDiff.append(xValues[i]-originX)
                    yDiff.append(yValues[i]-originY)   
            
            #Function call for the supplying the polar coordinates
            distances,angles,featureSet = self.supplyPolarCoordinates(xDiff,yDiff)

            if self.slidingWindow:
                #Write overlapping features
                self.writeOverlappingFeatures(featureSet,featureFileName,typeOfFlow,speed)
            else:
                #Function call to write features in .csv format
                self.writeFeatures(featureSet,featureFileName,typeOfFlow,speed)
            
            
        #plt.show()
        return featureSet

    def distanceCalculator(self,diff1,diff2):
        distance = np.sqrt(pow(diff1,2)+pow(diff2,2))
        return distance


    '''This function calculates the polar coordinates for supplied list of cartesian coordinates'''
    def supplyPolarCoordinates(self,xDiff,yDiff):
        xDiff = copy.deepcopy(xDiff)
        yDiff = copy.deepcopy(yDiff)
        polarDistances = [] 
        angles = []
        features = []
        for i in range(len(xDiff)):
            dist = self.distanceCalculator(xDiff[i],yDiff[i])
            polarDistances.append(dist)
            theta = math.degrees(math.atan2(yDiff[i],xDiff[i]))
            angles.append(theta)
            features.append(dist)
            features.append(theta)
        return polarDistances,angles,features
    
    '''This function writes the vector series data and labels in .csv format.
    The length of the series depends on the parameters in init'''
    def writeFeatures(self,fileContent,fileName,typeOfFlow,speed):
        features = copy.deepcopy(fileContent)
        #print features
        #speed = float(speed)
        if speed == 'NA' and self.learningProblem != "classification":
            print "speed not available"
            return None
        else:
            print typeOfFlow,speed


        #path = './tuft_real_data/3May/extractedFeatures/'
        path = self.writePath

        with open(path+'data/'+fileName+'.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            eachLine = []
            counter = 0
            counter2 = 0
            for i in features: 
                eachLine.append(i)
                counter += 1
                if counter%(2*self.featuresPerSeries) == 0:
                    writer.writerow(eachLine)
                    eachLine = []
                    counter2 += 1
            

        with open(path+'labels/'+fileName+'label.csv', 'w') as csvfile2:
            writer2 = csv.writer(csvfile2,delimiter=',')
            counter = 0
            for i in features: 
                counter += 1
                if counter%(2*self.featuresPerSeries) == 0:
                    if self.learningProblem == "classification":
                        writer2.writerow(typeOfFlow)
                    else:
                        writer2.writerow([speed])
            

    '''This function writes the vector series data and labels in .csv format.
    The length of the series depends on the parameters in init. It writes overlapping data
    for training purpose'''

    def writeOverlappingFeatures(self,fileContent,fileName,typeOfFlow,speed):
        features = copy.deepcopy(fileContent)
        #print features
        #speed = float(speed)
        print typeOfFlow,speed
        if speed == 'NA' and self.learningProblem != "classification":
            print "NA speed encountered!!"
            return None
        path = self.writePath
        with open(path+'data/'+fileName+'.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            eachLine = []
            counter = 0
            counter2 = 0
            for i in features: 
                eachLine.append(i)
                counter = len(eachLine)
                if counter%(2*self.featuresPerSeries) == 0:
                    writer.writerow(eachLine)
                    #eachLine = []
                    eachLine = eachLine[2*self.framesInTheSlidingWindow:]
                    counter2 += 1

        with open(path+'labels/'+fileName+'label.csv', 'w') as csvfile2:
            writer2 = csv.writer(csvfile2,delimiter=',')
            counter = 0
            #counter2 = 0
            for i in range(counter2): 
                counter += 1
                if self.learningProblem == "classification":
                    writer2.writerow(typeOfFlow)
                else:
                    writer2.writerow([speed])  
    
if __name__ == "__main__":
    readPath = './tuft_real_data/14Aug/'
    writePath = './tuft_real_data/24June/extractedFeatures/'
    slidingWindow = False
    timeseriesLength = 0.25
    #dataProcessor = processRealData("regression",timeseriesLength,readPath,writePath,slidingWindow) 
    dataProcessor = processRealData("classification",timeseriesLength,readPath,writePath,slidingWindow)
    dataProcessor.processFiles()