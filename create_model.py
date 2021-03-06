# script for grabbing samples from db and creating scaler.pkl and model.pkl

import os
import pickle
import numpy as np
from collections import namedtuple
# from utilities import contiguous_regions
from sklearn import preprocessing
from sklearn import svm
import psycopg2

conn = psycopg2.connect("dbname='calm_dog' user='pi' password='pi' host='localhost'")
cur = conn.cursor()

cur.execute("""SELECT * from data""")
rows = cur.fetchall()

copied_features = np.ndarray(shape=(len(rows),len(rows[0][2])), dtype=float, order='C')
labels = []
i = 0

for feature in rows:
  labels.append(rows[i][1])
  copied_features[i] = rows[i][2]
  i += 1

scaler = preprocessing.StandardScaler().fit(copied_features)
pickle.dump(scaler, open( "/home/pi/code/Ornithokrites/preprocessors/scaler5.pkl", "wb" ) )
print "Created scaler"
copied_features_scaled = scaler.transform(copied_features)

clf = svm.SVC()
clf.fit(copied_features_scaled, labels)
pickle.dump(clf, open( "/home/pi/code/Ornithokrites/models/model5.pkl", "wb" ) )
print "Created model"
