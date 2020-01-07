"""
  What is it?
  ===========================================================================

  Color quantization is the process of reducing the color palette of an
  image to a fixed number of colors. The K-means algorithm is one particular
  method among others to achieve this result. This has a number of other
  applications in image processing such as image segmentation and feature
  detection.

  For details, please see the README and/or powerpoints included.

  Changelog
  ===========================================================================

  4/10/2014
    * Compiled 32-bit and 64-bit libraries for Windows and Linux. The code
      now determines the correct one to load.

  4/06/2014
    * Significant performance improvement: rewrote K-means as a C library
      that gets loaded at runtime.

  3/30/2014
    * K-means now replaces empty clusters with random seeds to try to
      enforce the exact number of clusters. Convergence threshold still
      takes precedence.

  3/29/2014
    * implemented basic GUI and added GUI only mode (no parameters passed)

  3/28/2014
    * decoupled the KMeans class from assuming only image data is passed
      in. instead, it now takes any set of data and partitions it.
    * added Manhattan distance metric

  3/27/2014
    * added convergence threshold and ability for the algorithm to
      automatically detect when it has reached sufficient convergence

  3/25/2014
    * encapsulated k-means functionality in its own KMeans class

  3/24/2014
    * some speed improvements: using tuple instead of pixel class

  3/23/2014
    * using Tkinter/ImageTk modules for display windows (with PIL fallback)

  3/22/2014
    * removed unnecessary sqrt from distance calculations for efficiency

  3/21/2014
    * initial working version

  Tested with Python version(s): 2.7.3
  Tested on platforms: Ubuntu 12.04.3 LTS 64-bit, Windows 7 64-bit

  Notes, known issues, etc.
  ===========================================================================

  * Upon testing on Ubuntu, I had to install both the python-imaging-tk
    (ImageTk) and python-imaging (PIL). On Windows, I had to install
    PIL/Pillow for the correct Python version and architecture.

  * http://stackoverflow.com/a/4608010

    On Windows, the default photo viewer (opened when hasImageTk == False)
    has a problem with opening temporary files which PIL generates with the
    show() function. There isn't much I can do about it. However, the
    program still creates output.jpg which can be opened manually.

  TODO:
    * Set default file type in open file dialog (required in Windows)

  CSCI 230 Final Project
  Written by Brandon Sachtleben
"""

# import booleans
hasTk = hasImageTk = hasTkDialog = True

import sys      # for command line arguments
import time     # to track running time
import os       # for file path, detecting OS
import gc

# some of these modules didn't exist on the machines I've tested so I
# try to provide alternatives if possible.
try:
  import Image
except ImportError:
  try:
    from PIL import Image
  except:
    print("PIL (Python Imaging Library) or Pillow is required " \
      "for this program to run.")
    quit()

try:
  import tkinter as tk
except ImportError:
  hasTk = False

try:
  import tkinter.filedialog as tkfd
except ImportError:
  hasTkDialog = False

try:
  import ImageTk
except ImportError:
  try:
    from PIL import ImageTk
  except:
    hasImageTk = False

# python version
from pykmeans import *
# c version
import ckmeans

# start with the python version
KMeans = PyKMeans

# use C library preferably
useCLib = True

if useCLib:
  if ckmeans.hasCTypes():
    libkmeans = ckmeans.load()

    if libkmeans:
      # if we get here, use the C version
      KMeans = ckmeans.CKMeans
      print("Using C implementation")

    # something went wrong
    else:
      useCLib = False
      print("Using Python implementation")
else:
  useCLib = False
  print("Using Python implementation")

