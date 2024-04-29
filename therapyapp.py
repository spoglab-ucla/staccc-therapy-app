''' 
    ==========================================
    SPOG Lab, UCLA 
    
    Authors: Arjun Pawar and Dr. Meg Cychosz
    ==========================================
'''

import pandas as pd
import numpy as np
import scipy.io as sc
from scipy.io import wavfile
import tkinter as tk
from tkinter import *
from tkinter import ttk as ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import os as os
from pydub import AudioSegment
from pydub.playback import play
import subprocess
import math
import random
import datetime
#from datetime import datetime
from datetime import timedelta
from pytz import timezone
from PIL import ImageTk , Image

# Global variables

list_of_randoms = []
list_of_randoms_2 = []
checkbutton_value  = None
all_avail_IDs = []


main_input_folder = "/Users/arjun/Box/box-group-lena-studies/Soundscape/wavFiles"
main_output_folder = "/Users/arjun/Box/box-group-lena-studies/Soundscape/ucsf_app_stuff"
ucsf_logo_path = '/Users/arjun/Documents/College/spoglabapp/ucsf_logo.jpeg'
spog_logo_path = '/Users/arjun/Documents/College/spoglabapp/spoglab_logo.png'

# -----------------------------------------------------------
# Creating a record of all child IDs which are available
# -----------------------------------------------------------

path_of_childids = os.path.join(main_output_folder, 'avail_child_ID.txt')
with open(path_of_childids) as file:
  for item in file:
    all_avail_IDs.append(item.strip())

class Child():

    def __init__(self):
        
        self.sorted_ctccount = None
        self.long_CTCs_offsets =  []
        self.long_CHN_offsets =  []
        self.LENA_start_time = None

    def set_ID(self,id:str):
        self.childid = id
    
    def load_my_offsets(self):
        '''
        This function loads all the starting and ending times for each of the top 15 CTC and top 15 CHN clips, relative to start of the LENA recording
        '''

        path_of_offsets = os.path.join(main_output_folder,self.childid+"_CTCclips", self.childid+ "_longCTCoffsets.txt")

        with open(path_of_offsets) as file:
            for item in file:
                entry = item.strip()
                spaceindex = entry.find(" ")
                mytuple = (entry[0:spaceindex], entry[spaceindex+1:])
                self.long_CTCs_offsets.append(mytuple)

        path_of_CHN_offsets = os.path.join(main_output_folder,self.childid+"_CHNclips", self.childid+ "_longCHNoffsets.txt")

        with open(path_of_CHN_offsets) as file:
            for item in file:
                entry = item.strip()
                spaceindex = entry.find(" ")
                mytuple = (entry[0:spaceindex], entry[spaceindex+1:])
                self.long_CHN_offsets.append(mytuple)

    def getrealtime(self, i, whichtype:str):
        '''
        whichtype can take either "chn" or "ctc"
        '''

        infocsvpath = os.path.join(main_input_folder , self.childid + "_speech_output",  self.childid+"_its_info.csv")
        
        itsinfocsv = pd.read_csv(infocsvpath)
        datetime_str = str(itsinfocsv['startClockTime'][0])
        datetime_object = datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        datetime_object = datetime_object.replace(tzinfo=datetime.timezone.utc)

        self.LENA_start_time = datetime_object
        
        if (whichtype=='ctc'):
            offset_amount = int(float(self.long_CTCs_offsets[i][0]))
        else:
            offset_amount = int(float(self.long_CHN_offsets[i][0]))
        
        actual_time_of_clip_UTC = self.LENA_start_time + timedelta(seconds = offset_amount)
        
        if (self.childid.find('L')>=0 or self.childid.find('M')>=0  or self.childid.find('D')>=0  or self.childid.find('E')>=0):
            actual_time_of_clip = actual_time_of_clip_UTC.astimezone(timezone('America/Chicago'))

        if (self.childid.find('R')>=0 or self.childid.find('J')>=0):
            actual_time_of_clip = actual_time_of_clip_UTC.astimezone(timezone('America/New_York'))
        
        return actual_time_of_clip

# ------------------------------
#  END OF CLASS DECLARATION
# ------------------------------

