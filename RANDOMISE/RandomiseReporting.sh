#!/bin/bash

# Really simple script to find the significant results from
# randomise analyses and report some summary statistics from them

file=$1

range=(`fslstats ${file} -R`)
sig=(`echo "${range[1]} > 0.95" | bc -l`)
extent=(`fslstats ${file} -l 0.95 -v`)
coord_max=(`fslstats ${file} -x`)
cluster ###BETTER!!