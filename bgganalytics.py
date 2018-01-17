#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sklearn import linear_model

class GameAnalytics(object):
    def __init__(self, repository):
        self.repository = repository

    def get_recommendations_linreg(self, collection, rnumb=10, default_score=7.0):
        features, dimensions = self.repository.get_features(collection=collection)

        x_train = []
        y_train = []
        x_predict = {}
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
                    if col_rating is not None:
                        x_train.append(entry)
                        y_train.append(col_rating)
                else:
                    x_predict[id] = entry
            except:
                pass

        print("\nFitting training set: {}".format(len(x_train)))

        ols = linear_model.LinearRegression()
        model = ols.fit(x_train[:-10], y_train[:-10])
        # model = ols.fit(x_train, y_train)

        print("\nLinReg test set:")
        for i in zip(y_train[-10:], model.predict(x_train[-10:])):
            print(i)

        predicted_id_score = zip([k for k,v in x_predict.items()], model.predict([v for k,v in x_predict.items()]))
        sorted_prediction = sorted(predicted_id_score, key=lambda tup: tup[1], reverse=True)

        return sorted_prediction[0:rnumb if rnumb < len(sorted_prediction) else len(sorted_prediction)]

    def get_recommendations_brank(self, collection, rnumb=10, default_score=7.0):
        return None