"""
  Quantizer:
  Encapsulates the program's GUI and main application of k-means
"""
class Quantizer:
  def __init__(self, filename=None, resize=True, K=8, T=99,
         metric=Euclidean, gui=True):
    self.gui = gui
    self.resize = resize
    self.imageWindows = []

    if gui:
      self.window = tk.Tk()
      self.window.title("K-Means Color Quantizer")
      self.createWidgets()
      self.window.mainloop()
    else:
      self.window = None
      self.K = int(K)
      self.T = float(T)
      self.filename = filename
      self.metric = metric

  def createWidgets(self):
    # K value
    tk.Label(text="K (1+): ").grid(row=2, sticky=tk.W)
    self.KEntry = tk.Entry(width=15)
    self.KEntry.insert(0, "8")
    self.KEntry.grid(row=2, column=2, padx=5, pady=5)

    # convergence threshold
    tk.Label(text="Convergence (0-100): ").grid(
      row=3, sticky=tk.W)
    self.TEntry = tk.Entry(width=15)
    self.TEntry.insert(0, "99")
    self.TEntry.grid(row=3, column=2, padx=5, pady=5)

    # distance metric
    tk.Label(text="Distance metric: ").grid(row=4, sticky=tk.W)
    self.metricSelection = tk.StringVar(self.window, "Euclidean")
    self.metricOptions = tk.OptionMenu(self.window,
      self.metricSelection, "Euclidean", "Manhattan")
    self.metricOptions.grid(
      row=4, column=2, sticky=tk.E, padx=5, pady=5
    )

    # filename
    tk.Label(text="Filename: ").grid(row=5, sticky=tk.W)

    self.filenameVar = tk.StringVar(self.window, "")
    self.filenameEntry = tk.Entry(width=15, textvariable=self.filenameVar)
    self.filenameEntry.grid(row=5, sticky=tk.W, column=2, padx=5, pady=5)

    if hasTkDialog:
      tk.Button(text="Open File", command=self.openFilename).grid(
        row=6, column=2, sticky=tk.E, padx=5, pady=5
      )

      # list of supported RGB or RGB-convertible formats in PIL
      imageFormats = (
        ".bmp", ".dib", ".dcx", ".gif", ".im", ".jpg", ".jpe", ".jpeg",
        ".pcd", ".pcx", ".png", ".pbm", ".pgm", ".ppm", ".psd", ".tif",
        ".tiff", ".xpm"
      )
      self.fileOpts = {
        "filetypes": [
          ("All images", imageFormats),
          ("All files", ".*"),
          ("BMP", (".bmp", ".dib")),
          ("DCX", ".dcx"),
          ("GIF", ".gif"),
          ("IM", ".im"),
          ("JPEG", (".jpg", ".jpe", ".jpeg")),
          ("PCD", ".pcd"),
          ("PCX", ".pcx"),
          ("PNG", ".png"),
          ("PPM", (".pbm", ".pgm", ".ppm")),
          ("PSD", ".psd"),
          ("TIFF", (".tif", ".tiff")),
          ("XPM", ".xpm")
        ],

        "title": "Open an image file"
      }

    # show input image
    self.showInputVar = tk.IntVar()
    self.inputCheck = tk.Checkbutton(text="Show input image",
      variable=self.showInputVar)
    self.inputCheck.grid(row=7, padx=5, pady=5)

    # quantize button
    self.quantizeButton = tk.Button(text="Quantize",
      command=self.quantize)
    self.quantizeButton.grid(
      row=8, column=0, sticky=tk.N+tk.S+tk.E+tk.W, padx=5, pady=5
    )

    # quit button
    self.quitButton = tk.Button(text="Quit", command=self.window.quit)
    self.quitButton.grid(
      row=8, column=2, sticky=tk.N+tk.S+tk.E+tk.W, padx=5, pady=5
    )

  def openFilename(self):
    self.filenameVar.set(tkfd.askopenfilename(**self.fileOpts))

  def quantize(self):
    if self.gui:
      filename = self.filenameEntry.get()
      metric = self.metricSelection.get()

      if metric == "Euclidean":
        metric = Euclidean
      elif metric == "Manhattan":
        metric = Manhattan

      K = self.KEntry.get()
      T = self.TEntry.get()

      if validateArgs(K=K, T=T):
        K = int(K)
        T = float(T)
      else:
        return
    else:
      filename = self.filename
      metric = self.metric
      K = self.K
      T = self.T

    # load and display the source image
    try:
      inputImage = Image.open(filename)
    except:
      print("There was an error opening that file.")
      return

    # guarantee the image is in RGB mode
    inputImage = inputImage.convert("RGB")

    # resize if necessary
    width, height = inputImage.size

    if self.resize and (width > 600 or height > 600):
      if width > height:
        height = int(height * 600.0 / width)
        width = 600
      else:
        width = int(width * 600.0 / height)
        height = 600

      inputImage = inputImage.resize((width, height), Image.BILINEAR)
      print("Image scaled to %dx%d" % (width, height))
    else:
      print("Image resolution: %dx%d" % (width, height))

    # get a flattened list of the image data
    data = tuple(inputImage.getdata())

    # initialize k-means with given parameters
    if not useCLib:
      kmeans = KMeans(data, K, T, metric=metric)
    else:
      kmeans = KMeans()
      ckmeans.init(libkmeans, kmeans, K, T, metric, len(data))

    # track execution time
    ts = time.time()

    # generate K clusters with some initial attributes
    print("Generating initial %d clusters..." % K)

    if not useCLib:
      seeds = []
      for k in range(0, K):
        seeds.append(kmeans.generateRandomCluster(tuple([
            (0, 255) for b in range(0, 3)
        ])))

      kmeans.seedClusters(seeds)
    else:
      ckmeans.init_clusters(libkmeans, kmeans,
        (0, 0, 0), (256, 256, 256))

    # this constant holds the maximum (Euclidean) distance between colors
    maxDistance = K * 3 * 255**2
    # has the algorithm converged?
    converged = False
    # number of passes
    numPasses = 0

    # repeat algorithm until sufficient convergence
    while not converged:
      print("Pass %d" % (numPasses + 1))
      # clear pixel assignments in clusters
      if not useCLib:
        kmeans.clearClusters()
      else:
        ckmeans.clear_clusters(libkmeans, kmeans)

      # assign each pixel to best cluster
      print("1) Assigning pixels to clusters...")
      if not useCLib:
        kmeans.assignClusters()
      else:
        ckmeans.assign_clusters(libkmeans, kmeans, data)

      # update clusters
      print("2) Updating clusters...")
      if not useCLib:
        kmeans.updateClusters()
      else:
        ckmeans.update_clusters(libkmeans, kmeans)

      # look at threshold to determine when to terminate the algorithm.
      if not useCLib:
        cPerc = (1 - kmeans.getConvergence() / maxDistance) * 100
        if cPerc >= kmeans.getThreshold():
          converged = True
      else:
        cPerc = (1 - ckmeans.get_convergence(libkmeans, kmeans) /
          maxDistance) * 100
        if cPerc >= ckmeans.get_threshold(libkmeans, kmeans):
          converged = True

      print("%.4f%% converged." % cPerc)

      numPasses += 1

    print("Done! Execution time: %.4f seconds" % (time.time() - ts))

    if not useCLib:
      clusters = kmeans.getClusters()
    else:
      clusters = ckmeans.get_clusters(libkmeans, kmeans)

    # create output images
    print("Building the new image...")
    outputImage = buildImage(clusters, K, width, height)

    print("Saving new image to output.png...")
    outputImage.save("output.png")
    print("Saved.")

    # display the results
    self.displayOutput(inputImage, outputImage, width, height)

    # free memory
    if useCLib:
      ckmeans.free_clusters(libkmeans, kmeans)

  def displayOutput(self, inputImage, outputImage, width, height):
    # destroy/clear existing windows
    for w in self.imageWindows:
      w.getWindow().destroy()

    del self.imageWindows[:]

    # display the images
    # if we have tk and imagetk modules:
    global hasTk, hasImageTk
    if hasTk and hasImageTk:
      imageWindows = []
      window = self.window

      # input window (GUI, non-root window, show only if checked)
      if self.gui:
        if self.showInputVar.get():
          imageWindows.append(ImageWindow(window, inputImage,
            "Input", (width, height), (0, 0)))

      # input window (CLI, make it the root window)
      else:
        imageWindows.append(ImageWindow(window, inputImage,
          "Input", (width, height), (0, 0)))
        window = imageWindows[-1].getWindow()

      # output window (either mode, non-root, always show)
      imageWindows.append(ImageWindow(window, outputImage,
        "Output", (width, height), (width, 0)))

      self.imageWindows.extend(imageWindows)

      for w in imageWindows:
        w.display()

      if not self.gui:
        window.mainloop()
    # otherwise use PIL
    else:
      if self.gui:
        if self.showInputVar.get():
          # save just in case there is a temporary file issue so the
          # user can still access the results
          inputImage.save("input.png")
          inputImage.show()
          outputImage.show()
      else:
        inputImage.save("input.png")
        inputImage.show()
        outputImage.show()