def get_input():
    value = my_text_box.get("1.0","end-1c")
    my_text_box.delete("1.0","end")
    if value in all_avail_IDs:
        current_child.set_ID (value)
        current_child.load_my_offsets()
        showinfo(title='Selection', message = "You are now viewing child ID: " + current_child.childid + "!")
        showinfo(title='Status Update', message = "You can now use the interface.")
        which_child = Label(master, text="📍Current child: "+current_child.childid, font=('Aerial 14'), bg='green', fg = 'white')
        which_child.grid(row=1,column=2,sticky=W)
    else:
       showinfo(title='Error', message = 'This child ID was not found in our database.')

def play_longest_CTC():
    '''
    This function plays the clip with the longest CT measured by convo count which has been extracted
    '''    
    filetoplay = os.path.join(main_output_folder ,  current_child.childid+ "_CTCclips",current_child.childid+ "_longCTC0.wav")
    

    if(checkbutton_value.get()):
        actual_time_of_clip = current_child.getrealtime(0,'ctc')
        time_message = str(actual_time_of_clip.strftime('This clip is from time %H:%M on date %d-%m-%Y.'))
        showinfo(title="Time information!", message=time_message)

    subprocess.check_call(['open', '-a', 'Quicktime Player', filetoplay])


def play_other_long_CTC():
    '''
    This function plays another clip with a long CT measured by convo count which has been extracted
    '''
    random_index = random.randint(1,14)
    go_on = True
    global list_of_randoms

    if len(list_of_randoms)>=14:
        showinfo(title='Status Update', message = "All the extracted clips have been played. Resetting back to original state!")
        list_of_randoms = []

    while (go_on):
        if random_index not in list_of_randoms:
            list_of_randoms.append(random_index)
            go_on = False
            filetoplay = os.path.join(main_output_folder ,current_child.childid+ "_CTCclips", current_child.childid+ "_longCTC"+str(random_index)+".wav")
        else:
            random_index = random.randint(1,14)
    
    if(checkbutton_value.get()):
        actual_time_of_clip = current_child.getrealtime(random_index,'ctc')
        time_message = str(actual_time_of_clip.strftime('This clip is from time %H:%M on date %d-%m-%Y.'))
        showinfo(title="Time information!", message=time_message)
    subprocess.check_call(['open', '-a', 'Quicktime Player', filetoplay])


def play_longest_CHN():
    '''
    This function plays the clip with the longest CHN vocalization measured by duration which has been extracted
    '''    
    filetoplay = os.path.join(main_output_folder ,current_child.childid+"_CHNclips",current_child.childid+ "_longVoc0.wav") 

    if(checkbutton_value.get()):
        actual_time_of_clip = current_child.getrealtime(0,'chn')
        time_message = str(actual_time_of_clip.strftime('This clip is from time %H:%M on date %d-%m-%Y.'))
        showinfo(title="Time information!", message=time_message)

    subprocess.check_call(['open', '-a', 'Quicktime Player', filetoplay])

def play_other_long_CHN():
    '''
    This function plays another clip with a long vocalization measured by duration
    '''
    random_index = random.randint(1,14)
    go_on = True
    global list_of_randoms_2

    if len(list_of_randoms_2)>=14:
        showinfo(title='Status Update', message = "All the extracted clips have been played. Resetting back to original state!")
        list_of_randoms_2 = []

    while (go_on):
        if random_index not in list_of_randoms_2:
            list_of_randoms_2.append(random_index)
            go_on = False
            filetoplay = os.path.join(main_output_folder, current_child.childid+"_CHNclips", current_child.childid+ "_longVoc"+str(random_index)+".wav")
        else:
            random_index = random.randint(1,14)
    
    if(checkbutton_value.get()):
        actual_time_of_clip = current_child.getrealtime(random_index,'chn')
        time_message = str(actual_time_of_clip.strftime('This clip is from time %H:%M on date %d-%m-%Y.'))
        showinfo(title="Time information!", message=time_message)
    subprocess.check_call(['open', '-a', 'Quicktime Player', filetoplay])

def show_image(which_graph):
    imagefile = ""

    if (which_graph == 'MAN_speed'):
        imagefile = os.path.join(main_output_folder , current_child.childid+ "_plots",current_child.childid+ "_MANdayspeeds.png")
    
    elif (which_graph == 'FAN_speed'):
        imagefile = os.path.join(main_output_folder , current_child.childid+ "_plots",current_child.childid+ "_FANdayspeeds.png")

    elif (which_graph == 'MAN_words'):
        imagefile = os.path.join(main_output_folder , current_child.childid+ "_plots",current_child.childid+ "_MANdailywords.png")

    elif (which_graph == 'FAN_words'):
        imagefile = os.path.join(main_output_folder , current_child.childid+ "_plots",current_child.childid+ "_FANdailywords.png")
    
    elif  (which_graph == 'comb_words'):
        imagefile = os.path.join(main_output_folder , current_child.childid+ "_plots",current_child.childid+ "_combineddailywords.png")
 
    '''image = ImageTk.PhotoImage(file=imagefile)
    imagebox.config(image=image)
    imagebox.image = image
    imagebox.grid(row=10, column=2)'''

    top = Toplevel()
    top.title("Plot pop-up")
    image3 = tk.PhotoImage(file=imagefile)
     
    img_label = Label(top, image = image3)
    img_label.grid(row=0, column=0, columnspan=2)
    
    img_label.image = image3
 

