#!/bin/bash
for filename in data/categorized_data/non_barks_short/*.wav; do
  sox "$filename" data/categorized_data/non_barks/"$(basename "$filename" .wav)_long.wav" pad 3 3
done