"""
  ImageWindow:
  Creates a toplevel or root window.
"""
class ImageWindow:
  def __init__(self, rootWindow, image, title, size, position):
    if rootWindow == None:
      self.window = tk.Tk()
    else:
      self.window = tk.Toplevel(rootWindow)

    self.image = image
    self.title = title
    self.size = size
    self.position = position

  def display(self):
    self.image = ImageTk.PhotoImage(self.image)

    self.window.title(self.title)
    self.window.geometry("%dx%d+%d+%d" % (self.size + self.position))
    label = tk.Label(self.window, image=self.image)
    label.grid()

  def getWindow(self):
    return self.window

def buildImage(clusters, K, width, height):
  image = Image.new("RGB", (width, height))

  for k in range(0, K):
    if not useCLib:
      size = len(clusters[k].points)

      for p in clusters[k].points:
        x = int(p % width)
        y = int(p / width)
        c = clusters[k].centroid

        image.paste((int(c[0]), int(c[1]), int(c[2])), (x, y, x + 1, y + 1))
    else:
      size = clusters[k].size

      for i in range(0, size):
        x = int(clusters[k].indices[i] % width)
        y = int(clusters[k].indices[i] / width)
        c = clusters[k].centroid

        image.paste((int(c[0]), int(c[1]), int(c[2])), (x, y, x + 1, y + 1))

  return image

def validateArgs(K=1, T=0):
  valid = True

  try:
    K = int(K)
    T = float(T)
    if K < 1 or T < 0 or T > 100:
      raise ValueError
  except:
    print("Please supply only positive integers as arguments.")
    print("Example (K=4, T=99): python quantize.py image.jpg 4 99")
    print("Example (GUI mode): python quantize.py")
    valid = False

  return valid

def main():
  # if no args, invoke GUI
  if len(sys.argv) == 1:
    app = Quantizer(gui=True)
  else:
    K = 8
    T = 99.0
    filename = sys.argv[1]

    validArgs = True

    if len(sys.argv) == 3:
      K = sys.argv[2]
      validArgs = validateArgs(K=K)
    elif len(sys.argv) == 4:
      K, T = sys.argv[2:]
      validArgs = validateArgs(K=K, T=T)

    if validArgs:
      K = int(K)
      T = float(T)
      print("Using K=%d and T=%.2f" % (K, T))

      app = Quantizer(gui=False, K=K, T=T, filename=filename)
      app.quantize()

if __name__ == "__main__":
  main()
