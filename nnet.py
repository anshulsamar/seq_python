import numpy as np
import os
import pickle
import pdb
import dataLoader as dl
import view as view

class nnet(object):

    def __init__(self):

        # Network parameters
        self.units = 2048
        self.layers = 1
        self.imSize = 64*64
        self.alpha = 1e-3
        self.encLen = 4
        self.decLen = 4
        self.futLen = 4
        self.trainLen = 100
        self.epochs = 1
        self.currEpoch = 0
        self.currFile = 0
        scale1 = 1/np.sqrt(self.imSize)
        scale2 = 1/np.sqrt(self.units)

        # Encoder
        self.encOut = []
        self.encIn = [] 
        self.encInIm = []
        self.encInPast = [] 
        self.encImW = np.random.uniform(-scale1,scale1,(self.units,self.imSize))
        self.encW = np.random.uniform(-scale2,scale2,(self.units,self.units))
        self.encImB = np.zeros((self.units,1))

        # From Encoder -> Decoder/Future
        self.encDecW = np.random.uniform(-scale2,scale2,(self.units,self.units))
        self.decB = np.zeros((self.units,1))
        self.encFutW = np.random.uniform(-scale2,scale2,(self.units,self.units))
        self.futB = np.zeros((self.units,1))

        # Decoder
        self.decOut = []
        self.decIn = []
        self.decImIn = []
        self.decImOut = []
        self.decW = np.random.uniform(-scale2,scale2,(self.units,self.units))

        # Future
        self.futOut = []
        self.futIn = []
        self.futImIn = []
        self.futImOut = []
        self.futW = np.random.uniform(-scale2,scale2,(self.units,self.units))

        # Output image
        self.outImW = np.random.uniform(-scale2,scale2,(self.imSize,self.units))
        self.outImB = np.zeros((self.imSize,1))

        # Update and Loss
        self.updateEncImW = None
        self.updateEncImB = None
        self.updateEncW = None
        self.updateEncDecW = None
        self.updateEncFutW = None
        self.updateDecW = None
        self.updateDecB = None
        self.updateFutW = None
        self.updateFutB = None
        self.updateOutImW = None
        self.updateOutImB = None
        self.loss = []
        
        # Output and Data Files
        self.decOutFile = 'decode/decode.p'
        self.futOutFile = 'future/future.p'
        self.decFileHand = ''
        self.futFileHand = ''

        if (os.path.isfile(self.decOutFile)):
            os.remove(self.decOutfile)
        if (os.path.isfile(self.futOutFile)):
            os.remove(self.futOutFile)

        self.dataFile = 'data/data.p'
        self.numDataFiles = 3
        self.imPerFile = 96

        #Other
        self.epsilon = 1e-5

    def act(self,z):

        return 1/(1 + np.exp(-1 * z))

    def der(self,z):

        return self.act(z) * (1 - self.act(z))

    def cost(self,imTruth,imOut):

        cost = 0

        for i in range(0,np.shape(imTruth)[1]):
            norm = np.linalg.norm(imTruth[:,[i]] - imOut[:,[i]])
            cost = cost + 1.0/2 * np.square(norm)

        return cost

    def forwardProp(self,encImTruth,decImTruth,futImTruth,fileCount,write=True):

        # Encoder    
        self.encOut = np.zeros((self.units,self.encLen))
        self.encInIm = np.zeros((self.units,self.encLen))
        self.encInPast = np.zeros((self.units,self.encLen))
        self.encIn = np.zeros((self.units,self.encLen))


        for i in range(0,self.encLen):
            self.encInIm[:,[i]] = np.dot(self.encImW,encImTruth[:,[i]]) \
                                  + self.encImB
            self.encInPast[:,[i]] = np.dot(self.encW,self.encOut[:,[i-1]])
            self.encIn[:,[i]] = self.encInIm[:,[i]] + self.encInPast[:,[i]]
            self.encOut[:,[i]] = self.act(self.encIn[:,[i]])

        # Decoder
        if (self.decLen == 0):
            decLen = 1
        else:
            decLen = self.decLen
            
        self.decIn = np.zeros((self.units,decLen))
        self.decIn[:,[0]] = np.dot(self.encDecW,self.encOut[:,[-1]]) + self.decB
        self.decOut = np.zeros((self.units,decLen))
        self.decImIn = np.zeros((self.imSize,decLen))
        self.decImOut = np.zeros((self.imSize,decLen))

        for i in range(0,self.decLen):
            self.decOut[:,[i]] = self.act(self.decIn[:,[i]])
            weightedImage = np.dot(self.outImW,self.decOut[:,[i]])
            self.decImIn[:,[i]] =  weightedImage + self.outImB
            self.decImOut[:,[i]] = self.act(self.decImIn[:,[i]])
            if (i < self.decLen - 1):
                self.decIn[:,[i+1]] = np.dot(self.decW,self.decOut[:,[i]])

        # Future
        if (self.futLen == 0):
            futLen = 1
        else:
            futLen = self.futLen

        # Future
        self.futIn = np.zeros((self.units,futLen))
        self.futIn[:,[0]] = np.dot(self.encFutW,self.encOut[:,[-1]]) + self.futB
        self.futOut = np.zeros((self.units,futLen))
        self.futImIn = np.zeros((self.imSize,futLen))
        self.futImOut = np.zeros((self.imSize,futLen))

        for i in range(0,self.futLen):
            self.futOut[:,[i]] = self.act(self.futIn[:,[i]])
            weightedImage = np.dot(self.outImW,self.futOut[:,[i]])
            self.futImIn[:,[i]] = weightedImage + self.outImB
            self.futImOut[:,[i]] = self.act(self.futImIn[:,[i]])
            if (i < self.futLen - 1):
                self.futIn[:,[i+1]] = np.dot(self.futW,self.futOut[:,[i]])

        if (write):
            pickle.dump(self.decImOut,self.decFileHand)
            pickle.dump(self.futImOut,self.futFileHand)
      
    def backProp(self,encImTruth,decImTruth,futImTruth):

        # Decoder
        if (np.shape(decImTruth)[1] == 0):
            decImTruth = np.zeros((self.imSize,1))

        # Decoder
        if (self.decLen == 0):
            decLen = 1
        else:
            decLen = self.decLen

        delDec = np.zeros((self.units,decLen))
        delDecIm = np.zeros((self.imSize, decLen))
        diff = self.decImOut[:,[-1]] - decImTruth[:,[-1]]
        delDecIm[:,[-1]] = diff * self.der(self.decImIn[:,[-1]])
        delDec[:,[-1]] = np.dot(self.outImW.T,delDecIm[:,[-1]]) * \
                         self.der(self.decIn[:,[-1]])

        for i in range(0,self.decLen - 1)[::-1]:
            diff = self.decImOut[:,[i]] - decImTruth[:,[i]]
            delDecIm[:,[i]] = diff * self.der(self.decImIn[:,[i]])
            delFromIm = np.dot(self.outImW.T,delDecIm[:,[i]]) * \
                        self.der(self.decIn[:,[i]])
            delFromTime = np.dot(self.decW.T,delDec[:,[i+1]]) * \
                          self.der(self.decIn[:,[i]])
            delDec[:,[i]] = delFromTime + delFromIm


        # Future
        if (np.shape(futImTruth)[1] == 0):
            futImTruth = np.zeros((self.imSize,1))

        # Future
        if (self.futLen == 0):
            futLen = 1
        else:
            futLen = self.futLen

        # Future
        delFut = np.zeros((self.units,futLen))
        delFutIm = np.zeros((self.imSize, futLen))
        diff = self.futImOut[:,[-1]] - futImTruth[:,[-1]]
        delFutIm[:,[-1]] = diff * self.der(self.futImIn[:,[-1]])
        delFut[:,[-1]] = np.dot(self.outImW.T,delFutIm[:,[-1]]) * \
                         self.der(self.futIn[:,[-1]])


        for i in range(0,self.futLen - 1)[::-1]:
            diff = self.futImOut[:,[i]] - futImTruth[:,[i]]
            delFutIm[:,[i]] = diff * self.der(self.futImIn[:,[i]])
            delFromIm = np.dot(self.outImW.T,delFutIm[:,[i]]) * \
                        self.der(self.futIn[:,[i]])
            delFromTime = np.dot(self.futW.T,delFut[:,[i+1]]) * \
                          self.der(self.futIn[:,[i]])
            delFut[:,[i]] = delFromTime + delFromIm

        # Encoder
        delEnc = np.zeros((self.units, self.encLen))
        delEnc[:,[-1]] = (np.dot(self.encDecW.T,delDec[:,[0]]) + \
                              np.dot(self.encFutW.T,delFut[:,[0]])) * \
                              self.der(self.encIn[:,[-1]])
                             
        for i in range(0,self.encLen - 1)[::-1]:
            delEnc[:,[i]] = np.dot(self.encW.T,delEnc[:,[i+1]]) * \
                            self.der(self.encIn[:,[i]])
    
        # Encoder Update
        self.updateEncImW = np.dot(delEnc,encImTruth.T)
        self.encImW = self.encImW - self.alpha*self.updateEncImW

        self.updateEncImB = np.reshape(np.sum(delEnc,1),(self.units,1))
        self.encImB = self.encImB - self.alpha*self.updateEncImB

        self.updateEncW = np.dot(delEnc[:,1::],self.encOut[:,0:-1].T)
        self.encW = self.encW - self.alpha*self.updateEncW

        self.updateEncDecW = np.dot(delDec[:,[0]],self.encOut[:,[-1]].T)
        self.encDecW = self.encDecW - self.alpha*self.updateEncDecW

        self.updateEncFutW = np.dot(delFut[:,[0]],self.encOut[:,[-1]].T)
        self.encFutW = self.encFutW - self.alpha*self.updateEncFutW

        # Decoder Update
        self.updateDecW = np.dot(delDec[:,1::],self.decOut[:,0:-1].T)
        self.decW = self.decW - self.alpha*self.updateDecW

        self.updateDecB = delDec[:,[0]]
        self.decB = self.decB - self.alpha*self.updateDecB
        
        # Future Update
        self.updateFutW = np.dot(delFut[:,1::],self.futOut[:,0:-1].T)
        self.futW = self.futW - self.alpha*self.updateFutW

        self.updateFutB = delFut[:,[0]]
        self.futB = self.futB - self.alpha*self.updateFutB

        # Image Out Update
        self.updateOutImW = np.dot(delDecIm,self.decOut.T) \
                     + np.dot(delFutIm,self.futOut.T)
        self.outImW = self.outImW - self.alpha*self.updateOutImW

        self.updateOutImB = np.reshape(np.sum(delDecIm,1) + np.sum(delFutIm,1),\
                                       (self.imSize,1))
        self.outImB = self.outImB - self.alpha*self.updateOutImB


        #Update array
        self.update = [self.updateEncImW,self.updateEncImB, self.updateEncW,\
                       self.updateEncDecW,self.updateDecB,\
                       self.updateEncFutW,self.updateFutB,\
                       self.updateDecW,self.updateFutW,\
                       self.updateOutImW,self.updateOutImB]

    def gradCheck(self):

        #One epoch
        #self.train()
        
        #Data
        start = np.random.randint(0,self.imPerFile - self.encLen)
        f = np.random.randint(0,self.numDataFiles)
        self.trainSet = dl.loadTrainingSet(self,f)
        encImTruth = self.trainSet[:,start:start+self.encLen]
        decImTruth = self.trainSet[:,start:start+self.decLen][:,::-1]
        futImTruth = self.trainSet[:,\
            start+self.encLen:start+self.encLen+self.futLen]

        for checks in range(0,5):

            print "Check: #" + str(checks)
            print "-" * 50
            randRow = []
            randCol = []
            costPlus = []
            costMinus = []
            grad = []

            for (W,numRows,numCols) in \
                  [(self.encImW,self.units,self.imSize),\
                  (self.encImB,self.units,1),\
                  (self.encW,self.units,self.units),\
                  (self.encDecW,self.units,self.units),\
                  (self.decB,self.units,1),\
                  (self.encFutW,self.units,self.units),\
                  (self.futB,self.units,1),\
                  (self.decW,self.units,self.units),\
                  (self.futW,self.units,self.units),\
                  (self.outImW,self.imSize,self.units),\
                  (self.outImB,self.imSize,1)]:


                #Epsilon Matrix
                randRow.append(np.random.randint(0,numRows))
                randCol.append(np.random.randint(0,numCols))
        
                #Numerical grad calculation
                savedValue = W[randRow[-1],randCol[-1]]
                W[randRow[-1],randCol[-1]] += self.epsilon
                self.forwardProp(encImTruth,decImTruth,futImTruth,f,write=False)
                costPlus.append(self.cost(decImTruth,self.decImOut) +\
                       self.cost(futImTruth,self.futImOut))
                W[randRow[-1],randCol[-1]] = savedValue

                W[randRow[-1],randCol[-1]] -= self.epsilon
                self.forwardProp(encImTruth,decImTruth,futImTruth,f,write=False)
                costMinus.append(self.cost(decImTruth,self.decImOut) +\
                        self.cost(futImTruth,self.futImOut))
                grad.append((costPlus[-1] - costMinus[-1])/(2*self.epsilon))
                W[randRow[-1],randCol[-1]] = savedValue

            #Backprop Grad Calculation
            self.forwardProp(encImTruth,decImTruth,futImTruth,0,write=False)
            self.backProp(encImTruth, decImTruth, futImTruth)
            cost = self.cost(decImTruth,self.decImOut) +\
                   self.cost(futImTruth,self.futImOut)

            for i in range(0,len(randRow)):
                
                backPropGrad = self.update[i][randRow[i],randCol[i]]
                diff = np.absolute(grad[i] - backPropGrad)
                sumGrad = np.absolute(grad[i]) + np.absolute(backPropGrad)
                weightedDiff = diff/sumGrad

                if (weightedDiff > 1e-6):
                    print "\033[1;31mNum: %2.6f BP: %2.6f Diff: %.2e WDiff: %.2e\033[0m" % \
                  (grad[i],backPropGrad,diff,weightedDiff)
                else:
                    print "Num: %2.6f BP: %2.6f Diff: %.2e WDiff: %.2e" % \
                  (grad[i],backPropGrad,diff,weightedDiff)

    def saveNN(self):

        NNFileHand = open(self.NNFile + '.p','w')
        for W in [self.encImW,self.encImB,self.encW,\
                  self.encDecW,self.decB,self.encFutW,self.futB,\
                  self.decW, self.futW,self.outImW,self.outImB]:
            pickle.dump(W,NNFileHand)

        pickle.dump(self.currEpoch,NNFileHand)
        NNFileHand.close()

    def loadNN(self):

        NNFileHand = open(self.NNFile + '.p','w')
        self.encImW = pickle.load(NNFileHand)
        self.encImB = pickle.load(NNFileHand)
        self.encW = pickle.load(NNFileHand)
        self.encDecW = pickle.load(NNFileHand)
        self.decB = pickle.load(NNFileHand)
        self.encFutW = pickle.load(NNFileHand)
        self.futB = pickle.load(NNFileHand)
        self.decW = pickle.load(NNFileHand)
        self.futW = pickle.load(NNFileHand)
        self.outImW = pickle.load(NNFileHand)
        self.outImB = pickle.load(NNFileHand)
        self.currEpoch = pickle.load(NNFileHand)

    def train(self):

        totalCostDec = 0
        totalCostFut = 0
        imageCount = 0

        for f in range(0,self.numDataFiles):
            iteration = 0
            start = 0
            self.trainSet = dl.loadTrainingSet(self,f)
            self.decFileHand = open(self.decOutFile[:-2] + str(f) + '.p','w')
            self.futFileHand = open(self.futOutFile[:-2] + str(f) + '.p','w')

            while (start <= self.imPerFile - self.encLen):

                encImTruth = self.trainSet[:,start:start+self.encLen]
                decImTruth = self.trainSet[:,start:start+self.decLen][:,::-1]
                futStart = start + self.encLen
                futEnd = start + self.encLen + self.futLen
                futImTruth = self.trainSet[:,futStart:futEnd]
                self.forwardProp(encImTruth,decImTruth,futImTruth,f,write=True)
                costDec = self.cost(decImTruth,self.decImOut)
                costFut = self.cost(futImTruth,self.futImOut)
                totalCostDec += costDec
                totalCostFut += costFut
                imageCount += 1
                print "Epoch: %02d, File: %02d, Iter: %04d, Dec: %2.2f, Fut: %2.2f, ADec: %2.2f, AFut: %2.2f" % \
                    (self.currEpoch, f, iteration, costDec, costFut, \
                     totalCostDec/imageCount, totalCostFut/imageCount)
                self.backProp(encImTruth, decImTruth, futImTruth)
                start += 1
                iteration += 1

            self.decFileHand.close()
            self.futFileHand.close()
            self.decFileHand = ""
            self.futFileHand = ""
            self.trainSet = []

        
