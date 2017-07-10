#!/bin/bash
for filename in data/categorized_data/barks/*.wav; do
  sox "$filename" data/categorized_data/barks/"$(basename "$filename" .wav)_long.wav" pad 3 3
done