master = tk.Tk()
master.title('SPOG x UCSF Interface')
 

current_child = Child()

#l2 = tk.Label(master,font=("Times New Roman", 16), text= "Start here: ")
#l2.grid(row=3,column=0,sticky=E)

l3 = tk.Label(master,font=("Times New Roman", 16), text= "All about conversational turns (CTC): ")
l3.grid(row=5,column=0,sticky=E)

play_longest_CTC_button = ttk.Button(master, text='Play the longest CTC', command=play_longest_CTC)
play_longest_CTC_button.grid(row=6,column=1, sticky=W)

play_long_CTC_button = ttk.Button(master, text='Play another long CTC for us', command=play_other_long_CTC)
play_long_CTC_button.grid(row=7,column=1, sticky=W)

empty1 = tk.Label(master)
empty1.grid(row=8)

l4 = tk.Label(master,font=("Times New Roman", 16), text= "All about child vocalizations (CHN): ")
l4.grid(row=10,column=0,sticky=E)

play_longest_CHN_button = ttk.Button(master, text='Play the longest CHN voc', command=play_longest_CHN)
play_longest_CHN_button.grid(row=11,column=1, sticky=W)

play_long_CHN_button = ttk.Button(master, text='Play another long CHN for us', command=play_other_long_CHN)
play_long_CHN_button.grid(row=12,column=1, sticky=W)


inputdirections = tk.Label(master,font=("Times New Roman", 16), text= "Enter child ID for this session (case-sensitive, with no spaces) : ")
inputdirections.grid(row=13, column=0)

my_text_box=Text(master, height=3, width=20)
my_text_box.grid(row=13,column=1, sticky=W ,columnspan=2)

comment = tk.Button(master, height=2 , width=10, text="Done", command=lambda: get_input(),bg='yellow', fg='blue')
comment.grid(row=14,column=1, sticky=W)

checkbutton_value = tk.BooleanVar()
checkbutton = ttk.Checkbutton(text="Check this box before playing any audio to display real time of clip", variable=checkbutton_value)
checkbutton.grid(row=4, column=0, pady=5)

l1 = tk.Label(master, background= 'light blue',font=("SF Pro", 26), text= "Welcome to the interface!")
l1.grid(row=0,column=0, padx=10, pady=10,sticky=E)

graph = tk.Button(master, text="Show graph of male speech rates", command=lambda: show_image("MAN_speed"))
graph.grid(row=9,column=2)

graph2 = tk.Button(master, text="Show graph of female speech rates", command=lambda: show_image("FAN_speed"))
graph2.grid(row=10,column=2)

graph3 = tk.Button(master, text="Show graph of male word counts", command=lambda: show_image("MAN_words"))
graph3.grid(row=11,column=2)

graph4 = tk.Button(master, text="Show graph of female word counts", command=lambda: show_image("FAN_words"))
graph4.grid(row=12,column=2)

graph4 = tk.Button(master, text="Show graph of total word counts", command=lambda: show_image("comb_words"))
graph4.grid(row=13,column=2)

imagebox = tk.Label(master)
imagebox.grid(row=15,column=1)
imagebox.destroy()
 
img = ImageTk.PhotoImage(Image.open(ucsf_logo_path).resize((200,110)))
p1 = tk.Label(master,  image= img)
p1.grid(row=1,column=0, sticky=E)       

img2 = ImageTk.PhotoImage(Image.open(spog_logo_path).resize((290,110)))
p2 = tk.Label(master,  image= img2)
p2.grid(row=1,column=1,sticky=W)

#imagebox = tk.Label(master)
#imagebox.grid(row=10, column=2)
#graphclose = tk.Button(master, text="Close graph", command= imagebox.grid_remove)
#graphclose.grid(row=9,column=3)
 
master.mainloop()