#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import pandas as pd
import math
from sklearn import linear_model

class GameAnalytics(object):
    def __init__(self, repository):
        self.repository = repository

    def get_recommendations(self, collection, rnumb=10, default_score=7.0):
        features, dimensions = self.repository.get_features(collection=collection)

        x_train = []
        x_test = {}
        y_train = []
        for id, game_features in features.items():
            try:
                entry = []
                for dim in dimensions:
                    dim_val = 0.0
                    if hasattr(game_features, dim):
                        if type(getattr(game_features, dim)) is bool:
                            dim_val = 1.0 if getattr(game_features, dim) else 0.0
                        if type(getattr(game_features, dim)) is int or type(getattr(game_features, dim)) is float:
                            dim_val = getattr(game_features, dim)
                    entry.append(dim_val)
                col_inc, col_rating, col_numplays = collection.includes(id)
                if col_inc:
                    if col_rating is None:
                        col_rating = default_score
                    x_train.append(entry)
                    y_train.append(col_rating)
                else:
                    x_test[id] = entry
            except:
                pass

        ols = linear_model.LinearRegression()
        model = ols.fit(x_train, y_train)
        predicted_id_score = zip([k for k,v in x_test.items()], model.predict([v for k,v in x_test.items()]))
        sorted_prediction = sorted(predicted_id_score, key=lambda tup: tup[1], reverse=True)

        return sorted_prediction[0:rnumb if rnumb < len(sorted_prediction) else len(sorted_prediction)]
# return [self.repository.get_by_id(36218)]

