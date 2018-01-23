#!/usr/bin/env python3

import csv
import sys
import os
import numpy as np


if ( len(sys.argv) < 4 ):
	print(sys.argv[0]+" meter_filename bwm_ng_csv_filename output_filename")
	sys.exit(1)

xstep=240

lbl_height=32

out_filename=sys.argv[3]

bffile="tmp/boutput.csv"

gnuplot = open("tmp/graph.plt","w")

gnuplot.write("set datafile separator ';'\n")
gnuplot.write("set output '"+out_filename+"'\n")
gnuplot.write("set lmargin 10\n")

gnuplot.write("set terminal pngcairo size 1024,960 enhanced font 'Verdana,20'\n")
gnuplot.write("set xlabel 'Tempo (s)'\n")

gnuplot.write("set multiplot layout 2,1\n")
gnuplot.write("set ylabel 'FPS'\n")
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

#gnuplot.write("set label '4 CPU' at "+str(xstep/2-10)+","+str(lbl_height)+"\n")
gnuplot.write("set label '4 CPU' at "+str(5)+","+str(lbl_height)+"\n")

lost=0
last_fps=0
last_width=0
last_height=0
xstart=0
xend=0
xthreshold1=0
xthreshold2=0
tipo="nosdo"
xstartchange=0
xendchange=0

#fake_data=[]


sumb=0
mlen=1
r=0
for row in report:
	record_type = row[1]

	if ( record_type == "EVENT" ):
		timestamp = int(row[0])

		msg = row[2]

		if ( xstart == 0 ):
			xthreshold1=timestamp
			xstart = timestamp - xstep
		elif ( xend == 0 ):
			xthreshold2=timestamp
			xend = timestamp + xstep

		gnuplot.write("set arrow from "+str(timestamp-xstart)+", graph 0 to "+str(timestamp-xstart)+", graph 1 nohead\n")
#		gnuplot.write("set label '"+msg+"' at "+str(timestamp-xstart+xstep/2-10)+","+str(lbl_height)+"\n")
		gnuplot.write("set label '"+msg+"' at "+str(timestamp-xstart+5)+","+str(lbl_height)+"\n")

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

		fps = float(row[4])
		last_fps = fps
		lost = int(row[2])
		height =  int(row[5])
		width = int(row[6])

		if ( height > 400 and xstartchange == 0 ):
			tipo="sdo"
			xstartchange=timestamp-xstart
			mlen = 1
			sumb = 0
			r = 1
		elif ( height < 400 and xstartchange > 0 and xendchange == 0):
			xendchange=timestamp-xstart
			mlen = 1
			sumb = 0
			r = 2

		if ( width != 0 ):
			last_width = width
		else:
			width = last_width

		if ( height != 0 ):
			last_height = height
		else:
			height = last_height

		bitrate = 0
		if ( fps != 0 ):
			bitrate = float(row[7])

#			if (  r == 0 ):
#				fake_data.append(bitrate)

#			if ( tipo == "sdo" and r == 1 ):
#				noise = np.random.normal(0,0.5)*100
#				bitrate = fake_data.pop() + noise

#		if ( r == 0 and int(row[0]) > int(xthreshold1) and int(xthreshold1) > 0):
#		elif ( r == 1 and int(row[0]) > int(xthreshold2) and int(xthreshold2) > 0):

		sumb = sumb + float(bitrate)
		writer.writerow([timestamp,fps,lost,height,width,bitrate,sumb/mlen])
		mlen = mlen +1
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
sumtx=0
sumrx=0
mlen=1
r=0
for row in breader:
	if ( int(row[0]) >= int(xstart) ):
		if ( r == 0 and int(row[0]) > int(xthreshold1) ):
			mlen = 1
			sumtx = 0
			sumrx = 0
			sumb = 0
			r = 1 
		if ( r == 1 and int(row[0]) > int(xthreshold2) ):
			mlen = 1
			sumtx = 0
			sumrx = 0
			sumb = 0
			r = 2

		sumtx = sumtx + float(row[2])
		sumrx = sumrx + float(row[3])
		sumb = sumb + float(row[6])
		newrow=[row[0],0,row[2],row[3],sumtx/mlen,sumrx/mlen,sumb/mlen]
		bwriter.writerow(newrow)
		mlen = mlen + 1

