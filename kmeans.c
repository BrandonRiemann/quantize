/*
  I rewrote my original Python code for the clustering part of the algorithm
  in C. It runs significantly faster now as a result. I simply load in the
  library in Python using ctypes. I'm already somewhat familiar with C so it
  wasn't too much trouble to do the rewrite.

  Benchmark @ K=64 clusters:
  * Python implementation: 103.5477 seconds
  * C extension running through Python: 3.5314 seconds

  Compiled and linked using GCC 4.6.3 (32/64-bit on Linux):
  gcc -m32 -fPIC -g -c -Wall kmeans.c
  gcc -m32 -shared -Wl,-soname,kmeans.so.1 -o kmeans32.so kmeans.o -lc
  gcc -m64 -fPIC -g -c -Wall kmeans.c
  gcc -m64 -shared -Wl,-soname,kmeans.so.1 -o kmeans64.so kmeans.o -lc

  Written by Brandon Sachtleben
  CSCI 230 Final Project
*/

#include <stdlib.h> /* abs */
#include <stdint.h> /* uint32_t */
#include <limits.h> /* UINT_MAX */
#include <string.h> /* memcpy() */
#include <time.h>   /* time() */
#include <stdio.h>  /* printf() */

/* 3 component point struct */
typedef struct {
  int x;
  int y;
  int z;
} Point;

/* cluster struct */
typedef struct {
  /* data points */
  int **points;
  /* indices of data points */
  int *indices;
  /* centroids */
  int *centroid;
  int *prevCentroid;
  /* number of data points */
  int size;
} Cluster;

/* data needed for k-means algorithm */
typedef struct {
  /* number of clusters */
  int K;
  /* threshold between 0 and 100 */
  float T;
  /* 0 = euclidean, 1 = manhattan */
  int metric;
  /* number of data points */
  int data_size;
  /* distance function pointer */
  int (*dist)(int*,int*);
  /* upper and lower bounds of data */
  int lower[3], upper[3];
  /* clusters */
  Cluster *clusters;
} KMeans;

/* euclidean distance */
/* doesn't need the sqrt because it's all comparisons */
int euclidean(int *a, int *b) {
  return (a[0] - b[0]) * (a[0] - b[0]) +
       (a[1] - b[1]) * (a[1] - b[1]) +
       (a[2] - b[2]) * (a[2] - b[2]);
}

/* manhattan distance */
int manhattan(int *a, int *b) {
  return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]);
}

/* return random point within lower and upper bounds */
Point generate_random_seed(KMeans *kmeans) {
  Point p = {
    kmeans->lower[0] + rand() % (kmeans->upper[0] - kmeans->lower[0]),
    kmeans->lower[1] + rand() % (kmeans->upper[1] - kmeans->lower[1]),
    kmeans->lower[2] + rand() % (kmeans->upper[2] - kmeans->lower[2])
  };
  return p;
}

/* store some attributes for later use */
void init(KMeans *kmeans, int K, float T, int metric, int data_size) {
  kmeans->K = K;
  kmeans->T = T;
  kmeans->metric = metric;
  kmeans->data_size = data_size;

  switch (metric) {
    case 0: /* Euclidean */
      kmeans->dist = &euclidean;
      break;
    case 1: /* Manhattan */
      kmeans->dist = &manhattan;
      break;
    default:
      kmeans->dist = &euclidean;
  }

  /* set a seed for rand */
  srand(time(NULL));
}

/* initialize clusters with lower and upper bounds */
void init_clusters(KMeans *kmeans, int *lower, int *upper) {
  memcpy(kmeans->lower, lower, sizeof(int) * 3);
  memcpy(kmeans->upper, upper, sizeof(int) * 3);

  /* Create K clusters */
  kmeans->clusters = malloc(sizeof(*kmeans->clusters) * kmeans->K);

  Cluster *clusters = kmeans->clusters;

  int i;
  for (i = 0; i < kmeans->K; ++i) {
    /* size = 0 */
    clusters[i].size = 0;
    clusters[i].points = NULL;
    clusters[i].indices = NULL;

    /* centroid */
    clusters[i].centroid = malloc(sizeof(int) * 3);
    clusters[i].prevCentroid = malloc(sizeof(int) * 3);

    Point p = generate_random_seed(kmeans);
    clusters[i].centroid[0] = clusters[i].prevCentroid[0] = p.x;
    clusters[i].centroid[1] = clusters[i].prevCentroid[1] = p.y;
    clusters[i].centroid[2] = clusters[i].prevCentroid[2] = p.z;
  }
}

