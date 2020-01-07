"""
  Interface to the K-means C library.

  Loads the C library for the correct OS and architecture.
  Provides some wrappers for functions that need ctypes conversions.

  CSCI 230 Final Project
  Written by Brandon Sachtleben
"""

hasCTypes = True

try:
  import ctypes
except ImportError:
  hasCTypes = False

import os
import platform

# distance metrics
Euclidean, Manhattan = list(range(0, 2))

# point type is a pointer representing RGB components
Point = ctypes.POINTER(ctypes.c_int)
# point array type (any number of points)
PointArray = ctypes.POINTER(Point)

# ctypes struct definition of a cluster
class CCluster(ctypes.Structure):
  _fields_ = [
    ("points", PointArray),
    ("indices", Point),
    ("centroid", Point),
    ("prevCentroid", Point),
    ("size", ctypes.c_int)
  ]

# ctypes k-means struct
class CKMeans(ctypes.Structure):
  _fields_ = [
    ("K", ctypes.c_int),
    ("T", ctypes.c_float),
    ("metric", ctypes.c_int),
    ("data_size", ctypes.c_int),
    ("dist", ctypes.c_void_p),
    ("lower", ctypes.c_int * 3),
    ("upper", ctypes.c_int * 3),
    ("clusters", ctypes.POINTER(CCluster))
  ]

def hasCTypes():
  global hasCTypes
  return hasCTypes

def load():
  try:
    path = os.path.dirname(os.path.abspath(__file__))
    osName = platform.system()

    # load the external library
    # Linux
    if osName == "Linux":
      # 32-bit
      try:
        libkmeans = ctypes.cdll.LoadLibrary(
          os.path.join(path, "lib/kmeans32.so")
        )
      # 64-bit
      except:
        libkmeans = ctypes.cdll.LoadLibrary(
          os.path.join(path, "lib/kmeans64.so")
        )
    # Windows
    elif osName == "Windows":
      # 32-bit
      try:
        libkmeans = ctypes.WinDLL(
          os.path.join(path, "lib/kmeans32.dll")
        )
      # 64-bit
      except:
        libkmeans = ctypes.WinDLL(
          os.path.join(path, "lib/kmeans64.dll")
        )
    # OS not supported
    else:
      raise

    # set argument types
    libkmeans.init.argtypes = [
      ctypes.POINTER(CKMeans),
      ctypes.c_int,
      ctypes.c_float,
      ctypes.c_int,
      ctypes.c_int
    ]
    libkmeans.init_clusters.argtypes = [
      ctypes.POINTER(CKMeans),
      ctypes.c_int * 3,
      ctypes.c_int * 3
    ]
    libkmeans.assign_clusters.argtypes = [
      ctypes.POINTER(CKMeans),
      ctypes.POINTER(ctypes.c_int * 3)
    ]
    libkmeans.update_clusters.argtypes = [ctypes.POINTER(CKMeans)]
    libkmeans.get_convergence.argtypes = [ctypes.POINTER(CKMeans)]
    libkmeans.get_threshold.argtypes = [ctypes.POINTER(CKMeans)]
    libkmeans.get_clusters.argtypes = [ctypes.POINTER(CKMeans)]
    libkmeans.clear_clusters.argtypes = [ctypes.POINTER(CKMeans)]
    libkmeans.free_clusters.argtypes = [ctypes.POINTER(CKMeans)]

    # set the return types
    libkmeans.euclidean.restype = ctypes.c_int
    libkmeans.manhattan.restype = ctypes.c_int
    libkmeans.get_clusters.restype = ctypes.POINTER(CCluster)
    libkmeans.get_threshold.restype = ctypes.c_float
    libkmeans.get_convergence.restype = ctypes.c_float
  except:
    libkmeans = None
    print("Failed to load C library.")

  return libkmeans

def init(libkmeans, kmeans, K, T, metric, data_size):
  libkmeans.init(
    ctypes.byref(kmeans),
    ctypes.c_int(K),
    ctypes.c_float(T),
    ctypes.c_int(metric),
    ctypes.c_int(data_size)
  )

def init_clusters(libkmeans, kmeans, lower, upper):
  libkmeans.init_clusters(
    ctypes.byref(kmeans),
    (ctypes.c_int * 3)(*lower),
    (ctypes.c_int * 3)(*upper)
  )

def clear_clusters(libkmeans, kmeans):
  libkmeans.clear_clusters(ctypes.byref(kmeans))

def assign_clusters(libkmeans, kmeans, data):
  cdata = ((ctypes.c_int * 3) * len(data))()
  cdata[:] = data
  libkmeans.assign_clusters(ctypes.byref(kmeans), cdata)

def update_clusters(libkmeans, kmeans):
  libkmeans.update_clusters(ctypes.byref(kmeans))

def get_convergence(libkmeans, kmeans):
  return libkmeans.get_convergence(ctypes.byref(kmeans))

def get_threshold(libkmeans, kmeans):
  return libkmeans.get_threshold(ctypes.byref(kmeans))

def get_clusters(libkmeans, kmeans):
  return libkmeans.get_clusters(ctypes.byref(kmeans))

def free_clusters(libkmeans, kmeans):
  libkmeans.free_clusters(ctypes.byref(kmeans))