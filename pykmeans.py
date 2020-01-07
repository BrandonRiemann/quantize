"""
  Python implementation of the K-means algorithm

  This file contains my implementation of K-means in Python. There is a
  preferred C version that I wrote which is much faster (although does
  practically the same). The C version is used unless there is a problem
  with importing the ctypes module or C library, in which case PyKMeans
  is the fallback.

  CSCI 230 Final Project
  Written by Brandon Sachtleben
"""

# generate random clusters initially
import random

# distance metrics
Euclidean, Manhattan = list(range(0, 2))

"""
  PyCluster:
  A cluster is simply a subset of a data set with a centroid (average) of
  its containing points.
"""
class PyCluster:
  def __init__(self, centroid):
    # cluster color
    self.centroid = self.prevCentroid = centroid
    # data points
    self.points = {}
    # length of attribute
    if isinstance(centroid, int) or isinstance(centroid, float):
      self.components = 1
    else:
      self.components = len(centroid)

  def clearPixels(self):
    self.points.clear()

  # average all the attributes
  def computeCentroid(self):
    length = len(self.points)

    centroid = [0] * self.components

    for p in self.points:
      for i in range(0, self.components):
        centroid[i] += self.points[p][i]

    self.prevCentroid = self.centroid
    self.centroid = tuple([i / length for i in centroid])

"""
  PyKMeans:
  Contains the main implementation of the algorithm.
"""
class PyKMeans:
  def __init__(self, data, K=6, T=99, metric=Euclidean):
    # number of clusters
    self.K = int(K)
    # threshold
    self.T = float(T)
    # list of K clusters
    self.clusters = []
    # data to partition (should be tuple or list)
    self.data = data
    # length of individual elements
    if isinstance(self.data[0], int) or isinstance(self.data[0], float):
      self.components = 1
    else:
      self.components = len(self.data[0])
    # distance metric
    self.metric = metric

  # accessors
  def getK(self):
    return self.K

  def getThreshold(self):
    return self.T

  def getClusters(self):
    return self.clusters

  def getData(self):
    return self.data

  def getMetric(self):
    return self.metric

  # returns a cluster with random attributes
  # bounds is the upper and lower bounds of the data.
  # e.g. ((0, 255), (0, 255), (0, 255))
  def generateRandomCluster(self, bounds):
    return tuple([
      random.randrange(bounds[i][0], bounds[i][1] + 1)
      for i in range(0, len(bounds))
    ])

  def seedClusters(self, seeds):
    for s in seeds:
      self.clusters.append(PyCluster(s))

  # assign points to the clusters that minimize their distance from them
  def assignClusters(self):
    # store the function so we don't have to use unnecessary if statements
    # in the loops.
    if self.metric == Euclidean:
      distance = getEuclideanDistance
    elif self.metric == Manhattan:
      distance = getManhattanDistance
    else:
      distance = getEuclideanDistance

    # float("Inf") is not considered portable, so I'm using try/except
    # it throws an error on some systems and versions of Python
    try:
      largeValue = float("Inf")
    except:
      largeValue = 1e30000

    for i, p in enumerate(self.data):
      # initial value to be minimized
      minAttr = largeValue
      for c in self.clusters:
        attrDist = distance(c.centroid, p, self.components)

        if attrDist < minAttr:
          minAttr = attrDist
          k = c
      k.points[i] = p

  # clear all data points in clusters
  def clearClusters(self):
    [k.clearPixels() for k in self.clusters]

  # update the centroids of the cluster
  def updateClusters(self):
    for k in self.clusters:
      # if the cluster is empty, replace it with another random cluster
      # to be handled on reassignment
      if len(k.points) == 0:
        print("Found an empty cluster (reassigning).")
        k.prevCentroid = k.centroid = self.generateRandomCluster([
          (0, 255) for i in range(0, self.components)
        ])
      else:
        k.computeCentroid()

  # returns convergence of the algorithm
  def getConvergence(self):
    return float(sum([
      getEuclideanDistance(k.centroid, k.prevCentroid, self.components)
      for k in self.clusters
    ]))

# returns Euclidean distance between two positions (element length = n)
def getEuclideanDistance(a, b, n):
  return sum([(b[i] - a[i])**2 for i in range(0, n)])

# return Manhattan distance between two positions (element length = n)
def getManhattanDistance(a, b, n):
  return sum([abs(b[i] - a[i]) for i in range(0, n)])