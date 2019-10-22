"""
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
import threading
import subprocess
import os

theprocess=0

def tkThreadingTest():

    from tkinter import Tk, Label, Button, StringVar, Frame, BOTH, Entry, Checkbutton
    from time import sleep



    class UnitTestGUI:

        def __init__( self, master ):
            self.master = master
            self.checkuseCEDeviceVar=StringVar()
            self.checkuseCEDeviceVar.set('0')
            master.title( "Transcription Test" )
            master.geometry("400x250")
            #master.resizable(0, 0)
            theprocess=0

            self.back = Frame(master=master, bg='white')
            self.back.pack_propagate(0)  # Don't allow the widgets inside to determine the frame's width / height
            self.back.pack(fill=BOTH, expand=1)  # Expand the frame to fill the root window

            self.TeamsUser = StringVar()
            self.TeamsUser_entry = Entry(self.back, width=20, textvariable=self.TeamsUser)
            self.TeamsUser_entry.grid(column=2, row=1, sticky=("w", "e"))
            Label(self.back, text="Wbx Teams User: ").grid(column=1, row=1, sticky="w")

            self.threadedButton = Button(
                master=self.back, text="Start transcribing", command=self.onThreadedClicked )
            self.threadedButton.grid(column=1, row=5)
            #self.threadedButton.pack()

            self.statusLabelVar = StringVar()
            self.statusLabel = Label( master=self.back, textvariable=self.statusLabelVar, font=("Helvetica", 12), anchor="w",justify="left" , wraplength=500)
            self.statusLabel.grid(column=1, row=6)
            #self.statusLabel.pack()

            self.cancelButton = Button(
                master=self.back, text="Stop transcribing", command=self.onStopClicked )
            self.cancelButton.grid(column=1, row=7)
            #start with the Stop button disabled
            self.cancelButton.config(state="disabled")


            #self.cleanupButton = Button(
            #    master=self.back, text="Cleanup transcription", command=self.onCleanupClicked )
            #self.cleanupButton.grid(column=1, row=8)

            self.CEDeviceIP = StringVar()
            self.CEDeviceIP.set('X.X.X.X')
            self.CEDeviceIP_entry = Entry(self.back, width=14, textvariable=self.CEDeviceIP)
            self.CEDeviceIP_entry.grid(column=2, row=12, sticky=("w", "e"))
            Label(self.back, text="CE Device IP").grid(column=1, row=12, sticky="w")

            self.CEUser = StringVar()
            self.CEUser_entry = Entry(self.back, width=14, textvariable=self.CEUser)
            self.CEUser_entry.grid(column=2, row=13, sticky=("w", "e"))
            Label(self.back, text="User: ").grid(column=1, row=13, sticky="w")

            self.CEPwd = StringVar()
            self.CEPwd_entry = Entry(self.back, width=14, textvariable=self.CEPwd, show="*")
            self.CEPwd_entry.grid(column=2, row=14, sticky=("w", "e"))
            Label(self.back, text="Password: ").grid(column=1, row=14, sticky="w")


            self.checkuseCEDevice = Checkbutton(master=self.back, text="Use CE Device", variable=self.checkuseCEDeviceVar, command=self.activateCheck).grid(row=9,column=1)  # command is given



            self.CEDeviceIP_entry.config(state="disabled")
            self.CEUser_entry.config(state="disabled")
            self.CEPwd_entry.config(state="disabled")

            self.close = Button(master=self.back, text='Quit', command=master.destroy)
            self.close.grid(column=1, row=17)




        def activateCheck(self):
            print(self.checkuseCEDeviceVar.get())
            if self.checkuseCEDeviceVar.get() == '1':  # whenever checked
                self.CEDeviceIP_entry.config(state="normal")
                self.CEUser_entry.config(state="normal")
                self.CEPwd_entry.config(state="normal")
            elif self.checkuseCEDeviceVar.get() == '0':  # whenever unchecked
                self.CEDeviceIP_entry.config(state="disabled")
                self.CEUser_entry.config(state="disabled")
                self.CEPwd_entry.config(state="disabled")


        def close( self ) :
            print("close")
            try: self.bgTask.stop()
            except: pass
            try: self.timer.stop()
            except: pass
            self.master.quit()

        def onThreadedClicked( self ):
            print("onThreadedClicked")
            #try:self.bgTask.start()
            #except: pass
            try:
                userToSend=self.TeamsUser.get()
                #TODO validate the userToSend to make sure at least it is an email address
                if userToSend!="":
                    if self.checkuseCEDeviceVar.get() == '1':  # whenever checked
                        self.theprocess = subprocess.Popen(["python3", "./TranscribetoTeamsAndCEDevice.py",
                                                            userToSend,
                                                            self.CEDeviceIP_entry.get(),
                                                            self.CEUser_entry.get(),
                                                            self.CEPwd_entry.get()])

                    else:
                        self.theprocess = subprocess.Popen(["python3", "./TranscribetoTeamsAndCEDevice.py", userToSend])

                    self.statusLabelVar.set("Transcription started..." )
                    #enable the stop button
                    self.cancelButton.config(state="normal")
                    #disable the start and cleanup buttons
                    self.threadedButton.config(state="disabled")
                    #self.cleanupButton.config(state="disabled")

                else:
                    self.statusLabelVar.set("NEED TEAMS USER ID" )

            except: pass


        def onStopClicked( self ) :
            print("onStopClicked")
            #try: self.bgTask.stop()
            #except: pass
            try: self.timer.stop()
            except: pass
            try:
                self.theprocess.kill()
                self.statusLabelVar.set("Transcription ended..." )
                userToSend = self.TeamsUser.get()
                if userToSend!="":
                    self.theprocess = subprocess.Popen(["python3", "./TranscribetoTeamsCleanup.py", userToSend])
                    self.statusLabelVar.set("Cleaning up..." )
                else:
                    self.statusLabelVar.set("NEED TEAMS USER ID" )
                # disable the stop button
                self.cancelButton.config(state="disabled")
                # enable the start and cleanup buttons
                self.threadedButton.config(state="normal")
                #self.cleanupButton.config(state="normal")
            except: pass

        def onCleanupClicked( self ) :

            print("onCleanupClicked")
            try:
                userToSend=self.TeamsUser.get()
                #TODO validate the userToSend to make sure at least it is an email address
                if userToSend!="":
                    self.theprocess = subprocess.Popen(["python3", "./TranscribetoTeamsCleanup.py", userToSend])
                    self.statusLabelVar.set("Cleaning up..." )
                else:
                    self.statusLabelVar.set("NEED TEAMS USER ID" )
            except: pass


    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    gui = UnitTestGUI( root )
    root.protocol( "WM_DELETE_WINDOW", gui.close )
    root.mainloop()

if __name__ == "__main__":
    tkThreadingTest()