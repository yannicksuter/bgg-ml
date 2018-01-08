#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sklearn.cluster import KMeans

class GameAnalytics(object):
    def __init__(self, repository):
        self.repository = repository

    def get_featurematrix(self, games):
        for game in self.repository.games:
            pass
        return None

    def get_clusters(self, collection):
        data = self.get_featurematrix(collection)
        if data:
            kmeans = KMeans(n_clusters=12)
            kmeans = kmeans.fit(data)
            labels = kmeans.predict(data)
            C = kmeans.cluster_centers_
            L = kmeans.labels_

            print("42.")