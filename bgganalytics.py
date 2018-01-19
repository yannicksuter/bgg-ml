#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sklearn import linear_model
from sklearn.neural_network import MLPClassifier

class GameAnalytics(object):
    def __init__(self, repository):
        self.repository = repository

    def get_dim_features(self, game_features, dimensions):
        entry = []
        for dim in dimensions:
            dim_val = 0.0
            if hasattr(game_features, dim):
                if type(getattr(game_features, dim)) is bool:
                    dim_val = 1.0 if getattr(game_features, dim) else 0.0
                if type(getattr(game_features, dim)) is int or type(getattr(game_features, dim)) is float:
                    dim_val = getattr(game_features, dim)
            entry.append(dim_val)
        return entry

    def get_data_matrix(self, features, dimensions, collection, default_score):
        x_train = []
        y_train = []
        x_predict = {}
        for id, game_features in features.items():
            try:
                entry = self.get_dim_features(game_features, dimensions)
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
        return x_train, y_train, x_predict

    def export_collection_score_prediction(self, model, features, dimensions, collection):
        with open("data/col_prediction.tsv", "w") as output_file:
            for id, game_features in features.items():
                col_inc, col_rating, col_numplays = collection.includes(id)
                if col_inc:
                    game = self.repository.get_by_id(id)
                    pred_score = model.predict([self.get_dim_features(game_features, dimensions)])
                    output_file.write(
                        "{}\t{}\t{}\t{}\thttps://boardgamegeek.com/boardgame/{}\n".format(game.overall_rank,
                                                                                          game.name.encode("utf-8"),
                                                                                          col_rating, pred_score[0],
                                                                                          id))

    def get_recommendations_linreg(self, collection, rnumb=10, default_score=None, testset_size=10, export_col_prediction=True):
        features, dimensions = self.repository.get_features(collection=collection)
        x_train, y_train, x_predict = self.get_data_matrix(features, dimensions, collection, default_score)

        print("Calculating recommendations using linear regression method.")
        print("> Fitting training set (size:{})".format(len(x_train)))

        # ols = linear_model.LinearRegression()
        ols = linear_model.BayesianRidge()
        if testset_size == 0:
            model = ols.fit(x_train, y_train)
        else:
            model = ols.fit(x_train[:-testset_size], y_train[:-testset_size])
            test_predictions = list(zip(y_train[-testset_size:], model.predict(x_train[-testset_size:])))
            avg_error = sum([abs(tup[1]-tup[0]) for tup in test_predictions]) / len(test_predictions)
            print("> Model match on test set: %s (avg_err: %.2f)" % (str(["%.2f: %.2f (%.2f)" % (tup[0], tup[1], tup[1]-tup[0]) for tup in test_predictions]), avg_error))

        print("> Predicting scores for %d boardgames." % (len(x_predict)))
        predicted_id_score = zip([k for k,v in x_predict.items()], model.predict([v for k,v in x_predict.items()]))
        sorted_prediction = sorted(predicted_id_score, key=lambda tup: tup[1], reverse=True)

        if export_col_prediction:
            self.export_collection_score_prediction(model, features, dimensions, collection)

        return sorted_prediction[0:rnumb if rnumb < len(sorted_prediction) else len(sorted_prediction)]

    def get_recommendations_brank(self, collection, rnumb=10, default_score=7.0):
        return None

    def clf_score(self, clf_vec):
        score = 0.0
        for i in range(len(clf_vec)):
            score += (clf_vec[i]*(i+1))
        return score/10.0

    def get_recommendations_nn(self, collection, rnumb=10, default_score=7.0, export_col_prediction=True):
        features, dimensions = self.repository.get_features(collection=collection)
        x_train, y_train, x_predict = self.get_data_matrix(features, dimensions, collection, default_score)

        #tranf score into a class vector
        y_train_clf = []
        for s in y_train:
            y_train_clf.append(
                [1.0 if s == 1 else 0.0, 1.0 if s == 2 else 0.0, 1.0 if s == 3 else 0.0, 1.0 if s == 4 else 0.0, 1.0 if s == 5 else 0.0,
                 1.0 if s == 6 else 0.0, 1.0 if s == 7 else 0.0, 1.0 if s == 8 else 0.0, 1.0 if s == 9 else 0.0, 1.0 if s == 10 else 0.0])

        #train neural network
        hidden_layer_size = 50
        # int(len(dimensions)/2)
        clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes = (hidden_layer_size,), random_state = 1)
        clf.fit(x_train, y_train_clf)

        predicted_id_score = zip([k for k,v in x_predict.items()], [self.clf_score(v) for v in clf.predict([v for k,v in x_predict.items()])])
        sorted_prediction = sorted(predicted_id_score, key=lambda tup: tup[1], reverse=True)

        if export_col_prediction:
            self.export_collection_score_prediction_nn(clf, features, dimensions, collection)

        return sorted_prediction[0:rnumb if rnumb < len(sorted_prediction) else len(sorted_prediction)]

    def export_collection_score_prediction_nn(self, model, features, dimensions, collection):
        with open("data/col_prediction_nn.tsv", "w") as output_file:
            for id, game_features in features.items():
                col_inc, col_rating, col_numplays = collection.includes(id)
                if col_inc:
                    game = self.repository.get_by_id(id)
                    pred_score = self.clf_score(model.predict([self.get_dim_features(game_features, dimensions)])[0])
                    output_file.write(
                        "{}\t{}\t{}\t{}\thttps://boardgamegeek.com/boardgame/{}\n".format(game.overall_rank,
                                                                                          game.name.encode("utf-8"),
                                                                                          col_rating, pred_score,
                                                                                          id))
