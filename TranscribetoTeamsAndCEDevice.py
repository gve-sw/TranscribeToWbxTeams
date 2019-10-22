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
from __future__ import division

#https://cloud.google.com/speech-to-text/
#https://pypi.org/project/google-cloud-speech/

#source testgooglespeech/bin/activate
#testgooglespeech/bin/pip install google-cloud-speech

import re
import sys

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
import os
import requests
from config import GOOGLE_APPLICATION_CREDENTIALS, WEBEX_TEAMS_ACCESS_TOKEN

# Audio recording parameters
RATE = 20000
CHUNK = int(RATE / 10)  # 100ms
import threading

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
CEDEVICEADDRESS=""
XAPIUSER=""
XAPIPWD=""
XAPITIMEOUT=5
TEAMSUSER=""

import paramiko

def connectToCEDevice():
    global stdin, stdout, stderr, ssh
    if (CEDEVICEADDRESS!=""):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to CE device....")
        print("Host: ",CEDEVICEADDRESS)
        print("User: ",XAPIUSER)
        print("Pwd: ",XAPIPWD)
        #print("Environment variable is: ",CEDEVICEADDRESS2)
        ssh.connect(CEDEVICEADDRESS, 22, XAPIUSER, XAPIPWD,timeout=XAPITIMEOUT)
        print("Connected!")
        stdin, stdout, stderr = ssh.exec_command("",get_pty=True)
        stdin.write('xCommand UserInterface Message TextLine Display Text: "Getting Started" X:10 Y:10 Duration:10\n')
        print("Sent first CE command!")

def printToCEDevice(strToPrint):
    global stdin, stdout, stderr, ssh
    if (CEDEVICEADDRESS!=""):
        stdin.write('xCommand UserInterface Message TextLine Display Text: "'+strToPrint+'" X:10 Y:10 Duration:10\n')



class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript
        #send_to_teams(transcript)

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))
        

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()
            
            num_chars_printed = len(transcript)
            
        else:
            send_to_teams(transcript)
            printToCEDevice(transcript)

            print(transcript + overwrite_chars)
            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0

def send_to_teams(text):
    from webexteamssdk import WebexTeamsAPI
    api = WebexTeamsAPI(access_token=WEBEX_TEAMS_ACCESS_TOKEN)   
    send_msg = api.messages.create(toPersonEmail=TEAMSUSER, markdown=text)


 
def main(argv):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    #language_code = 'it'  # a BCP-47 language tag
    language_code = 'en-US'  # a BCP-47 language tag
    global TEAMSUSER, CEDEVICEADDRESS, XAPIUSER, XAPIPWD

    if len(argv)==1:
        TEAMSUSER=argv[0]
    elif len(argv)==4:
        TEAMSUSER=argv[0]
        CEDEVICEADDRESS=argv[1]
        XAPIUSER=argv[2]
        XAPIPWD=argv[3]
    else:
        print("invalid number of arguments: TeamsEmailAddress CEDeviceIP CDDeviceUser CDDevicePwd")
        sys.exit(1)

    connectToCEDevice()

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)


if __name__ == '__main__':
    main(sys.argv[1:])