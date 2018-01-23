#!/usr/bin/env python3

import csv
import sys
import os
import numpy as np

xstep=240

lbl_height=32

type=sys.argv[1]
out_filename=sys.argv[2]

bffile="tmp/boutput.csv"

gnuplot = open("tmp/graph.plt","w")

gnuplot.write("set datafile separator ';'\n")
gnuplot.write("set output '"+out_filename+"'\n")
gnuplot.write("set lmargin 10\n")

gnuplot.write("set terminal pngcairo size 1024,480 enhanced font 'Verdana,20'\n")
gnuplot.write("set xlabel 'Tempo (s)'\n")

gnuplot.write("set ylabel 'Bitrate available [Kbps]'\n")
#gnuplot.write("set autoscale\n")

outfile=open("tmp/output.csv","w")

writer = csv.writer(outfile,
			delimiter=';',
			quotechar='"',
			quoting=csv.QUOTE_MINIMAL)

for i in range(0,800):
	if (type == 'nosdo'):
		writer.writerow([i,1000])
		writer.writerow([i,350])
		writer.writerow([i,150])
	else:
		if ( i < 240 or i > 480 ):
			writer.writerow([i,1000])
			writer.writerow([i,350])
			writer.writerow([i,150])
		else:
			writer.writerow([i,350])

outfile.close()

if ( type == "sdo"):
	gnuplot.write("set title 'with self-orchestrator module'\n")
else:
	gnuplot.write("set title 'without self-orchestrator module'\n")

gnuplot.write("set yrange [0:1200]\n")

gnuplot.write("plot 'tmp/output.csv' using 1:2 t'Bitrate' with points pointtype 5")

gnuplot.close()

os.system("gnuplot tmp/graph.plt");
os.system("open "+out_filename);
