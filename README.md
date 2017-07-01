Ornithokrites
============
- See the complete original readme in README_orig

Ornithokrites is a transliteration of ancient Greek όρνϊθοκρίτης, meaning interpreter of flight or cries of birds. With its rather ambitious name, the program itself is a tool meant for an automatic identification of kiwi calls from low quality audio recordings. It has been designed to cope with large variations of environmental conditions and low quality of input data. For each provided audio file, the program enables detection of any kiwi calls and, in case they are present, which gender they belong to (male, female or both).

How it works
============
After the recordings are ready following steps take place:

1. **Apply high-pass filter**. This step will reduce strength of any signal below 1500 Hz. Previous experiments have demonstrated that kiwi rarely show any vocalization below this value. It also helps to eliminate bird calls which are of no interest to the user, e.g. morepork.
2. **Find Regions of Interest** (ROIs), defined as any signal different than background noise. Since length of a single kiwi call is roughly constant, ROI length is fixed to one second. First onsets are found by calculating local energy of the input spectral frame and taking those above certain dynamically-assessed threshold. Then from the detected onset a delay of -0.2s is taken to compensate for possible discontinuities. End of ROI is defined as +0.8s after beginning of the onset, summing to 1s interval. The algorithm is made sensitive, since the potential cost of not including kiwi candidate in a set of ROIs is much higher then adding noise-only ROI.
3. **Reduce noise**. Since ROIs are identified, Noise-Only Regions (NORs) can be estimated as anything outside ROIs (including some margin). Based on NORs spectral subtraction is performed: knowing noise spectrum we can try to eliminate noise over whole sample.
4. **Calculate Audio Features** Those features will serve as a kiwi audio signature, allowing to discriminate kiwi male from female - and a kiwi from any other animals. Audio Features are calculated with Yaafe library. On its [project page](http://yaafe.sourceforge.net/features.html) a complete description of above-mentioned features can be found. For each ROI following features are calculated:
   - spectral flatness
   - perceptual spread
   - spectral rolloff
   - spectral decrease
   - spectral shape statistics
   - spectral slope
   - Linear Predictive Coding (LPC)
   - Line Spectral Pairs (LSP)
5. **Perform kiwi identification**. At this stage Audio Features are extracted from the recording. Based on these, a Machine Learning algorithm, that is Support Vector Machine (SVM), will try to classify ROI as kiwi male, kiwi female and not a kiwi. Additional rules are then applied, employing our knowledge on repetitive character of kiwi calls. Only in case a sufficiently long set of calls is identified, the kiwi presence is marked. 
6. **Report**. Algorithm output can be: female, male, male and female and no kiwi detected.

Todd's Notes
=============

### Plan
- Create db with table to store data features/labels
- Run code for home sounds then dog barks
  - X = np.nan_to_num(features)
  - save X and labels 0 for home sound, 1 for dog bark
- Then load all features and run scaling preprocessor
  - X_scaled = preprocessing.scale(X)
  - pickle.dump( X_scaled, open("/home/osboxes/Desktop/Ornithokrites/scaler2.pkl", "wb" ) )
- Then run
  - clf = svm.SVC()
  - clf.fit(X_scaled, y) where y is array of labels
- Then save this fit to can test
  - pickle.dump( clf, open( "/home/osboxes/Desktop/Ornithokrites/model2.pkl", "wb" ) )
- Then later can loaded
  - clf2 = pickle.loads("/home/osboxes/Desktop/Ornithokrites/scaler2.pkl") # check syntax
- To test against new
  - first preprocess new sample
  - X = np.nan_to_num(features)
  - X = self._scaler.transform(X)
  - P = self._model.predict(X)
  - clf2.predict([[2., 2.]])

### Debug
import code; code.interact(local=dict(globals(), **locals()))

import inspect
inspect.getmembers(self)
wrap len() around object for length
wrap type() around object for type

### Audio manipulation
Pad audio file with 5 seconds of silence at beginning and end of file
sox Bark2.wav Bark2longer.wav pad 5 5

#!/bin/bash
for filename in kiwidata/george/*.wav; do 
  sox "$filename" kiwidata/test/"$(basename "$filename" .wav)_long.wav" pad 2 2 
done

Append all wav files to all_barks.wav
sox $(ls *.wav) all_barks.wav

Convert m4a's from iPhone recording to wav
for f in *.m4a; do avconv -i "$f" "${f/%m4a/wav}"; done

# Record 1 second
arecord -D hw:1,0 -f s16_le -r 44100 -d 1 -q > tmp/record.wav

# Record 10 seconds
sox -b 32 -e unsigned-integer -r 96k -c 2 -d --clobber --buffer $((96000*2*10)) /tmp/soxrecording.wav trim 0 10

### Store features in postgres database
createdb calm_dog
psql -d calm_dog

CREATE TABLE data (
    text_label      text,
    label           integer,
    features        float8[]
);

### Access db from python
import psycopg2
conn = psycopg2.connect("dbname='calm_dog' user='osboxes' host='localhost' password='osboxes'")
cur = conn.cursor()

# Delete previous entries
cur.execute("DELETE FROM data")
conn.commit()

### Insert features into db
cleaned_features = np.nan_to_num(features)

# For importing the barks into db
for feature in cleaned_features:
  cur.execute(
      """INSERT INTO data (text_label, label, features)
         VALUES (%s, %s, %s);""",
       ("bark", 1, list(feature)))

# For importing the house noises into db
for feature in cleaned_features:
  cur.execute(
      """INSERT INTO data (text_label, label, features)
         VALUES (%s, %s, %s);""",
       ("house", 0, list(feature)))

conn.commit()
conn.rollback()
conn.close()

### Retrieve rows from db
cur.execute("""SELECT * from data""")
rows = cur.fetchall()

### Manipulate retrieved data
Convert numpy.ndarray to list then back to ndarray
np.asarray(list(X))

rows[0][2] # is features array
rows[0][1] # is label

copied_features = np.ndarray(shape=(110,11), dtype=float, order='C')
labels = [] # This is a python list

i = 0
for feature in rows:
  labels.append(rows[i][1]) # Add label to labels list
  copied_features[i] = rows[i][2] # Add features array
  i += 1

#### Perform preprocessing
Create New Preprocessor so can apply it later to testing data
copied_features_scaled = preprocessing.StandardScaler().fit(copied_features)

### Save Preprocessor and Model to files
pickle.dump(copied_features_scaled, open( "/home/osboxes/Desktop/Ornithokrites/scaler2.pkl", "wb" ) )

### Create fit
clf = svm.SVC()
clf.fit(copied_features_scaled, labels) 

### Save fit model
pickle.dump(clf, open( "/home/osboxes/Desktop/Ornithokrites/model2.pkl", "wb" ) )

### Predict whether passed in feature is bark or house noise
- scaler_path = os.path.join(app_config.program_directory, 'scaler3.pkl')
- model_path = os.path.join(app_config.program_directory, 'model2.pkl')
- with open(model_path, 'rb') as model_loader, open(scaler_path, 'rb') as scaler_loader:
      self._model = pickle.load(model_loader)
      self._scaler = pickle.load(scaler_loader)
- Obtain audio clip
- clean_clip = np.nan_to_num(clip)
- processed_clip = 
clf.predict(test_feature)

