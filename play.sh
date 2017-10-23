#!/bin/bash

while [ 1 ]; do
	./vlc.out http://192.168.40.10:1935/live/live_160p/playlist.m3u8
	sleep 1
done
