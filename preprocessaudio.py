import pandas as pd
import numpy as np
import scipy.io as sc
from scipy.io import wavfile
import os as os
import argparse as agp
from pydub import AudioSegment
from pydub.playback import play
import subprocess
import math
import random
import datetime
from datetime import timedelta
from pytz import timezone
import seaborn as sns
import matplotlib.pyplot as plt

# -----------------------------------------------------------
# Global variables that should be changed
# -----------------------------------------------------------

main_output_folder = "/Users/arjun/Box/box-group-lena-studies/Soundscape/ucsf_app_stuff"
main_input_folder = "/Users/arjun/Box/box-group-lena-studies/Soundscape/wavFiles"

class Child():
    def __init__(self, id):
        self.id = id
        self.sorted_ctccount = None
        self.ctc_timestamps_main = None
        self.chn_timestamps_main = None
        self.long_CTCs_offsets =  []
        self.long_CHN_offsets =  []
        self.rate = None
        self.wavdata = None

    def do_extraction(self):
        directory = main_input_folder
        wavpath = os.path.join(directory, self.id +".wav")
        self.rate, self.wavdata = wavfile.read(wavpath)
        self.ctc_timestamps_main= pd.read_csv(os.path.join(directory,self.id+'_CTC_output', self.id+'_CTC_timestamps.csv'))
     
    def prepare_CTCclips(self):
        '''
        This function prepares a dataframe with clips arrranged in descending order of CTC count
        '''
        self.sorted_ctccount = self.ctc_timestamps_main.sort_values(by=['convo_count'], ascending=0, ignore_index = 1) 
    
    
    def extract_clips_longCTC (self):
        '''
        This function extracts and saves the clip with the longest CT measured by convo count, not duration.
        It also extracts the top 15 clips based on CTC count length.
        '''
        directory = main_input_folder
        path = os.path.join(directory, self.id+".wav")
        
        self.prepare_CTCclips()
        upperbound = 15
        
        if (15>=len(self.sorted_ctccount)):
            upperbound = len(self.sorted_ctccount)
            
        for i in range(0 , upperbound):
            start, ending = self.sorted_ctccount.at[i,'clip_onset'] , self.sorted_ctccount.at[i,'clip_offset']
            split_at_frame = math.floor(self.rate * start)
            stop_at_frame = math.ceil(self.rate * ending)
            left_data  = self.wavdata[split_at_frame : stop_at_frame] 
            self.long_CTCs_offsets.append((start,ending)) 
            newfolder = os.path.join(main_output_folder,self.id+"_CTCclips")
            os.makedirs(newfolder, exist_ok=True)
            newpath = os.path.join(newfolder, self.id+ "_longCTC"+str(i)+".wav")
            wavfile.write(newpath, self.rate, left_data)

        items = self.long_CTCs_offsets
        newpathfile = os.path.join(newfolder, self.id+ "_longCTCoffsets.txt")
        file = open(newpathfile,'w')
        file.write('\n'.join('{} {}'.format(item[0],item[1]) for item in items))
        file.close()



    def extract_clips_longVoc (self):
        '''
        This function extracts and saves the clips with the top 15 longest child utterances based on time duration.
        '''
        filepath_of_csv = os.path.join(main_input_folder, self.id+ "_voc_output", self.id+"_CHN_timestamps.csv")
    
        self.chn_timestamps_main = pd.read_csv(filepath_of_csv)
        utterances_df = self.chn_timestamps_main[self.chn_timestamps_main['childUttCnt']!=0]
        sorted_chn_length  = utterances_df.sort_values(by=['duration'], ascending=0, ignore_index = 1)
    
        upperbound = 15

        if (15>=len(sorted_chn_length)):
            upperbound = len(sorted_chn_length)
            
        for i in range(0 , upperbound):
            start, ending = sorted_chn_length.at[i,'onset'] , sorted_chn_length.at[i,'offset']
            split_at_frame = math.floor(self.rate * start)
            stop_at_frame = math.ceil(self.rate * ending)
            left_data  = self.wavdata[split_at_frame : stop_at_frame] 
            self.long_CHN_offsets.append((start,ending))  
            newfolder = os.path.join(main_output_folder, self.id+"_CHNclips")
            os.makedirs(newfolder, exist_ok=True)
            newpath = os.path.join(newfolder , self.id+ "_longVoc"+str(i)+".wav")
            wavfile.write(newpath, self.rate, left_data)
        
        items = self.long_CHN_offsets
        newpathfile = os.path.join(newfolder, self.id+ "_longCHNoffsets.txt")
        file = open(newpathfile,'w')
        file.write('\n'.join('{} {}'.format(item[0],item[1]) for item in items))
        file.close()

    def create_MAN_speed_graph(self):

        '''
        This function creates a plot of male talking speed by mining MAN timestamps and saves it in the output directory. This has binning done w.r.t. values of offsets.
        '''

        filepath_of_csv = os.path.join(main_input_folder, self.id+ "_speech_output", self.id+"_MAN_timestamps.csv")
        man_timestamps_main = pd.read_csv(filepath_of_csv)
        man_timestamps1 = man_timestamps_main
        man_timestamps1['value_bin']=pd.cut(man_timestamps_main['clip_offset'], 20, labels=[x for x in range(1,21)])
        man_timestamps1['freq_bin']=pd.qcut(man_timestamps_main['clip_offset'], 20, labels=[x for x in range(1,21)])
        man_vbin_offset_df = man_timestamps1.groupby('value_bin').agg({'duration': 'sum', 'wordCount': 'sum', 'clip_offset':'max'})
        man_vbin_offset_df['hourly_offset'] = man_vbin_offset_df['clip_offset']/3600
        man_vbin_offset_df['avg_speed_recorded'] = man_vbin_offset_df['wordCount']/man_vbin_offset_df['duration']

        man_vbin_offset_df.dropna(inplace=True)

        truncated_x = ['{:.2f}'.format(t) for t in man_vbin_offset_df['hourly_offset']]
        truncated_y = [round(t,2) for t in man_vbin_offset_df['avg_speed_recorded']]
        ax = sns.barplot(x = man_vbin_offset_df['hourly_offset'], y = truncated_y, palette = "ch:s=.25,rot=-.25",edgecolor='black')
        ax.bar_label(ax.containers[0], fontsize=12)
        sns.set(rc={'figure.figsize':(12,8)})
        sns.set_theme(style='white')
        plt.xticks(rotation=0)
        ax.set_xticklabels(truncated_x)
        plt.xlabel('No. of hours into the recording', fontsize=16)
        plt.ylabel('Average no. of words/sec', fontsize=16)
        plt.title("Average male speech rate (words/sec) around child", fontsize=20)

        newfolder = os.path.join(main_output_folder, self.id+"_plots")
        os.makedirs(newfolder, exist_ok=True)
        newpath = os.path.join(newfolder, self.id+ "_MANspeed_vbin.png")
        plt.savefig(newpath, bbox_inches = 'tight')
        plt.close()

    # Not that useful now
    ''' 
    def create_FAN_speed_graph(self):

        
        This function creates a plot of male talking speed by mining MAN timestamps and saves it in the output directory. This has binning done w.r.t. values of offsets.
         

        filepath_of_csv = os.path.join(main_input_folder, self.id+ "_speech_output", self.id+"_FAN_timestamps.csv")
        fan_timestamps_main = pd.read_csv(filepath_of_csv)
        fan_timestamps1 = fan_timestamps_main
        fan_timestamps1['value_bin']=pd.cut(fan_timestamps_main['clip_offset'], 20, labels=[x for x in range(1,21)])
        fan_timestamps1['freq_bin']=pd.qcut(fan_timestamps_main['clip_offset'], 20, labels=[x for x in range(1,21)])
        fan_vbin_offset_df = fan_timestamps1.groupby('value_bin').agg({'duration': 'sum', 'wordCount': 'sum', 'clip_offset':'max'})
        fan_vbin_offset_df['hourly_offset'] = fan_vbin_offset_df['clip_offset']/3600
        fan_vbin_offset_df['avg_speed_recorded'] = fan_vbin_offset_df['wordCount']/fan_vbin_offset_df['duration']

        fan_vbin_offset_df.dropna(inplace=True)

        truncated_x = ['{:.2f}'.format(t) for t in fan_vbin_offset_df['hourly_offset']]
        truncated_y = [round(t,2) for t in fan_vbin_offset_df['avg_speed_recorded']]
        ax = sns.barplot(x = fan_vbin_offset_df['hourly_offset'], y = truncated_y, palette = "ch:s=.25,rot=-.25",edgecolor='black')
        ax.bar_label(ax.containers[0], fontsize=11)
        sns.set(rc={'figure.figsize':(16,8)})
        sns.set_theme(style='white')
        plt.xticks(rotation=30)
        ax.set_xticklabels(truncated_x)
        plt.xlabel('No. of hours into the recording', fontsize=16)
        plt.ylabel('Average no. of words/sec', fontsize=16)
        plt.title("Average female speech rate (words/sec) around child", fontsize=20)

        newfolder = os.path.join(main_output_folder, self.id+"_plots")
        os.makedirs(newfolder, exist_ok=True)
        newpath = os.path.join(newfolder, self.id+ "_FANspeed_vbin.png")
        plt.savefig(newpath, bbox_inches = 'tight')
        plt.close()
    '''

    def create_dayspeed_graphs(self, mf:str):
        #Preprocessing of data

        if mf =='MAN':
            filepath_of_csv = os.path.join(main_input_folder, self.id+ "_speech_output", self.id+"_MAN_timestamps.csv")
            graphtitle = "Average male speech rate (words/sec) around child"
            graphfile = "_MANdayspeeds.png"
        else:
            filepath_of_csv = os.path.join(main_input_folder, self.id+ "_speech_output", self.id+"_FAN_timestamps.csv")
            graphtitle = "Average female speech rate (words/sec) around child"
            graphfile = "_FANdayspeeds.png"

        man_timestamps_main = pd.read_csv(filepath_of_csv)
        man_timestamps_main['words_per_sec'] = man_timestamps_main['wordCount']/man_timestamps_main['duration']
      
        infocsvpath = os.path.join(main_input_folder , self.id + "_speech_output",   self.id+"_its_info.csv")  
        itsinfocsv = pd.read_csv(infocsvpath)
        start_datetime_str = str(itsinfocsv['startClockTime'][0])
        end_datetime_str = str(itsinfocsv['endClockTime'][0]) 

        start_datetime_object = datetime.datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        end_datetime_object = datetime.datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%SZ')

        og_start_time = start_datetime_object.replace(tzinfo=datetime.timezone.utc)
        og_end_time  = end_datetime_object.replace(tzinfo=datetime.timezone.utc)

        if (self.id.find('L')>=0 or self.id.find('M')>=0  or  self.id.find('D')>=0  or self.id.find('E')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/Chicago'))
                    actual_time_of_end =  og_end_time.astimezone(timezone('America/Chicago'))

        elif (self.id.find('R')>=0 or self.id.find('J')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/New_York'))
                    actual_time_of_end = og_end_time.astimezone(timezone('America/New_York'))
        
        start_bucket = actual_time_of_start.hour+1
        if (actual_time_of_start.day < actual_time_of_end.day):
            end_bucket = actual_time_of_end.hour + 25
        else:
            end_bucket = actual_time_of_end.hour + 1
        secs_until_closest_hour = 3600 - actual_time_of_start.minute*60 - actual_time_of_start.second
        buckets = [i for i in range (start_bucket, end_bucket+1)]
        no_of_buckets = len(buckets)
        bucket_offsets = [0,secs_until_closest_hour]
        for i in range(1, no_of_buckets):
            bucket_offsets.append(secs_until_closest_hour+3600*(i))
         
        man_timestamps_main['before_hour_of_day'] = pd.cut(man_timestamps_main['clip_offset'], bins=bucket_offsets,labels=buckets, include_lowest=True, right=True)
        condensed_df = man_timestamps_main.groupby('before_hour_of_day').agg({'duration': 'sum', 'wordCount': 'sum'})
        condensed_df['avg_rate'] = condensed_df['wordCount'] / condensed_df['duration'] 
        condensed_df.fillna(0)
        
        #Plotting of graph
        xaxis = ['{}:00'.format(t) for t in buckets]
        yaxis = [round(y,2) for y in condensed_df['avg_rate']]
        ax = sns.barplot(x = buckets, y = yaxis, palette = "ch:s=.25,rot=-.25",edgecolor='black')
        ax.bar_label(ax.containers[0], fontsize=11)
        sns.set(rc={'figure.figsize':(9,6)})
        sns.set_theme(style='white')
        plt.xticks(rotation=30)
        ax.set_xticklabels(xaxis)
        plt.xlabel('Hour of the day', fontsize=14)
        plt.ylabel('Average no. of words/sec', fontsize=16)
        plt.title(graphtitle, fontsize=20)
         
        newfolder = os.path.join(main_output_folder, self.id+"_plots")
        os.makedirs(newfolder, exist_ok=True)
        newpath = os.path.join(newfolder, self.id+ graphfile)
        plt.savefig(newpath, bbox_inches = 'tight',dpi=140)
        plt.close()


    def create_day_words_graph(self,mf:str):

        #Preprocessing of data

        if mf == 'MAN':
            filepath_of_csv = os.path.join(main_input_folder , self.id  + "_speech_output", self.id +"_MAN_timestamps.csv")
            title = "Word counts of male speech around child"
            palette = 'YlGn'
            graphfile = "_MANdailywords.png"
        else:
            filepath_of_csv = os.path.join(main_input_folder , self.id + "_speech_output", self.id +"_FAN_timestamps.csv")
            title = "Word counts of female speech around child"
            palette = 'Wistia'
            graphfile = "_FANdailywords.png"

        man_timestamps_main = pd.read_csv(filepath_of_csv)
    
        infocsvpath = os.path.join(main_input_folder , self.id  + "_speech_output",   self.id +"_its_info.csv")  
        itsinfocsv = pd.read_csv(infocsvpath)
        start_datetime_str = str(itsinfocsv['startClockTime'][0])
        end_datetime_str = str(itsinfocsv['endClockTime'][0]) 

        start_datetime_object = datetime.datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        end_datetime_object = datetime.datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%SZ')

        og_start_time = start_datetime_object.replace(tzinfo=datetime.timezone.utc)
        og_end_time  = end_datetime_object.replace(tzinfo=datetime.timezone.utc)

        if (self.id.find('L')>=0 or self.id.find('M')>=0  or  self.id.find('D')>=0  or self.id.find('E')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/Chicago'))
                    actual_time_of_end =  og_end_time.astimezone(timezone('America/Chicago'))

        elif (self.id.find('R')>=0 or self.id.find('J')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/New_York'))
                    actual_time_of_end = og_end_time.astimezone(timezone('America/New_York'))
        

        start_bucket = actual_time_of_start.hour+1
        if (actual_time_of_start.day < actual_time_of_end.day):
            end_bucket = actual_time_of_end.hour + 25
        else:
            end_bucket = actual_time_of_end.hour+1
        secs_until_closest_hour = 3600 - actual_time_of_start.minute*60 - actual_time_of_start.second
        buckets = [i for i in range (start_bucket, end_bucket+1)]
        no_of_buckets = len(buckets)
        bucket_offsets = [0,secs_until_closest_hour]
        for i in range(1, no_of_buckets):
            bucket_offsets.append(secs_until_closest_hour+3600*(i))
        man_timestamps_main['before_hour_of_day'] = pd.cut(man_timestamps_main['clip_offset'], bins=bucket_offsets, labels=buckets, include_lowest=True, right=True)
        
        condensed_df = man_timestamps_main.groupby('before_hour_of_day').agg({'wordCount': 'sum'})
        
        condensed_df.fillna(0)

        #Plotting of graph
        xaxis = ['{}:00'.format(t) for t in buckets]
        yaxis = [round(y) for y in condensed_df['wordCount']]
        ax = sns.barplot(x = buckets, y = yaxis, palette = palette,edgecolor='black')
        ax.bar_label(ax.containers[0], fontsize=12)
        sns.set(rc={'figure.figsize':(9,6)})
        sns.set_theme(style='white')
        plt.xticks(rotation=0)
        ax.set_xticklabels(xaxis)
        plt.xlabel('Hour of the day', fontsize=16)
        plt.ylabel('Total words uttered', fontsize=16)
        plt.title(title, fontsize=20)

        newfolder = os.path.join(main_output_folder, self.id+"_plots")
        os.makedirs(newfolder, exist_ok=True)
        newpath = os.path.join(newfolder, self.id+ graphfile)
        plt.savefig(newpath, bbox_inches = 'tight',dpi=140)
        plt.close()

    def returnonlyone(self, mf:str):   
        #Helper function for preprocessing of data
        filepath_of_csv  = ""

        if mf == 'MAN':
            filepath_of_csv = os.path.join("/Users/arjun/Box/box-group-lena-studies/Soundscape/wavFiles" , self.id+ "_speech_output", self.id+"_MAN_timestamps.csv")
            title = "Word counts of male speech around child"
            palette = 'YlGn'

        else:
            filepath_of_csv = os.path.join("/Users/arjun/Box/box-group-lena-studies/Soundscape/wavFiles" , self.id+ "_speech_output", self.id+"_FAN_timestamps.csv")
            title = "Word counts of female speech around child"
            palette = 'Wistia'

        man_timestamps_main = pd.read_csv(filepath_of_csv)

        infocsvpath = os.path.join(main_input_folder , self.id + "_speech_output",   self.id+"_its_info.csv")  
        itsinfocsv = pd.read_csv(infocsvpath)
        start_datetime_str = str(itsinfocsv['startClockTime'][0])
        end_datetime_str = str(itsinfocsv['endClockTime'][0]) 

        start_datetime_object = datetime.datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        end_datetime_object = datetime.datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%SZ')

        og_start_time = start_datetime_object.replace(tzinfo=datetime.timezone.utc)
        og_end_time  = end_datetime_object.replace(tzinfo=datetime.timezone.utc)

        if (self.id.find('L')>=0 or self.id.find('M')>=0  or  self.id.find('D')>=0  or self.id.find('E')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/Chicago'))
                    actual_time_of_end =  og_end_time.astimezone(timezone('America/Chicago'))

        elif (self.id.find('R')>=0 or self.id.find('J')>=0):
                    actual_time_of_start = og_start_time.astimezone(timezone('America/New_York'))
                    actual_time_of_end = og_end_time.astimezone(timezone('America/New_York'))

        start_bucket = actual_time_of_start.hour+1
        if (actual_time_of_start.day < actual_time_of_end.day):
            end_bucket = actual_time_of_end.hour + 25
        else:
            end_bucket = actual_time_of_end.hour+1
        secs_until_closest_hour = 3600 - actual_time_of_start.minute*60 - actual_time_of_start.second
        buckets = [i for i in range (start_bucket, end_bucket+1)]
        no_of_buckets = len(buckets)
        bucket_offsets = [0,secs_until_closest_hour]
        for i in range(1, no_of_buckets):
            bucket_offsets.append(secs_until_closest_hour+3600*(i))
        man_timestamps_main['before_hour_of_day'] = pd.cut(man_timestamps_main['clip_offset'], bins=bucket_offsets, labels=buckets, include_lowest=True, right=True)

        condensed_df = man_timestamps_main.groupby('before_hour_of_day').agg({'wordCount': 'sum'})
        condensed_df.fillna(0)
        
        return condensed_df


    def create_combined_words_graph(self):

        #Preprocessing of data
        onlyman = self.returnonlyone('MAN')
        onlywoman = self.returnonlyone('FAN')

        result = pd.concat([onlyman, onlywoman], axis=1)
        result.columns = ['MAN','FAN']
        result = result.reset_index()
        melteddf = pd.melt(result, id_vars='before_hour_of_day', var_name="speaker", value_name="word_counts")
         

        #Plotting
        ax = sns.barplot(x='before_hour_of_day', y='word_counts', hue='speaker',palette=["yellow", "green"],data=melteddf)

        buckets = list((onlywoman.index.values))

        if len(onlyman)>len(onlywoman):
            buckets = list((onlyman.index.values))


        xaxis = ['{}:00'.format(str(t)) for t in buckets]
        ax.bar_label(ax.containers[0], fontsize=8)
        ax.bar_label(ax.containers[1], fontsize=8)
        sns.set(rc={'figure.figsize':(9,6)})
        sns.set_theme(style='white')
        plt.xticks(rotation=0)
        ax.set_xticklabels(xaxis)
        plt.xlabel('Hour of the day (24h)', fontsize=16)
        plt.ylabel('Total words uttered', fontsize=16)
        plt.title('Total words uttered by male & female caregivers around child', fontsize=20)

        newfolder = os.path.join(main_output_folder, self.id+"_plots")
        os.makedirs(newfolder, exist_ok=True)
        newpath = os.path.join(newfolder, self.id+"_combineddailywords.png")
        plt.savefig(newpath, bbox_inches = 'tight',dpi=140)
        plt.close()
        

# -----------------------------------------------------------
# Parsing command line arguments  
# -----------------------------------------------------------
parser = agp.ArgumentParser(formatter_class = agp.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--childid", type=str, help="Child ID associated with recording")
parser.add_argument("-t", "--task", type=str, help="Which extraction task do you want to perform?", default="all")
args = vars(parser.parse_args())

if (args['childid']==""):
    print('ChildID not supplied.')

if (args['task']=="all"):
    child1 = Child(args['childid'])
    child1.do_extraction()
    child1.extract_clips_longCTC()
    child1.extract_clips_longVoc()
    child1.create_dayspeed_graphs('MAN')
    child1.create_dayspeed_graphs('FAN')

elif(args['task']=="ctc"):
    child1 = Child(args['childid'])
    child1.do_extraction()
    child1.extract_clips_longCTC()

elif(args['task']=="chn"):
    child1 = Child(args['childid'])
    child1.do_extraction()
    child1.extract_clips_longVoc()

elif(args['task']=="plots"):
    child1 = Child(args['childid'])
    child1.create_dayspeed_graphs('MAN')
    child1.create_dayspeed_graphs('FAN')
    child1.create_day_words_graph('MAN')
    child1.create_day_words_graph('FAN')
    child1.create_combined_words_graph()

else:
    child1 = Child(args['childid'])
    child1.do_extraction()
    child1.extract_clips_longVoc()