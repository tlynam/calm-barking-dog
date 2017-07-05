#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 22 17:50:43 2014

@author: Lukasz Tracewski

Identification of kiwi calls from audio recordings - main module.
"""

import multiprocessing
import configuration
import noise_reduction
import features
import identification
import s3connection
import wave
import numpy
from datetime import datetime
from subprocess import call
import psycopg2
import shutil
from sklearn import preprocessing
from sklearn import svm
import pickle

class Ornithokrites(object):
	"""
	Synchronous version. All steps are done in sequence: a single wave file is acquired and then
	processed.
	"""

	def __init__(self, app_config):
		self.app_config = app_config
		self.kiwi_finder = identification.KiwiFinder(app_config)
		self.noise_remover = noise_reduction.NoiseRemover()
		self.fetcher = s3connection.RecordingsFetcher()
		self.sample_count = 0


	def run(self):
		for rate, sample, path in self.fetcher.get_next_recording(data_store=app_config.data_store,
															stream=app_config.stream,
															bucket_name=app_config.bucket):

			self.process(rate, sample, path)


	def process(self, rate, sample, path):
		filtered_sample = self.noise_remover.remove_noise(sample, rate)
		segmented_sounds = self.noise_remover.segmentator.Sounds

		if segmented_sounds:
			feature_extractor = features.FeatureExtractor(app_config, rate)
			extracted_features = feature_extractor.process(filtered_sample, segmented_sounds)
			extracted_features = numpy.nan_to_num(extracted_features)

			if app_config.stream: # If streaming audio: play audio if bark, and save raw segments to bark/non_bark folders
				segments_analysis = self.kiwi_finder.find_individual_calls(extracted_features)

				self.save_segments(segmented_sounds, segments_analysis, filtered_sample, rate)
				if 1 in segments_analysis: # Detect bark
					print "Bark detected, playing rain for 5 seconds"
					call(["aplay", "calming_sounds/rain.wav", "-d", "5"])

			elif app_config.data_store: # If reading audio from disk: save features into db, and regenerate models
				self.store_features(extracted_features, path)
				self.move_processed_file(path)
				# self.regenerate_models()

		elif app_config.data_store: # Delete file with no segments
			old_path = path
			new_path = path.replace("categorized_data", "no_segments")
			shutil.move(old_path, new_path)
			print "Moved file from categorized_data to no_segments folder " + new_path


	def regenerate_models(self):
		conn = psycopg2.connect("dbname='calm_dog' user='pi' password='pi' host='localhost'")
		cur = conn.cursor()

		cur.execute("""SELECT * from data""")
		rows = cur.fetchall()

		copied_features = numpy.ndarray(shape=(len(rows),len(rows[0][2])), dtype=float, order='C')
		labels = []
		i = 0

		for feature in rows:
		  labels.append(rows[i][1])
		  copied_features[i] = rows[i][2]
		  i += 1

		scaler = preprocessing.StandardScaler().fit(copied_features)

		preprocessor_path = "/home/pi/code/Ornithokrites/preprocessors/scaler4.pkl"
		pickle.dump(scaler, open(preprocessor_path, "wb" ) )
		print "Regenerated Preprocessor: " + preprocessor_path

		copied_features_scaled = scaler.transform(copied_features)

		clf = svm.SVC()
		clf.fit(copied_features_scaled, labels)

		model_path = "/home/pi/code/Ornithokrites/models/model4.pkl"
		pickle.dump(clf, open(model_path, "wb" ) )
		print "Regenerated Model: " + model_path


	def store_features(self, extracted_features, path):
		if 'non_bark' in path:
			label, text_label = [0, 'non_bark']
		else:
			label, text_label = [1, 'bark']

		conn = psycopg2.connect("dbname='calm_dog' user='pi' password='pi' host='localhost'")
		cur = conn.cursor()

		for feature in extracted_features:
		  cur.execute(
		      """INSERT INTO data (text_label, label, features)
		         VALUES (%s, %s, %s);""",
		       (text_label, label, list(feature)))

		conn.commit()
		conn.close()
		print "Stored " + str(len(extracted_features)) + " features into database from " + path


	def move_processed_file(self, path):
		old_path = path
		new_path = path.replace("categorized_data", "imported_data")
		shutil.move(old_path, new_path)
		print "Moved file from categorized_data to imported_data folder " + new_path


	def save_segments(self, segmented_sounds, segments_analysis, filtered_sample, rate):
		for index, (start, end) in enumerate(segmented_sounds):
			feature = segments_analysis[index]

			data = filtered_sample[int(start):int(end)]
			data = data.astype(numpy.int16)
			raw_data = data.tostring()

			self.save_file(raw_data, feature, rate)


	def save_file(self, data, feature, rate):
		folder = 'barks' if feature == 1 else 'non_barks'
		fullpath = 'data/raw_data/' + folder + '/' + datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f') + '.wav'

		w = wave.open(fullpath, 'wb')
		w.setnchannels(1)
		w.setsampwidth(2)
		w.setframerate(rate)
		w.writeframes(data)
		w.close()
		print "Saved raw data " + fullpath


if __name__ == '__main__':
	app_config = configuration.Configurator().parse_arguments()
	Ornithokrites(app_config).run()