Cluster *get_clusters(KMeans *kmeans) {
  return kmeans->clusters;
}

float get_threshold(KMeans *kmeans) {
  return kmeans->T;
}

float get_convergence(KMeans *kmeans) {
  int i, sum = 0;

  for (i = 0; i < kmeans->K; ++i) {
    sum += euclidean(
      kmeans->clusters[i].centroid,
      kmeans->clusters[i].prevCentroid
    );
  }

  return sum;
}

void clear_clusters(KMeans *kmeans) {
  /* clear/free only the points */
  int i, j;

  Cluster *clusters = kmeans->clusters;

  for (i = 0; i < kmeans->K; ++i) {
    for (j = 0; j < clusters[i].size; ++j) {
      free(clusters[i].points[j]);
    }

    free(clusters[i].points);
    free(clusters[i].indices);

    clusters[i].points = NULL;
    clusters[i].indices = NULL;
    clusters[i].size = 0;
  }
}

void compute_centroid(Cluster cluster) {
  int r = 0, g = 0, b = 0;
  int i;

  for (i = 0; i < cluster.size; ++i) {
    r += cluster.points[i][0];
    g += cluster.points[i][1];
    b += cluster.points[i][2];
  }

  /* save old centroid */
  memcpy(cluster.prevCentroid, cluster.centroid, sizeof(int) * 3);

  /* new centroid */
  cluster.centroid[0] = r / cluster.size;
  cluster.centroid[1] = g / cluster.size;
  cluster.centroid[2] = b / cluster.size;
}

void update_clusters(KMeans *kmeans) {
  int i;

  Cluster *clusters = kmeans->clusters;

  for (i = 0; i < kmeans->K; ++i) {
    if (clusters[i].size == 0) {
      printf("Found an empty cluster (reassigning).\n");

      /* new centroid */
      Point p = generate_random_seed(kmeans);
      clusters[i].centroid[0] = clusters[i].prevCentroid[0] = p.x;
      clusters[i].centroid[1] = clusters[i].prevCentroid[1] = p.y;
      clusters[i].centroid[2] = clusters[i].prevCentroid[2] = p.z;
    } else {
      compute_centroid(clusters[i]);
    }
  }
}

void free_clusters(KMeans *kmeans) {
  int i, j;

  Cluster *clusters = kmeans->clusters;

  for (i = 0; i < kmeans->K; ++i) {
    for (j = 0; j < clusters[i].size; ++j) {
      free(clusters[i].points[j]);
    }

    free(clusters[i].points);
    free(clusters[i].indices);
    free(clusters[i].centroid);
    free(clusters[i].prevCentroid);
  }

  free(clusters);
}

void assign_clusters(KMeans *kmeans, int *data) {
  uint32_t minCentroid, centroidDist;
  int i, j, k;

  Cluster *clusters = kmeans->clusters;

  /* minimize the distance from the point to the cluster */
  for (i = 0; i < kmeans->data_size; ++i) {
    minCentroid = UINT_MAX;

    for (j = 0; j < kmeans->K; ++j) {
      centroidDist = kmeans->dist(clusters[j].centroid, &data[i*3]);

      if (centroidDist < minCentroid) {
        minCentroid = centroidDist;
        k = j;
      }
    }

    int idx = clusters[k].size;

    /* reallocate list of points so we can add one */
    clusters[k].points = realloc(clusters[k].points,
      sizeof(*clusters[k].points) * (idx + 1));

    /* reallocate index list */
    clusters[k].indices = realloc(clusters[k].indices,
      sizeof(*clusters[k].indices) * (idx + 1));

    /* allocate space for a point */
    clusters[k].points[idx] = malloc(sizeof(int) * 3);

    /* copy the point from the data set to the cluster */
    memcpy(clusters[k].points[idx], &data[i*3], sizeof(int) * 3);

    /* record the index of the point */
    clusters[k].indices[idx] = i;

    ++clusters[k].size;
  }
}