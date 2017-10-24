#include <stdio.h>
#include <stdlib.h>
#include <vlc/vlc.h>
#include <unistd.h>
#include <time.h>
#include <inttypes.h>
#include <string.h>

#define MAX_LOG_LINE_LENGTH 10240

void onVlcBuffering(const libvlc_event_t* event, void* userData);
void onLogCallback(void* data, int level, const libvlc_log_t *log, const char *fmt, va_list ap);
int64_t getMilliseconds();
int getTime();
void reportEvent(char * tag ,char* msg);


int main(int argc, char* argv[])
{
	char* state2string[]={ "NothingSpecial","Opening","Buffering","Playing","Paused","Stopped","Ended","Error"};

	FILE* fp;

	int last_displayed=0;
	int last_check_time=0;
	int last_fps_zero=0;
	int last_lost=0;
	int lost_sum=0;
	float fps=0;

	libvlc_instance_t * inst;
	libvlc_media_player_t *mp;
	libvlc_media_t *m;

	fp=fopen("vlc.log","w");
	if ( fp == NULL )
	{
		return 1;
	}
	fclose(fp);

	fp=fopen("report.csv","w");
	if ( fp == NULL )
	{
		return 1;
	}
	fclose(fp);


	while(1)
	{
		/* Load the VLC engine */
		inst = libvlc_new (0, NULL);
		libvlc_log_set(inst,onLogCallback,NULL);

		last_displayed=0;
		last_check_time=0;
		last_fps_zero=0;
		last_lost=0;
		/* Create a new item */
		m = libvlc_media_new_location (inst, argv[1]);

		/* Create a media player playing environement */
		mp = libvlc_media_player_new_from_media (m);

		libvlc_event_manager_t* eMan = libvlc_media_player_event_manager(mp);
		libvlc_event_attach(eMan,libvlc_MediaPlayerBuffering,onVlcBuffering,NULL);

		/* play the media_player */
		libvlc_media_player_play (mp);

		while (1)
		{
			libvlc_media_stats_t stats;
			libvlc_state_t state_media;
			libvlc_state_t state_player;
			state_media=libvlc_media_get_state(m);
			state_player=libvlc_media_player_get_state(mp);

			if ( state_media == 0 || state_media == 1 ) continue;
			int err = libvlc_media_get_stats(m,&stats);
			if (err)
			{
				int now_time=time(NULL);

				unsigned int width=0;
				unsigned int height=0;

				if (now_time == last_check_time) continue;

				if(last_check_time != 0 )
				{
					fps=stats.i_displayed_pictures-last_displayed;
					fps=fps/(now_time-last_check_time);
				}

				last_lost = stats.i_lost_pictures;
				libvlc_video_get_size(mp,0,&width,&height);

				FILE* fp=fopen("report.csv","a");
				if ( fp == NULL )
				{
					printf("Unable to open report.csv\n");
					break;
				}

				fprintf(fp,"%d;",now_time);
				fprintf(fp,"STATUS;");
				fprintf(fp,"%d;",last_lost+lost_sum);
				fprintf(fp,"%d;",stats.i_displayed_pictures);
				fprintf(fp,"%f;",fps);
				fprintf(fp,"%d;",height);
				fprintf(fp,"%d;",width);
				fprintf(fp,"%s;",state2string[state_media]);
				fprintf(fp,"%s;\n",state2string[state_player]);

				fclose(fp);

				printf("Lost %d ",last_lost+lost_sum);
				printf("Displayed %d ",stats.i_displayed_pictures);
				printf("FPS %f ",fps);
				printf("W %d H %d ",width,height);
				printf("M=%s ",state2string[state_media]);
				printf("MP=%s\n",state2string[state_player]);

				last_check_time=time(NULL);
				last_displayed=stats.i_displayed_pictures;

				if ( fps < 1 && fps > -1 ) last_fps_zero++;

				if ( last_fps_zero == 5 ) break;
			}
			if (state_player == 6 ||
				state_player == 7 ||
				state_media == 6 ||
				state_media == 7 )
			{
				break;
			}
			sleep(2);
		}
		lost_sum += last_lost;

		/* Stop playing */
		libvlc_media_player_stop (mp);

		/* Free the media_player */
		libvlc_media_player_release (mp);

		/* No need to keep the media now */
		libvlc_media_release (m);

		libvlc_release (inst);

		reportEvent("RESPAWN","");
	}


	return 0;
}