bout.close()
bandwidthfile.close()

if ( tipo == "sdo"):
	gnuplot.write("set title 'with self-orchestrator module'\n")
else:
	gnuplot.write("set title 'without self-orchestrator module'\n")

gnuplot.write("set yrange [0:35]\n")

gnuplot.write("set xrange [0:"+str(xend-xstart)+"]\n")

gnuplot.write("init(x) = ( sum = 0 )\n")

gnuplot.write("plot sum = init(0), \\\n")
gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):2 t'FPS' with line, \\\n")
#gnuplot.write("\t'' using ($1-"+str(xstart)+"):(sum = sum + $2, sum/($0+1)) t'AVG FPS' with line, \\\n")
#gnuplot.write("\t'' using ($1-"+str(xstart)+"):3 t'Frame lost' with line, \\\n")
gnuplot.write("\t'tmp/output_error.csv' using ($1-"+str(xstart)+"):2 t'Errors', \\\n")
gnuplot.write("\t'tmp/output_buff.csv' using ($1-"+str(xstart)+"):2 t'Buffering' \n")

#gnuplot.write("set ylabel 'Resolution (Pixel)'\n")
##gnuplot.write("set yrange [0:1200]\n")
#gnuplot.write("set autoscale\n")
#gnuplot.write("set xrange [0:"+str(xend-xstart)+"]\n")
#gnuplot.write("unset label\n")

#gnuplot.write("plot sum= init(0), \\\n")

#gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):4 t'Frame height' with line, \\\n")
#gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):5 t'Frame width' with line \n")


gnuplot.write("set ylabel 'Bandwidth usage (Kbps)'\n")
#gnuplot.write("set yrange [0:1200]\n")
gnuplot.write("set autoscale\n")
#gnuplot.write("set yrange [0:1500]\n")
gnuplot.write("set yrange [0:3000]\n")
#gnuplot.write("set yrange [0:800]\n")
gnuplot.write("set xrange [0:"+str(xend-xstart)+"]\n")
gnuplot.write("unset label\n")

#gnuplot.write("plot 'output.csv' using 1:4 t'Tx' with line, \\\n")
#gnuplot.write("\t'' using 1:5 t'Rx' with line\n")


#gnuplot.write("set arrow from graph 0,first 1148 to graph 1,first 1148 nohead lc rgb '#FF0000' front\n")
#gnuplot.write("set arrow from graph 0,first 296 to graph 1,first 296 nohead lc rgb '#0000FF' front\n")

#if ( tipo == "sdo"):
#	gnuplot.write("set arrow from 0,296 to "+str(xstartchange)+",296 nohead lc rgb '#FF0000' front\n")
#	gnuplot.write("set arrow from "+str(xstartchange)+",1148 to "+str(xendchange)+",1148 nohead lc rgb '#FF0000' front\n")
#	gnuplot.write("set arrow from "+str(xendchange)+",296 to "+str(xend-xstart)+",296 nohead lc rgb '#FF0000' front\n")
#else:
#	gnuplot.write("set arrow from 0,296 to "+str(xend-xstart)+",296 nohead lc rgb '#FF0000' front\n")


gnuplot.write("set arrow from 0,296 to "+str(xend-xstart)+",296 nohead lc rgb '#FF0000' front\n")

gnuplot.write("plot sum= init(0), \\\n")
gnuplot.write("\tNaN lc rgb '#FF0000' title 'Theoretical bitrate', \\\n")
#gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):($3*8/1000) t'Tx' with line, \\\n")
#gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):($4*8/1000) t'Rx' with line, \\\n")
#gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):($5*8/1000) t'AVG Tx' with line, \\\n")
#gnuplot.write("\t'"+bffile+"' using ($1-"+str(xstart)+"):($6*8/1000) t'AVG Rx' with line, \\\n")
gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):6 t'Bitrate' with line, \\\n")
gnuplot.write("\t'tmp/output.csv' using ($1-"+str(xstart)+"):7 t'AVG Bitrate' with line \n")



gnuplot.close()

os.system("gnuplot tmp/graph.plt");
os.system("open "+out_filename);

