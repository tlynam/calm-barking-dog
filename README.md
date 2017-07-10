Calm your dog with machine learning
============

To listing continuously for dog barks and play `rain.wav` when a bark is detected.  I plan on being able to pass in the microphone location.
`python ornithokrites.py --stream 'stream'`

To load categorized sound files into the database.  Sound files must be in either `/barks` or `/non_barks`.
Until it's fixed, we need first to add padding to the beginning and end of sound clips.  This is because the sound clips from the stream recording are very short and aren't picked up as segments.  Edit this `add_wav_padding.sh` file and run for both barks and non_barks.

`./add_wav_padding.sh`

If you have many sound clips to load, it's much faster to join wav clips together before processing.  I found it errors with files above ~12 mb though.
`sox *.wav joined-barks.wav`

To load categorized sound clips into the database.
`python ornithokrites.py -d data/categorized_data/`

To regenerate the scaler and model.  The scaler is for normalizing the sound.
`python create_model.py`

To restore the database:
`pg_restore --verbose --clean --no-acl --no-owner -h localhost -U pi -d calm_dog calm_dog.dump`

To dump the database:
`pg_dump --username pi --verbose --clean --no-owner --no-acl --format=c calm_dog > calm_dog2.dump`

How it works (Based on the wonderful Ornithokrites project by Lukasz Tracewski)
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

Setup
=============
Following libraries are used:
- [Aubio 4.0](http://aubio.org/) - a great tool designed for the extraction of annotations from audio signals.
- [Yaafe 0.64](http://yaafe.sourceforge.net/) - an audio features extraction toolbox with load of features to choose from.
- [scikit-learn 0.14.1](http://scikit-learn.org/) - powerful Machine Learning library.
- [NumPy 1.8.1](http://www.numpy.org/), [SciPy 0.13.3](http://www.scipy.org/) - canonical Python numerical libraries.