int64_t getMilliseconds()
{
	struct timespec t;
	clock_gettime(CLOCK_REALTIME,&t);
	return t.tv_sec*INT64_C(1000)+t.tv_nsec/1000000;
}

int getTime()
{
	return time(NULL);
}

void onVlcBuffering(const libvlc_event_t* event, void* userData)
{
	float percent = (float) event->u.media_player_buffering.new_cache;

	FILE* fp=fopen("report.csv","a");
	if ( fp == NULL )
	{
		printf("Unable to open report.csv\n");
		exit(1);
	}

//	fprintf(fp,"%"PRId64";",getMilliseconds());
	fprintf(fp,"%d;",getTime());
	fprintf(fp,"BUFFERING;");
	fprintf(fp,"%f%%;\n",percent);
	fclose(fp);

	printf("BUFFERING %f%%\n",percent);
}


void reportEvent(char * tag ,char* msg)
{
	FILE* fp=fopen("report.csv","a");
	if ( fp == NULL )
	{
		printf("Unable to open report.csv\n");
		exit(1);
	}

//	fprintf(fp,"%"PRId64";",getMilliseconds());
	fprintf(fp,"%d;",getTime());
	fprintf(fp,"%s;",tag);
	fprintf(fp,"%s;\n",msg);
	fclose(fp);

	printf("%s '%s'\n",tag,msg);
}

void onLogCallback(void* data, int level, const libvlc_log_t *log,
			const char *fmt, va_list ap)
{
	FILE* fp=fopen("vlc.log","a");
	if ( fp == NULL )
	{
		printf("Unable to open vlc.log\n");
		exit(1);
	}

	const char* name;
	const char* header;
	char buffer[10240];

	libvlc_log_get_object(log,&name,&header,NULL);
	vsprintf(buffer,fmt,ap);
	fprintf(fp,"%"PRId64";",getMilliseconds());
	fprintf(fp,"Level %d Module '%s' Header '%s' %s\n",level,name,header,buffer);
	fclose(fp);

	if(strcmp(name,"audio output") == 0 )
	{
		if( strstr(buffer,"deferring start") != NULL ) reportEvent("WARNING_EVENT",buffer);
		else if( strstr(buffer,"starting late") != NULL ) reportEvent("WARNING_EVENT",buffer);
		else if( strstr(buffer,"underflow") != NULL ) reportEvent("ERROR_EVENT",buffer);
		else if( strstr(buffer,"playback too early") != NULL ) reportEvent("WARNING_EVENT",buffer);
		else if( strstr(buffer,"playback way too early") != NULL ) reportEvent("ERROR_EVENT",buffer);
	}
	else if ( strcmp(name,"video output") == 0 )
	{
		if( strstr(buffer,"picture is too late to be displayed") != NULL ) reportEvent("ERROR_EVENT",buffer);
	}
	else if ( strcmp(name,"decoder") == 0 )
	{
		if( strstr(buffer,"More than") != NULL ) reportEvent("ERROR_EVENT",buffer);
	}
	else if ( strcmp(name,"input") == 0 )
	{
		if( strstr(buffer,"ES_OUT_SET_(GROUP_)PCR is caled too late") != NULL ) reportEvent("ERROR_EVENT",buffer);
	}
	else if ( strcmp(name,"stream") == 0 )
	{
		if( strstr(buffer,"playback in danger of stalling") != NULL ) reportEvent("ERROR_EVENT",buffer);
		else if ( strstr(buffer,"predicted to take") != NULL ) reportEvent("ERROR_EVENT",buffer);
	}
}
