import tools
import numpy as np
import cudamat as cm
import Optimizer as Optimizer

def class NNet:

    def __init__(self, params):

        self.params = params
        self.optimizer = Optimizer(params)
        self.weights = []
        self.bias = []
        for pair in zip(layers[0:-1],layers[1:]):
            #create matrics and bias terms
        for W in weights:
            initializeWeights(W)
        for b in bias:
            initializeBias(b)
    
    def initializeWeights(W):

    def initializeBias(b):
        
    def getImage(im):

    def act(z):

    def der(z):

    def calculateCost(image, output):

    def forwardProp(image):

        activations = [image]
        inputs = []

        for W, b in zip(self.weights,self.bias):
            z = W*activations[-1] + b
            inputs.append(z)
            activations.append(act(z))

        output = activations[-1]
        cost = calculateCost(image,output)
        return [inputs, activations,cost]

    def backProp(inputs, activations):    

        output = activations.remove(-1)
        deltas = [-(output - image)*der(inputs[-1],output)]
        
        for i in range(1,len(weights)).reverse():
            deltas.insert(weights[i].T * deltas[0] .* der(inputs[i-1],activations[i]),0)
        for i in range(0,len(weights)):
            updateW = deltas[i]*a[i].T
            self.optimizer.updateWeight(weights[i],updateW)
            updateB = deltas[i]
            self.optimizer.updateBias(bias[i],updateB)

    def run():
        for epoch in self.epochs:
            for im in range(0,self.numImages):
                image = getImage(im)
                cost = prop(image)
                print "Iteration " + im + " Cost: " + cost
        
        
