#!/usr/bin/env python3

import csv
import sys
import os


xstep=240
xstart=0
xend=0

lbl_height=32

out_filename=sys.argv[3]

bffile="tmp/boutput.csv"

gnuplot = open("tmp/graph.plt","w")

gnuplot.write("set datafile separator ';'\n")
gnuplot.write("set output '"+out_filename+"'\n")
gnuplot.write("set lmargin 10\n")

gnuplot.write("set terminal pngcairo size 1024,960 enhanced font 'Verdana,10'\n")
gnuplot.write("set xlabel 'Tempo (s)'\n")

gnuplot.write("set multiplot layout 2,1\n")
gnuplot.write("set ylabel 'FPS'\n")
gnuplot.write("set title 'Self-orchestrator validation'\n")
#gnuplot.write("set autoscale\n")

reportfile=open(sys.argv[1],'r')

outfile=open("tmp/output.csv","w")

outfile_error=open("tmp/output_error.csv","w")

outfile_buff=open("tmp/output_buff.csv","w")

report = csv.reader(reportfile,
			delimiter=';')

writer = csv.writer(outfile,
			delimiter=';',
			quotechar='"',
			quoting=csv.QUOTE_MINIMAL)

writer_err = csv.writer(outfile_error,
			delimiter=';',
			quotechar='"',
			quoting=csv.QUOTE_MINIMAL)

writer_buff = csv.writer(outfile_buff,
			delimiter=';',
			quotechar='"',
			quoting=csv.QUOTE_MINIMAL)


gnuplot.write("set label '4 CPU' at "+str(xstep/2-10)+","+str(lbl_height)+"\n")

lost=0
last_fps=0
last_width=0
last_height=0

for row in report:
	record_type = row[1]

	if ( record_type == "EVENT" ):
		timestamp = int(row[0])

		msg = row[2]

		if ( xstart == 0 ):
			xstart = timestamp - xstep
		elif ( xend == 0 ):
			xend = timestamp + xstep

		gnuplot.write("set arrow from "+str(timestamp-xstart)+", graph 0 to "+str(timestamp-xstart)+", graph 1 nohead\n")
		gnuplot.write("set label '"+msg+"' at "+str(timestamp-xstart+xstep/2-10)+","+str(lbl_height)+"\n")

	elif ( record_type == "ERROR_EVENT" ):
		if ( len(row[0]) > 10 ):
			timestamp = int(row[0])/1000
		else:
			timestamp = int(row[0])

		msg = row[2]

#		gnuplot.write("set label  at "+str(timestamp)+","+str(last_fps)+" '' point pointtype 2 pointsize 1 lc rgb 'red'\n")
		writer_err.writerow([timestamp,last_fps])

	elif ( record_type == "BUFFERING" ):
		if ( len(row[0]) > 10 ):
			timestamp = int(row[0])/1000
		else:
			timestamp = int(row[0])

		msg = row[2]

#		gnuplot.write("set label  at "+str(timestamp)+","+str(last_fps)+" '' point pointtype 4 pointsize 1 lc rgb 'blue'\n")

		writer_buff.writerow([timestamp,last_fps])

	elif ( record_type == "STATUS" ):
		timestamp = int(row[0])

		fps = row[4]
		last_fps = fps
		lost = row[2]
		height =  int(row[5])
		width = int(row[6])

		if ( width != 0 ):
			last_width = width
		else:
			width = last_width

		if ( height != 0 ):
			last_height = height
		else:
			height = last_height

		writer.writerow([timestamp,fps,lost,height,width])
	else:
#		print("Invalid record type:",record_type)
		pass


reportfile.close()
outfile.close()
outfile_error.close()
outfile_buff.close()

bandwidthfile=open(sys.argv[2],'r')
bout=open(bffile,"w")


breader = csv.reader(bandwidthfile,
			delimiter=';')

bwriter = csv.writer(bout,
			delimiter=';',
			quotechar='"',
			quoting=csv.QUOTE_MINIMAL)

for row in breader:
	if ( int(row[0]) >= int(xstart) ):
		bwriter.writerow(row)

bout.close()
bandwidthfile.close()

gnuplot.write("set yrange [0:35]\n")

gnuplot.write("set xrange [0:"+str(xend-xstart)+"]\n")

gnuplot.write("init(x) = ( sum = 0 )\n")

gnuplot.write("plot sum = init(0), \\\n")
gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):2 t'FPS' with line, \\\n")
gnuplot.write("\t'' using ($1-"+str(xstart)+"):(sum = sum + $2, sum/($0+1)) t'AVG FPS' with line, \\\n")
gnuplot.write("\t'' using ($1-"+str(xstart)+"):3 t'Frame lost' with line, \\\n")
gnuplot.write("\t'tmp/output_error.csv' using ($1-"+str(xstart)+"):2 t'Errors', \\\n")
gnuplot.write("\t'tmp/output_buff.csv' using ($1-"+str(xstart)+"):2 t'Buffering' \n")

gnuplot.write("set ylabel 'Bandwidth usage (MBps)'\n")
#gnuplot.write("set yrange [0:1200]\n")
gnuplot.write("set autoscale\n")
gnuplot.write("set xrange [0:"+str(xend-xstart)+"]\n")
gnuplot.write("unset label\n")

#gnuplot.write("plot 'output.csv' using 1:4 t'Tx' with line, \\\n")
#gnuplot.write("\t'' using 1:5 t'Rx' with line\n")

gnuplot.write("plot sum= init(0), \\\n")
gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):($3/1024/1024*8) t'Tx' with line, \\\n")
gnuplot.write("\t'' using ($1-"+str(xstart)+"):($4/1024/1024*8) t'Rx' with line, \\\n")
gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):(sum = sum + $3/1024/1024*8, sum/($0+1)) t'AVG TX' with line, \\\n")
gnuplot.write("\tsum=init(0), \\\n")
gnuplot.write("\t'' using ($1-"+str(xstart)+"):(sum = sum + $4/1024/1024*8, sum/($0+1)) t'AVG RX' with line \n")


gnuplot.close()

os.system("gnuplot tmp/graph.plt");
os.system("open "+out_filename);

