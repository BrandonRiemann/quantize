"""
    Feature Detection
    ===========================================================================

    Attempts to identify and extract various features of an image based on
    my own algorithm. This could be a useful image processing technique to
    separate regions of an image and apply filters separately to each part.

    This program will load an image from disk and automatically partition
    the image according to the features it finds. Output windows indicate
    all of the detected regions.

    For details on how I constructed the algorithm, please see the
    accompanying README. I describe the design and implementation there.

    ===========================================================================

    CSCI 230 Final Project

    3/20/2014 - version 1.0.1
        added iterative version of traversePath() to avoid the recursive
        stack limit

    3/19/2014 - version 1.0.0
        initial coding stage/design

    Written by Brandon Sachtleben
"""

import time # measure execution time
import math
from PIL import Image # for image display, pixel data, and crop

BLOCK_SIZE = 2 # should be an even number
image = None
blocks = None

# a block is a contiguous region of pixels
class Block:
    def __init__(self):
        self.pixels = []
        self.avg = self.position = self.x = self.y = 0

    # adds a pixel to the internal list of pixels
    def addPixel(self, pixel):
        self.pixels.append(pixel)

    def addPixelList(self, pixels):
        self.pixels.extend(pixels)

    # return a rounded average intensity of the block of pixels
    def roundedAverage(self):
        return int(round(sum(self.pixels) / float(len(self.pixels))))

# given image width and (x, y) in image, returns the intensity at that pixel
# imageData expects a flattened list of intensity values
def getPixelIntensity(imageData, width, pos):
    return imageData[pos[0] % width + pos[1] * width]

# crop the image to a multiple of the desired block size
def blockAdjustCrop(image, block_size):
    # get the original width and height of the image
    orig_width, orig_height = image.size
    # find the greatest multiple of blocks we can fit in the image
    width = math.floor(orig_width / block_size) * block_size
    height = math.floor(orig_height / block_size) * block_size
    # center the crop
    x_offset = (orig_width - width) / 2
    y_offset = (orig_height - height) / 2
    width += x_offset
    height += y_offset

    # crop the image; parameter is a 4-tuple (left, upper, right, lower)
    return image.crop((int(x_offset),
                       int(y_offset),
                       int(width),
                       int(height)))

def generateBlocks(image):
    data = list(image.getdata())
    width, height = image.size
    blocks = []
    block = Block()
    position = 0

    for col in range(0, width, BLOCK_SIZE):
        for row in range(0, height):
            if (row + 1) % BLOCK_SIZE == 0:
                block.x = col
                block.y = row
                block.avg = block.roundedAverage()
                block.position = position
                blocks.append(block)
                position += 1
                block = Block()
                continue

            index = col + row * width
            block.addPixelList(data[index : index + BLOCK_SIZE])

    # length of blocks should be the area of image / area of block size
    assert len(blocks) == width * height / BLOCK_SIZE ** 2

    return blocks

# returns a list of neighbor blocks given a block object
def getNeighbors(block):
    global image, blocks
    width, height = image.size

    neighbors = []

    rows = height / BLOCK_SIZE
    col = math.floor(block.position / rows) * rows

    # check all 8 directions for potential neighbors
    left = block.position - rows
    right = block.position + rows
    top = block.position - 1
    bottom = block.position + 1
    top_right = right - 1
    top_left = left - 1
    bottom_right = right + 1
    bottom_left = left + 1

    if bottom < col + rows:
        neighbors.append(blocks[bottom])
    if right < len(blocks):
        neighbors.append(blocks[right])
        if top >= col:
            neighbors.append(blocks[top_right])
        if bottom < col + rows:
            neighbors.append(blocks[bottom_right])
    if left >= 0:
        neighbors.append(blocks[left])
        if top >= col:
            neighbors.append(blocks[top_left])
        if bottom < col + rows:
            neighbors.append(blocks[bottom_left])
    if top >= col:
        neighbors.append(blocks[top])

    return neighbors

# reduce a list of cells based on a given threshold
def reduceNeighbors(cells, orig_cell, threshold):
    # use a list comprehension to remove necessary elements
    return [x for x in cells if abs(x.avg - orig_cell.avg) < threshold]

# recursive function that creates a subgraph from several path traversals
# higher threshold => greater tolerance (more blocks matched)
def traversePathRecursive(cell, orig_cell, visited = [], threshold = 127):
    neighbors = reduceNeighbors(getNeighbors(cell), orig_cell, threshold)

    path = [cell]
    visited.append(cell.position)

    for N in neighbors:
        if N.position not in visited:
            path += traversePath(N, orig_cell, visited, threshold)

    return path

# same as above but an iterative version (to avoid recursion limit)
def traversePathIterative(orig_cell, visited = [], threshold = 127):
    neighbors = [orig_cell]
    path = []

    for N in neighbors:
        if N.position not in visited:
            path.append(N)
            visited.append(N.position)
            neighbors += reduceNeighbors(getNeighbors(N), orig_cell, threshold)

    return path

def main():
    # open the image, convert it to greyscale, and crop it
    # L stands for luminance
    global image, blocks

    image_color = Image.open("face.jpg")
    image_color.show()
    image = blockAdjustCrop(image_color.convert("L"), BLOCK_SIZE)

    # generate all of the blocks in the image
    blocks = generateBlocks(image)

    visited = []
    subgraphs = []
    width, height = image.size
    area = width * height

    ts = time.time()

    for block in blocks:
        if block.position not in visited:
            subgraph = traversePathIterative(block, visited, 61)
            subgraphs.append(subgraph)
            print("# vertices in subgraph: %d (%.2f%% of graph)" % \
                (len(subgraph),
                len(subgraph) * BLOCK_SIZE**2 * 100 / float(area)))

    print("Total vertices in graph: " + str(len(blocks)))
    # a good number of subgraphs for an image might be around 2-10
    # modifying the threshold and weights will help achieve this
    # higher threshold => less subgraphs (more connected regions)
    # higher target weight => less subgraphs (not yet implemented)
    print("Total subgraphs: " +  str(len(subgraphs)))

    print("Execution time: %.4f seconds" % (time.time() - ts))

    for subgraph in subgraphs:
        for block in subgraph:
            image.paste(subgraph[0].avg,
                (block.x,
                block.y - BLOCK_SIZE,
                block.x + BLOCK_SIZE,
                block.y - BLOCK_SIZE + BLOCK_SIZE))

    image.show()

if __name__ == "__main__":
    main()