#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 11:43:19 2023

@author: Erik Mårtensson
"""

# import
from estimator.estimator import *
import matplotlib.pyplot as plt
import math


def getSecurityLevels():
    Logging.set_level(Logging.LEVEL0)

    #Kyber512
    nValues = list(range(132, 512 + 1)) # Below n = 132, the estimation of Kyber512 breaks down
    parameters = schemes.Kyber512
    
    #Kyber768/Kyber1024
#    nValues = list(range(140, 1024 + 1)) # Below n = 140, the estimation of Kyber768/Kyber1024 breaks down
#    parameters = schemes.Kyber1024
    
    securityLevels = [0]*len(nValues)

    for k in range(len(nValues)):
        parameters.n = nValues[k]
        securityLevels[k] = LWE.primal_bdd(parameters, red_shape_model="gsa")['rop'].log2()
        

def getPostProcessingCost(securityLevels, lowestN, k):
    index = max(0, k - lowestN)
    return 2**securityLevels[index]

def queryCost(numQueries, costPerKey, p):
    return numQueries*costPerKey*2**(p - 1)

def totalCost(securityLevels, lowestN, k, numQueries, costPerKey, p):
    return queryCost(numQueries, costPerKey, p) + getPostProcessingCost(securityLevels, lowestN, k)

# Pairwise - only multiples of 5 for Kyber768 and Kyber1024 (no improvement for Kyber512)
# Adaptive - use data from the implementation work 

# The most basic version - non-adaptive only
def optimizeCostOnePositionParallel(securityLevels, lowestN, numQueries, costPerKey, l):
    if numQueries == 0:
        return 2**securityLevels[l*256-lowestN]
    numQueries = math.floor(numQueries/3)*3 # Queries need to come in multiples of 3 for this type of approach
    p = 1
    lowestCost = 2**300 # Arbitrary value higher than the cost of breaking Kyber1024 with lattice reduction
    while 1:
        cost = totalCost(securityLevels, lowestN, l*256 - int(numQueries/3*p), numQueries, costPerKey, p)
        if cost < lowestCost:
            lowestCost = cost
        p = p + 1
        if math.ceil(numQueries/3/l)*p > 256:
            break
        
    return lowestCost

# The pairwise version - Kyber768 and Kyber1024 only
def optimizeCostPairwiseParallel(securityLevels, lowestN, numQueries, costPerKey, l):
    if numQueries == 0:
        return 2**securityLevels[l*256-lowestN]
    numQueries = math.floor(numQueries/5)*5 # Queries need to come in multiples of 5 for this type of approach
    p = 1
    lowestCost = 2**300 # Arbitrary value higher than the cost of breaking Kyber1024 with lattice reduction
    while 1:
        cost = totalCost(securityLevels, lowestN, l*256 - int(numQueries/5*p*2), numQueries, costPerKey, p)
        if cost < lowestCost:
            lowestCost = cost
        p = p + 1
        if p > 128 or math.ceil(numQueries/5/l)*2*p > 256:
            break
    return lowestCost

# Optimizing Kyber512 mismatch + postprocessing attacks
def optimizeCostParallelAllKyber512(securityLevels, lowestN, numQueries, costPerKey):
    lowestCost = 2**300 # Arbitrary value higher than the cost of breaking Kyber1024 with lattice reduction
    if numQueries <= 1:
        return 2**securityLevels[512-lowestN]
    if numQueries == 2:
        for p in range(1, 128 + 1):
            r = round(35/64 * p) # 35/64 of all entries will be 0 or -1 => recovered in 2 queries
            cost = totalCost(securityLevels, lowestN, 512 - r, numQueries, costPerKey, p)
            if cost < lowestCost:
                lowestCost = cost
        return lowestCost
    if numQueries == 3:
        return optimizeCostOnePositionParallel(securityLevels, lowestN, numQueries, costPerKey, 2)
    
    lowestCost = optimizeCostOnePositionParallel(securityLevels, lowestN, numQueries, costPerKey, 2) # Non-adaptive as baseline
    # From running simulations we have these numbers
    coeffPerQuery512Partial = [0.390722, 0.780761, 1.169541, 1.558025, 1.945332, 2.332215, 2.717417, 3.101606, 3.485747, 3.869395, 4.252483, 4.631852, 5.012065, 5.394588, 5.773993, 6.150142, 6.528968, 6.901181, 7.278002, 7.652135, 8.022711, 8.396816, 8.771105, 9.144193, 9.513179, 9.879402, 10.252483, 10.617063, 10.983543, 11.347492, 11.7087, 12.069853, 12.435287, 12.792591, 13.147202, 13.508224, 13.86409, 14.219782, 14.577415, 14.918119, 15.301023, 15.627961, 15.978013, 16.35761, 16.683569, 17.036332, 17.410217, 17.724328, 18.046867, 18.446339, 18.800234, 19.089167, 19.40536, 19.796665, 20.173864, 20.470768, 20.748429, 21.099, 21.467018, 21.836871, 22.14555, 22.379678, 22.716199, 23.084216, 23.460927, 23.813946, 24.094922, 24.330735, 24.6475, 24.99, 25.353458, 25.724, 26.064994, 26.367125, 26.586857, 26.831286, 27.114286, 27.458571, 27.802143, 28.154176, 28.532418, 28.868443, 29.202189, 29.434423, 29.626026, 29.869808, 30.165833, 30.504167, 30.850833, 31.198333, 31.535, 31.874091, 32.227045, 32.557, 32.749394, 32.913515, 33.034697, 33.105273, 33.319545, 33.613818, 33.943, 34.293, 34.608, 34.929, 35.258, 35.586, 35.914111, 36.248444, 36.566722, 36.802528, 37.049917, 37.155917, 37.275444, 37.340417, 37.565, 37.861806, 38.176111, 38.4625, 38.80625, 39.14, 39.46625, 39.795, 40.14625, 40.44125, 40.7625, 41.105, 41.41125, 41.70875]
    p = 1
    while 1:
        r = round(coeffPerQuery512Partial[p - 1]*numQueries) # We recover this many positions
        cost = totalCost(securityLevels, lowestN, 512 - r, numQueries, costPerKey, p)
        if cost < lowestCost:
            lowestCost = cost
        p = p + 1
        if p > 128 or round(coeffPerQuery512Partial[p - 1])/2*numQueries > 256 - p: # Fix this line!
            break
    return lowestCost

# Optimizing Kyber768 mismatch + postprocessing attacks
def optimizeCostParallelAllKyber768(securityLevels, lowestN, numQueries, costPerKey):
    lowestCost = 2**300 # Arbitrary value higher than the cost of breaking Kyber1024 with lattice reduction
    if numQueries <= 1:
        return 2**securityLevels[768-lowestN]
    if numQueries == 2:
        for p in range(1, 192 + 1):
            r = round(5/8 * p) # 5/8 of all entries will be 0 or -1 => recovered in 2 queries
            cost = totalCost(securityLevels, lowestN, 768 - r, numQueries, costPerKey, p)
            if cost < lowestCost:
                lowestCost = cost
        return lowestCost
    if numQueries == 3:
        return optimizeCostOnePositionParallel(securityLevels, lowestN, numQueries, costPerKey, 3)
    
    lowestCost = optimizeCostPairwiseParallel(securityLevels, lowestN, numQueries, costPerKey, 3) # Non-adaptive as baseline
    # From running simulations we have these numbers
    coeffPerQuery768Partial = [0.432415, 0.863906, 1.294588, 1.724323, 2.153202, 2.581018, 3.008038, 3.433501, 3.858778, 4.283477, 4.708003, 5.13051, 5.549369, 5.971497, 6.389146, 6.809949, 7.225495, 7.64335, 8.052764, 8.475521, 8.882101, 9.295771, 9.70979, 10.120273, 10.536133, 10.943416, 11.344974, 11.746365, 12.150143, 12.572548, 12.956088, 13.365789, 13.765325, 14.15402, 14.562926, 14.949109, 15.346808, 15.763608, 16.116877, 16.559125, 16.920831, 17.296104, 17.732295, 18.095373, 18.467222, 18.898558, 19.282007, 19.612594, 20.00161, 20.446684, 20.812303, 21.121462, 21.512667, 21.9214, 22.348244, 22.672872, 22.998777, 23.372593, 23.769259, 24.200541, 24.577591, 24.838682, 25.139467, 25.52875, 25.92125, 26.311178, 26.746781, 27.123825, 27.42437, 27.742944, 28.096667, 28.502857, 28.895714, 29.278095, 29.674048, 30.061023, 30.359202, 30.531231, 30.713509, 31.058743, 31.435556, 31.832222, 32.202778, 32.577778, 32.971667, 33.356111, 33.76393, 34.057141, 34.160177, 34.301125, 34.646, 35.043333, 35.427333, 35.811333, 36.216667, 36.594, 36.988, 37.354667, 37.740667, 38.138095, 38.52481, 38.876907, 39.144791, 39.258833, 39.314504, 39.286612, 39.490714, 39.799487, 40.120192, 40.471667, 40.844167, 41.204167, 41.574167, 41.9525, 42.310833, 42.6775, 43.053333, 43.433333, 43.7925, 44.17, 44.545, 44.8975, 45.2625, 45.639167, 46.0125, 46.395, 46.753333, 47.116667, 43, 43.333333, 43.666667, 44, 44.333333, 44.666667, 45, 45.333333, 45.666667, 46, 46.333333, 46.666667, 47, 47.333333, 47.666667, 48.02125, 48.453333, 48.873333, 49.31375, 49.8325, 50.391071, 51.014405, 51.591964, 52.19244, 52.750655, 53.145595, 53.4925, 53.760893, 54.021905, 54.311905, 54.607619, 54.944524, 55.223333, 55.571667, 55.891667, 56.238333, 56.591667, 56.923333, 57.265, 57.616667, 57.93, 58.301667, 58.646667, 59.006667, 59.338333, 59.701667, 60.053333, 60.403333, 60.75, 61.116667, 61.458333, 61.791667, 62.135, 62.475, 62.835, 63.198333, 63.533333, 63.89, 64.243333, 64.591667, 64.953333, 65.3, 65.626667, 65.978333]
    p = 1
    while 1:
        r = round(coeffPerQuery768Partial[p - 1]*numQueries) # We recover this many positions
        cost = totalCost(securityLevels, lowestN, 768 - r, numQueries, costPerKey, p)
        if cost < lowestCost:
            lowestCost = cost
        p = p + 1
        if p > 192 or round(coeffPerQuery768Partial[p - 1])/3*numQueries > 256 - p: # Fix this line!
            break
    return lowestCost
    
# Optimizing Kyber768 mismatch + postprocessing attacks
def optimizeCostParallelAllKyber1024(securityLevels, lowestN, numQueries, costPerKey):
    lowestCost = 2**300 # Arbitrary value higher than the cost of breaking Kyber1024 with lattice reduction
    if numQueries <= 1:
        return 2**securityLevels[1024-lowestN]
    if numQueries == 2:
        for p in range(1, 256 + 1):
            r = round(5/8 * p) # 5/8 of all entries will be 0 or -1 => recovered in 2 queries
            cost = totalCost(securityLevels, lowestN, 1024 - r, numQueries, costPerKey, p)
            if cost < lowestCost:
                lowestCost = cost
        return lowestCost
    if numQueries == 3:
        return optimizeCostOnePositionParallel(securityLevels, lowestN, numQueries, costPerKey, 4)
    
    lowestCost = optimizeCostPairwiseParallel(securityLevels, lowestN, numQueries, costPerKey, 4) # Non-adaptive as baseline
    # From running simulations we have these numbers
    coeffPerQuery1024Partial = [0.432595, 0.864265, 1.295136, 1.725118, 2.153975, 2.582342, 3.0094, 3.435083, 3.860424, 4.2852, 4.710061, 5.132144, 5.552557, 5.974396, 6.393584, 6.812665, 7.22941, 7.647182, 8.057262, 8.477859, 8.886099, 9.302002, 9.715358, 10.125747, 10.539873, 10.949017, 11.348717, 11.749529, 12.1586, 12.577975, 12.960981, 13.373972, 13.773659, 14.16366, 14.572617, 14.963529, 15.358494, 15.773211, 16.135163, 16.571421, 16.932145, 17.313697, 17.746923, 18.108732, 18.480417, 18.913658, 19.289453, 19.631222, 20.024434, 20.462384, 20.819759, 21.140999, 21.53575, 21.951146, 22.373818, 22.685915, 23.016242, 23.396944, 23.804167, 24.229365, 24.598576, 24.855872, 25.176714, 25.560938, 25.942812, 26.341169, 26.784715, 27.150387, 27.439753, 27.751527, 28.111071, 28.520714, 28.910357, 29.296786, 29.691349, 30.079505, 30.376967, 30.559864, 30.749183, 31.08925, 31.46375, 31.861667, 32.240417, 32.615833, 33.00625, 33.381667, 33.792187, 34.076392, 34.169137, 34.341, 34.663, 35.059, 35.4345, 35.8295, 36.224, 36.6045, 36.99, 37.3615, 37.7465, 38.146357, 38.538637, 38.902151, 39.172721, 39.26951, 39.335857, 39.33627, 39.55548, 39.85364, 40.186838, 40.55, 40.921875, 41.288125, 41.66, 42.0375, 42.3925, 42.761875, 43.13625, 43.511875, 43.868125, 44.24875, 44.6275, 44.98375, 45.3475, 45.723125, 46.09125, 46.47125, 46.83125, 47.200625, 43, 43.333333, 43.666667, 44, 44.333333, 44.666667, 45, 45.333333, 45.666667, 46, 46.333333, 46.666667, 47, 47.333333, 47.666667, 48.015455, 48.420606, 48.830303, 49.276909, 49.804545, 50.34901, 50.993508, 51.645833, 52.263566, 52.807957, 53.226518, 53.57926, 53.860333, 54.130619, 54.431389, 54.725972, 55.07125, 55.37125, 55.71375, 56.05, 56.38875, 56.745, 57.08625, 57.42625, 57.7825, 58.1025, 58.47375, 58.81125, 59.17375, 59.505, 59.86125, 60.22125, 60.57, 60.915, 61.2775, 61.6325, 61.97, 62.3125, 62.64375, 62.99625, 63.35875, 63.69125, 64.0375, 64.405, 64.76625, 65.12, 65.46625, 65.795, 66.14875, 66.47875, 66.84625, 67.18875, 67.53375, 67.8775, 68.235, 68.58625, 68.925, 69.25875, 69.605, 69.94625, 70.3075, 70.6525, 70.99, 71.33, 71.6825, 72.03375, 72.3675, 72.7475, 73.07125, 73.40625, 73.77, 74.1075, 74.445, 74.80375, 75.1675, 75.49625, 75.83625, 76.165, 76.49375, 76.83375, 77.17, 77.51625, 77.8575, 78.18375, 78.525, 78.85875, 79.19625, 79.525, 79.8625, 80.22, 80.5675, 80.92, 81.25625, 81.60375, 81.935, 82.275, 82.605, 82.9475, 83.2825, 83.61625, 83.965, 84.32625, 84.685, 85.0375, 85.38125, 85.74, 86.06625, 86.3925, 86.7425, 87.09125, 87.43125, 87.76, 88.1]
    p = 1
    while 1:
        r = round(coeffPerQuery1024Partial[p - 1]*numQueries) # We recover this many positions
        cost = totalCost(securityLevels, lowestN, 1024 - r, numQueries, costPerKey, p)
        if cost < lowestCost:
            lowestCost = cost
        p = p + 1
        if p > 256 or round(coeffPerQuery1024Partial[p - 1])/4*numQueries > 256 - p: # Fix this line!
            break
    return lowestCost

# Constants for the different Kyber versions
KYBER512 = 0
KYBER768 = 1
KYBER1024 = 2

# Choose a version of Kyber
# kyberVersion = KYBER512
# kyberVersion = KYBER768
kyberVersion = KYBER1024

# Use pre-computed costs of post-processing with a certain number of positions for different versions of Kyber
# To compute these numbers use the function getSecurityLevels() above
if kyberVersion == KYBER512:
    nValues = list(range(132, 512 + 1)) # The cost model breaks down when post-processing with less than 132 positions for Kyber512
    securityLevels = [41.8814518664410, 42.1580763243877, 42.4379383540005, 42.7561672688905, 43.1773365053692, 43.4816788367421, 43.8916029663479, 44.1872131045975, 44.4819704005920, 44.7788735052714, 45.0750338212157, 45.3956025310114, 45.6827632931993, 45.9693035404145, 46.2517712446026, 46.5337031954381, 46.8151408708840, 47.0644814557715, 47.3387695670860, 47.6156324520061, 47.9107245334047, 48.1846470487001, 48.4375757751267, 48.7055643572194, 48.9267999072602, 49.1923397361600, 49.4556003803735, 49.7224874520702, 49.9945440760635, 50.2277456570876, 50.4915169993003, 50.7238310444749, 50.9890393216599, 51.2693542410537, 51.5246026971686, 51.7338529076764, 51.9945871878960, 52.2470922451125, 52.5125823567124, 52.7506513601680, 53.0099761471998, 53.2361321134378, 53.5108132509281, 53.7720970073770, 53.9784169544889, 54.2355487693487, 54.4789213763243, 54.7439067514415, 54.9852102581361, 55.2475132042796, 55.4653749215701, 55.7301612468609, 55.9959159731198, 56.2019610148005, 56.4619240948700, 56.7011006161009, 56.9593134997984, 57.2118972027639, 57.4241872041499, 57.6852019994887, 57.9464980978050, 58.1682057493170, 58.4222718860006, 58.6559560336089, 58.9418310907799, 59.1703693361641, 59.3835250854503, 59.6390999822128, 59.8954890558875, 60.1610756638538, 60.3776079546461, 60.6091924129505, 60.8688868056573, 61.1332806353736, 61.3893914794028, 61.5943508064124, 61.8457331579485, 62.1090989661357, 62.3374218285794, 62.5948183046707, 62.8212448780603, 63.0955532940714, 63.3480771046707, 63.5512305613794, 63.8126620232325, 64.0587796324941, 64.3245340426814, 64.5538511076639, 64.7753463105570, 65.0379038041147, 65.3147768912576, 65.5739430706635, 65.7663523606928, 66.0124961048217, 66.2739519459590, 66.5204104937587, 66.7728766556778, 66.9917184324945, 67.2603312900013, 67.5231459824280, 67.7899596673109, 67.9866924174746, 68.2275669904811, 68.4914493186411, 68.7418068679663, 68.9974480385227, 69.2129930677958, 69.4762220002235, 69.7392410513647, 70.0082329940975, 70.2122460655681, 70.4472684800299, 70.7135679651284, 70.9740417006363, 71.2247555887214, 71.4367804420366, 71.6963958589128, 71.9596650709586, 72.2288226701709, 72.4403867198479, 72.6736919656215, 72.9359282974145, 73.2186042067702, 73.4574543048868, 73.6676971494126, 73.9289695302999, 74.1843477207488, 74.4517403552699, 74.6784459139680, 74.9363791489678, 75.1649796099238, 75.4431351165308, 75.7096614885468, 75.9574684351963, 76.1603179212770, 76.4150701427553, 76.6769639626399, 76.9464862499064, 77.1747253431255, 77.4354480126520, 77.6612160797335, 77.9382399925344, 78.2049918090481, 78.4631668553009, 78.6626668018261, 78.9138524584613, 79.1760649326719, 79.4457884258088, 79.7155037972125, 79.9423268634523, 80.1643309727749, 80.4375041470857, 80.7027982911805, 80.9743090795041, 81.1764964450738, 81.4344478371813, 81.6795696216107, 81.9476422660537, 82.2175667416450, 82.4566258035288, 82.7181056284398, 82.9375264060024, 83.2063877136024, 83.4752878632977, 83.7538998511269, 83.9511122604680, 84.2116134317718, 84.4538135811393, 84.7221187666799, 84.9940968170488, 85.2398754270439, 85.5017627342515, 85.7177105376645, 85.9830172503504, 86.2504895770040, 86.5229233292501, 86.7936971556089, 86.9960984426180, 87.2344871744313, 87.5030481389989, 87.7734038590932, 88.0455739202117, 88.2929039124833, 88.5045799371291, 88.7706661348647, 89.0315971001929, 89.3025797613453, 89.5735599566669, 89.8461820710731, 90.0550756149271, 90.2901463481789, 90.5571821024906, 90.8295444990210, 91.1019116489979, 91.3560058790529, 91.5680274300349, 91.8306276323895, 92.0879556565500, 92.3575437027090, 92.6303482459869, 92.9031589683339, 93.1212442646954, 93.3539278573370, 93.6177886804111, 93.9009917591309, 94.1713463357927, 94.4445853075989, 94.6939268145361, 94.8991364577431, 95.1580355545973, 95.4200348538710, 95.6914493633918, 95.9628616785270, 96.2358655006472, 96.4643650754615, 96.7285090067956, 96.9556152088114, 97.2351003462812, 97.5056871516983, 97.7776899974083, 98.0511207497258, 98.3072156323775, 98.5079805162340, 98.7597748377168, 99.0298637838441, 99.3015014772931, 99.5747023339995, 99.8479089674907, 100.080953435618, 100.308146164218, 100.571063797246, 100.845590358391, 101.116409340211, 101.390026473240, 101.663650456361, 101.932512201141, 102.131247668703, 102.378676766263, 102.645980041167, 102.917847673357, 103.191250932221, 103.464659741839, 103.738074043549, 103.975495547536, 104.196295587358, 104.462883052173, 104.734291321399, 105.006725249052, 105.280540718266, 105.554362708469, 105.839516161487, 106.103895464370, 106.298233430325, 106.541693168956, 106.813798552969, 107.085901780804, 107.359516807592, 107.634652543502, 107.909797877502, 108.152171640680, 108.367900668101, 108.635683158550, 108.904303031892, 109.176963558614, 109.450983234521, 109.725009079318, 110.000403500591, 110.289271695824, 110.481338326813, 110.720256655052, 110.989663639948, 111.262010725012, 111.535840565906, 111.811161755348, 112.085004344896, 112.360342466829, 112.611160406043, 112.824693125384, 113.091989182920, 113.355884633192, 113.628780307355, 113.903010916852, 114.177247338907, 114.452827822621, 114.727078053549, 115.004016134812, 115.214693463516, 115.450085754524, 115.719795566116, 115.993847061480, 116.267903229297, 116.543422224056, 116.817490384203, 117.093025413279, 117.368569072132, 117.624205852183, 117.832813715552, 118.091883712585, 118.362417504505, 118.636864212410, 118.911316379880, 119.185773961891, 119.461551704012, 119.737338075246, 120.013133044873, 120.240721124147, 120.504540050140, 120.736578337870, 121.009444955096, 121.282309197222, 121.558028793733, 121.833756618918, 122.109492642162, 122.385236832949, 122.660989160864, 122.936749595588, 123.197645248588, 123.401086103398, 123.655329020042, 123.928722793647, 124.203401663756, 124.478085572870, 124.754063102696, 125.030048775759, 125.306042563442, 125.583334963452, 125.859345916333, 126.087543385442, 126.313066784371, 126.590649330636, 126.863418348365, 127.137331149990, 127.412395479566, 127.688616394487, 127.964845372907, 128.241082387961, 128.517327412883, 128.793580421008, 129.070995401358, 129.333896552554, 129.533242786310, 129.783165102342, 130.056829287788, 130.331751980158, 130.607939346046, 130.884134360895, 131.160336998369, 131.436547232230, 131.712765036338, 131.990254241327, 132.266488095077, 132.543994166316, 132.776539063589, 132.998213199676, 133.270750727192, 133.546050677265, 133.821355824292, 134.096666134689, 134.373109781302, 134.649560938882, 134.926019583030, 135.203615310314, 135.480089622824, 135.757701622724, 136.034191511312, 136.314396098777, 136.508838333124, 136.752318133162, 137.026274933197, 137.301460348161, 137.577880280937, 137.854307323908, 138.130741453271, 138.407182645309, 138.683630876394, 138.961320095957, 139.237783282816, 139.515488253421, 139.793201013661, 140.069686944003, 140.318015243517]
elif kyberVersion == KYBER768 or kyberVersion == KYBER1024: # Kyber768/Kyber1024
    nValues = list(range(140, 1024 + 1)) # The cost model breaks down when post-processing with less than 132 positions for Kyber768/Kyber1024
    securityLevels = [42.0192239011371, 42.3166801190003, 42.6136226589466, 42.9251980465571, 43.3408394561864, 43.6413018822815, 43.9435629134200, 44.2840966346118, 44.6326144138669, 44.9196244397220, 45.2059601781097, 45.4369282398042, 45.7138823542522, 45.9935705562915, 46.2387469112890, 46.5145072809098, 46.8066621487137, 47.0796471981659, 47.3323062867768, 47.5981925618279, 47.8103430661077, 48.0741736528813, 48.3397875158210, 48.6103557838295, 48.8334049513836, 49.0635882638196, 49.3271392108544, 49.5927637225781, 49.8025256968911, 50.0582660707098, 50.3096873602902, 50.5458348631480, 50.7996965404386, 51.0213680242778, 51.2936885234417, 51.5582022268708, 51.7464438307151, 51.9920108574888, 52.2310385601724, 52.4809813358166, 52.7012135746840, 52.9661158629651, 53.1688049078389, 53.4202530804809, 53.6595148807182, 53.8951589385802, 54.1099158384728, 54.3686255000577, 54.6281624572525, 54.8273271243299, 55.0642678349159, 55.3097869971917, 55.5594763911779, 55.7693784891299, 56.0269605371588, 56.2323113854168, 56.4672197796824, 56.7219656480458, 56.9625284925702, 57.1685749863154, 57.4221094583654, 57.6386011553207, 57.8900477273603, 58.1160192895492, 58.3641278474088, 58.5693073963537, 58.8209083929923, 59.0774421071402, 59.2864308847490, 59.5117418240602, 59.7676823666275, 59.9690192912839, 60.2223027527802, 60.4686940381003, 60.6849067866797, 60.9067551355913, 61.1702199026914, 61.4206412402343, 61.6161113839321, 61.8617607993985, 62.0855287709234, 62.3036824197780, 62.5744812735701, 62.8289141955189, 63.0147746889315, 63.2544434094079, 63.4882994378253, 63.7406176581755, 63.9555613578594, 64.2198909226421, 64.4129392224031, 64.6512824878459, 64.9083680618903, 65.1376009974212, 65.3519312851507, 65.6127171527096, 65.8209485642173, 66.0675054122652, 66.3029712197833, 66.5397559184931, 66.7503962358696, 67.0113486455376, 67.2663652710242, 67.4652717754271, 67.6995764682623, 67.9614151894402, 68.1974132417732, 68.4047376155752, 68.6611461157468, 68.8728345144725, 69.1251019261510, 69.3559092386914, 69.6018208015211, 69.8076749147983, 70.0616740337250, 70.3191139146879, 70.5276682757245, 70.7545943092100, 71.0335038212909, 71.2623684264778, 71.4647076055953, 71.7158927744053, 71.9793190367491, 72.1877572983638, 72.4134718819918, 72.6894106130451, 72.9257976441580, 73.1266320466858, 73.3762454890725, 73.6045960023331, 73.8530386594972, 74.0768671892551, 74.3401374335017, 74.5406205570286, 74.7911087034712, 75.0388304111032, 75.2650051234198, 75.4879816223663, 75.7405473326416, 76.0063201658157, 76.2028553841063, 76.4580986479470, 76.7017342697189, 76.9328511498911, 77.1537140228321, 77.4065907925914, 77.6777524744144, 77.8741538328251, 78.1253381336204, 78.3687162038574, 78.6347152825345, 78.8575041446903, 79.0749496633618, 79.3424548448722, 79.6048897183647, 79.7972113751121, 80.0359750527570, 80.3021526733680, 80.5307892849349, 80.7455654500815, 81.0086493374441, 81.2757903447232, 81.4692553484899, 81.7071718189791, 81.9717142887049, 82.2087852160881, 82.4203433070216, 82.6801091260047, 82.9441235942258, 83.1499377445575, 83.3839620666876, 83.6415278499935, 83.9098631471096, 84.1465726159867, 84.3552356262975, 84.6143834232034, 84.8818396754526, 85.0832451120699, 85.3169669921723, 85.5818983644392, 85.8293966819520, 86.0363479543816, 86.2913575639432, 86.5541544394106, 86.8217643044956, 87.0255191781709, 87.2559234773298, 87.5228055645298, 87.7725079329881, 87.9760814553520, 88.2298877548646, 88.4944735387950, 88.7638567922509, 88.9703651824958, 89.1989608168467, 89.4790977776846, 89.7182962405344, 89.9201562412962, 90.1721652756722, 90.4385355962184, 90.7080701802564, 90.9177154488006, 91.1442390616377, 91.4222741439711, 91.6688325360051, 91.8684557501453, 92.1181020688917, 92.3830807980576, 92.6527643287437, 92.8695002094738, 93.0916992350910, 93.3673695366516, 93.6281471159066, 93.8245119839779, 94.0706886175362, 94.3312339847822, 94.5995063529660, 94.8235726798226, 95.0446661004968, 95.3157386728115, 95.5834700433951, 95.8386686403863, 96.0350797573907, 96.2813367894200, 96.5482397077981, 96.8197789220437, 97.0423629100484, 97.2607200839492, 97.5324193282058, 97.8016982266318, 98.0604045892728, 98.2424330850559, 98.5004373999661, 98.7690449852948, 99.0068162418246, 99.2211493490835, 99.4872608614535, 99.7525833338086, 100.028985271394, 100.218225166923, 100.457477720842, 100.721741557515, 100.992032571602, 101.230541035864, 101.443361398992, 101.707909715970, 101.974780669309, 102.259735420115, 102.445047620771, 102.682221942937, 102.946701220769, 103.217145711986, 103.489092740516, 103.672679477787, 103.933258830163, 104.198961462410, 104.470058004944, 104.747564757084, 104.936704773064, 105.173723943081, 105.442831162143, 105.714912889558, 105.952618346432, 106.164630113368, 106.426416497965, 106.696313019567, 106.967544850671, 107.170014298288, 107.404215453680, 107.672031339592, 107.942772460110, 108.194784558820, 108.399926681801, 108.657042739053, 108.924446199577, 109.195822854528, 109.468534142993, 109.671866634480, 109.904627216699, 110.174073072160, 110.446430632916, 110.695743945041, 110.901339947504, 111.157033991717, 111.425923977025, 111.698765451045, 111.971607285675, 112.177855405637, 112.408690308504, 112.678301536205, 112.950795398960, 113.204636592826, 113.406615460097, 113.661701380285, 113.930762288194, 114.202421765591, 114.475390954959, 114.686178319989, 114.914874669066, 115.184654219168, 115.457285172761, 115.729914132884, 115.920231771206, 116.169621397553, 116.437568661307, 116.709373500472, 116.982473691608, 117.201692591848, 117.425930796594, 117.703162269280, 117.973235740330, 118.246795827292, 118.499451719280, 118.697719566765, 118.947562538541, 119.218234600885, 119.490178026896, 119.763405987832, 119.983320271062, 120.206266036070, 120.483334528253, 120.754711598384, 121.028394957460, 121.283842296491, 121.480651100018, 121.730211955081, 122.001034871536, 122.274393831154, 122.547752719922, 122.770638123746, 122.991615581945, 123.266649583257, 123.538170394583, 123.811976365274, 124.075855781794, 124.270363243754, 124.516188956784, 124.787169583313, 125.059396729384, 125.334148828593, 125.565035050354, 125.781824944131, 126.053020873346, 126.324690367287, 126.597484735289, 126.871414186001, 127.068060278801, 127.306628703408, 127.575291656467, 127.847663553887, 128.121280294832, 128.396151181208, 128.626365063749, 128.845697086701, 129.113057730652, 129.385988549206, 129.660041649454, 129.934096129452, 130.129174045919, 130.369022027819, 130.639088100993, 130.911601708386, 131.186587332133, 131.460336373876, 131.694874981119, 131.907636784722, 132.177391882035, 132.449344427908, 132.723519204758, 132.998813509566, 133.201269405661, 133.435984441260, 133.706223603348, 133.978883100348, 134.252761534670, 134.527867848492, 134.770304272876, 134.979729028124, 135.243703582350, 135.516904112520, 135.790100152688, 136.065505946199, 136.355259094490, 136.540365933829, 136.776589775502, 137.048191132639, 137.322200875931, 137.596210068645, 137.871435354833, 138.114940129418, 138.317353916881, 138.586356369259, 138.859689758466, 139.134113225796, 139.409633847763, 139.705876481204, 139.887588440633, 140.121843161559, 140.393598913616, 140.667738593223, 140.943079011039, 141.218423526890, 141.468034665103, 141.666216973526, 141.933265143192, 142.205656607640, 142.480204277595, 142.755837842016, 143.031476080127, 143.242662284197, 143.471602502437, 143.743522525800, 144.016612317364, 144.292070465914, 144.566343325988, 144.842998523772, 145.032586083691, 145.284293157253, 145.555775008816, 145.829379869100, 146.104053481533, 146.379802671092, 146.655556324577, 146.868168402922, 147.096635837839, 147.368709249829, 147.643113523918, 147.918691544430, 148.193096939292, 148.469858799865, 148.723698905041, 148.909899437237, 149.181537465641, 149.456337075651, 149.731137312044, 150.007001496235, 150.282869955569, 150.558742663041, 150.727364619315, 150.998450320977, 151.272988760452, 151.547526341553, 151.823225909023, 152.098929029743, 152.374635674369, 152.561945944449, 152.812540875499, 153.086423784202, 153.360302087289, 153.636279202672, 153.912260419683, 154.188245712543, 154.415116399146, 154.633722443540, 154.906118934119, 155.180791873904, 155.455463876380, 155.731284573029, 156.007108651536, 156.290200705653, 156.473551704337, 156.720564166691, 156.993551685628, 157.268605146655, 157.544698570661, 157.819754911587, 158.096897159260, 158.373002274779, 158.549115654928, 158.821024332175, 159.094595635053, 159.370024746637, 159.646388971572, 159.922757550831, 160.199130462676, 160.475507685414, 160.659586426911, 160.906938364125, 161.180076131501, 161.455258326589, 161.731469534868, 162.007684476658, 162.283903128602, 162.561157672967, 162.788922837336, 163.007848535435, 163.282482299455, 163.557113532147, 163.833590836523, 164.110072302965, 164.386557910822, 164.663047639481, 164.934702880141, 165.097631275467, 165.370925050396, 165.646238042325, 165.921551205507, 166.197882616255, 166.474217570058, 166.751576174949, 167.027919519874, 167.205783880559, 167.473429433388, 167.748195465619, 168.023872440823, 168.300465299876, 168.577062126733, 168.853662901809, 169.131184938369, 169.407794646810, 169.567936343959, 169.841387564344, 170.115831057583, 170.391274878353, 170.667725061111, 170.944178616966, 171.221643824917, 171.499114342390, 171.775580581438, 171.945824979435, 172.218931557379, 172.494734351279, 172.770538272335, 173.047248697953, 173.323962896713, 173.601587829419, 173.878310592166, 174.155945631301, 174.317105952675, 174.590712311104, 174.865299598979, 175.141868488613, 175.418440603652, 175.695015924119, 175.971594430061, 176.249173438344, 176.526757532967, 176.700716074534, 176.970443526409, 177.245483859288, 177.521415160296, 177.798242173816, 178.075072786983, 178.351906982248, 178.629642063581, 178.907382238917, 179.184229185357, 179.347358443895, 179.621123915038, 179.895858555845, 180.172550926104, 180.449246352937, 180.725944817442, 181.003630322120, 181.280336088340, 181.558030755748, 181.835730290225, 182.002051900656, 182.276352270806, 182.552412218893, 182.829357311210, 183.106305829869, 183.383257758280, 183.661099897266, 183.938946928292, 184.216798839266, 184.493767344802, 184.657932192216, 184.931856980879, 185.207706734458, 185.484524813278, 185.761345784361, 186.038169629853, 186.315967962676, 186.592798756576, 186.870605857732, 187.148417623468, 187.316589955858, 187.589311080957, 187.865503605284, 188.141696884853, 188.418765418964, 188.696712193922, 188.973788200213, 189.251743899098, 189.529704279576, 189.806791898073, 190.085639040213, 190.250959793482, 190.525049921830, 190.801039905799, 191.077985471364, 191.354933770145, 191.631884785303, 191.909797396415, 192.186755016427, 192.464676010183, 192.742601470148, 193.020531385223, 193.185380120716, 193.459990615500, 193.736318245748, 194.013509461260, 194.290703756217, 194.567901115900, 194.845966910654, 195.124037192361, 195.402111950475, 195.680191174480, 195.958274853898, 196.129402172568, 196.401796230912, 196.676991160044, 196.954066750861, 197.231144924751, 197.508225665866, 197.785308958368, 198.063341217381, 198.341377760281, 198.619418576686, 198.897463656243, 199.175512988630, 199.339455094724, 199.614227365184, 199.890694238155, 200.168013259541, 200.445335192042, 200.722660021838, 201.000841735374, 201.279027736430, 201.556363102917, 201.835412561886, 202.113611366754, 202.391814420077, 202.564964263808, 202.837558460971, 203.112914393123, 203.390124505070, 203.667337044026, 203.944551995111, 204.222701258687, 204.499922148099, 204.778079038976, 205.056240006444, 205.334405040889, 205.613508833359, 205.807259730473, 206.052979867881, 206.328753222404, 206.605363303693, 206.882814333949, 207.160268103206, 207.438566522080, 207.716026667554, 207.994332821972, 208.272643052686, 208.550957350634, 208.830119860345, 209.108442713351, 209.335826105795, 209.560130986203, 209.833836100952, 210.110270427837, 210.389095836866, 210.664971397447, 210.945234347472, 211.223686561009, 211.502142839209, 211.780603173504, 212.055446425085, 212.337535976240, 212.616764911582, 212.879058507983, 213.078192963929, 213.329009653701, 213.605768472856, 213.882527608685, 214.160115791180, 214.437706543421, 214.716129948969, 214.994557247482, 215.272988430547, 215.551423489780, 215.829862416818, 216.108305203323, 216.386751840981, 216.666034988807, 216.887445410222, 217.114181370087, 217.391258214117, 217.668336082443, 217.946158517350, 218.224727675295, 218.502556469633, 218.781133034611, 219.059713461622, 219.338297742776, 219.616885870206, 219.896223789594, 220.174819929558, 220.453419892723, 220.711218196709, 220.914562932756, 221.170464395277, 221.446566660316, 221.723480998349, 222.001211400692, 222.278944210043, 222.557496587813, 222.835235064085, 223.113794398896, 223.392357411892, 223.671742963007, 223.950313734327, 224.228888161328, 224.508285914591, 224.823730089937, 225.005474006674, 225.237561104138, 225.512603795574, 225.789833197722, 226.067795667911, 226.345760788437, 226.624461769685, 226.903166421764, 227.181140849988, 227.460586709389, 227.739302330473, 228.018021593465, 228.296744491183, 228.576206203620, 228.854936685007, 229.134406263805, 229.413144301512, 229.595594055573, 229.870534409520, 230.131057835548, 230.408136429896, 230.685215130459, 230.963900026753, 231.241785182594, 231.520476662409, 231.799171628184, 232.077870072866, 232.356571989422, 232.635277370838, 232.914791921850, 233.193504625480, 233.473026862016, 233.751746861493, 234.031276757843, 234.244213879213, 234.520900245403, 234.756571478676, 235.033963240263, 235.312076095558, 235.590191422392, 235.868309211749, 236.147151483434, 236.425997212187, 236.704846391418, 236.983699014551, 237.263278044818, 237.542137862517, 237.821001104852, 238.100591352298, 238.380185302601, 238.659059434535, 238.938660808265, 239.185666625975, 239.497150833098, 239.674892589446, 239.942779030637, 240.217682810068, 240.494938079646, 240.772981354861, 241.051026701396, 241.329863339496, 241.608703258863, 241.887546453099, 242.166392915823, 242.445242640669, 242.724886413506, 243.003743043713, 243.283394076368, 243.562257588050, 243.841915857247, 244.120786226649, 244.418753788940, 244.680120773236, 244.886368572039, 245.163798105655, 245.405489422977, 245.682351207188, 245.960627038363, 246.238905155672, 246.517894242757, 246.796886578784, 247.075882157798, 247.354880973855, 247.633883021029, 247.912888293409, 248.192607024110, 248.471619046231, 248.751344799494, 249.030363548903, 249.310096302757, 249.589832532385, 249.868861489714, 250.148604687234, 250.428351344306, 250.708101455569, 250.946487986424, 251.165046983243, 251.441664277425, 251.715079806933, 251.990992928784, 252.268442970016, 252.546665230271, 252.825662085322, 253.104662006661, 253.383664988552, 253.662671025273, 253.941680111115, 254.221466449198, 254.500482001633, 254.780275150592, 255.059297148245, 255.339097087258, 255.618900398470, 255.897932217221, 256.177742287495, 256.457555714585, 256.737372493407, 257.016417462925, 257.301028421319, 257.496664341822, 257.774284629733, 258.053019557997, 258.299786620231, 258.577552569148, 258.856012694513, 259.135168897611, 259.413633828161, 259.692795766449, 259.972655621252, 260.251823882969, 260.530995146162, 260.810864891812, 261.090042448175, 261.369918753340, 261.649102582938, 261.928985428119, 262.208871521355, 262.488760857848, 262.767957481139, 263.047853319011, 263.327752385767, 263.607654676658, 263.887560186944, 264.167468911900, 264.447380846810, 264.727295986974, 264.958891285359, 265.287135864310, 265.461513838853, 265.739593844747, 266.018292850465, 266.298059134361, 266.574984523443, 266.852660160626, 267.131842967902, 267.411028605630, 267.690217068768, 267.969408352283, 268.248602451156, 268.527799360379, 268.807754374891, 269.087712531863, 269.366918580298, 269.646883035290, 269.926850619148, 270.206065765340, 270.486039620049, 270.766016590134]

lowestN = nValues[0]
costPerKey = 2**15

# Specify the number 256 blocks in the secret key depending on the version of Kyber
if kyberVersion == KYBER512:
    l = 2 # Kyber512
elif kyberVersion == KYBER768:
    l = 3 # Kyber768
elif kyberVersion == KYBER1024:
    l = 4 # Kyber1024

if kyberVersion == KYBER512:
    highestNumQueries = 40 # Kyber512
elif kyberVersion == KYBER768 or kyberVersion == KYBER1024:
    highestNumQueries = 60 # Kyber768/Kyber1024

queries = list(range(highestNumQueries + 1))
complexities = len(queries)*[0]

for k in range(len(queries)):
    numQueries = queries[k]
    if kyberVersion == KYBER512:
        complexities[k] = math.log2(optimizeCostParallelAllKyber512(securityLevels, lowestN, numQueries, costPerKey))
    elif kyberVersion == KYBER768:
        complexities[k] = math.log2(optimizeCostParallelAllKyber768(securityLevels, lowestN, numQueries, costPerKey))
    elif kyberVersion == KYBER1024:
        complexities[k] = math.log2(optimizeCostParallelAllKyber1024(securityLevels, lowestN, numQueries, costPerKey))    

plt.plot(queries, complexities, '*')
plt.xlabel('Number of queries')
plt.ylabel('Bit complexity')

if kyberVersion == KYBER512:
    plt.title('Kyber512')
elif kyberVersion == KYBER768:
    plt.title('Kyber768')
elif kyberVersion == KYBER1024:
    plt.title('Kyber1024')