import threading
import time
import urllib
from collections import deque

import discord

import cogs.voice_lib.mkvparse as mkvparse


class Handler(mkvparse.MatroskaHandler):
    def __init__(self, packet_buffer):
        self.packet_buffer = packet_buffer

    # dispatched for each frame by mkvparse
    def frame(self, track_id, timestamp, data, more_laced_frames, duration, keyframe, invisible, discardable):
        while len(self.packet_buffer) > 5000:
            time.sleep(1)  # block until packet buffer size is reduced
        self.packet_buffer.append(data)


class Buffer:
    def __init__(self, raw_packet_stream):
        self.raw_packets = raw_packet_stream
        self.packets = deque()

        self.handler = Handler(self.packets)
        self.parser = None

    def parse_opus(self):
        self.parser = threading.Thread(target=mkvparse.mkvparse, args=(self, self.handler))
        self.parser.daemon = True
        self.parser.start()

    def wait_until_ready(self):
        while len(self.packets) < 25 and self.parser.is_alive():
            time.sleep(0.1)

    def read(self, n):
        # Called by mkvparse
        return self.raw_packets.read(n)


class Source(discord.AudioSource):
    def __init__(self, file, song=None):
        self.buffer = Buffer(file)
        self.buffer.parse_opus()
        self.song = song

    def read(self):
        self.buffer.wait_until_ready()
        try:
            frame = self.buffer.packets.popleft()
        except IndexError:
            frame = b''
        return frame

    def is_opus(self):
        return True


class EmptySource(discord.AudioSource):
    def read(self):
        return b''


def get_source(song):
    song.refresh_info()

    if song.codec != 'opus':
        source = discord.FFmpegPCMAudio(song.media_url)
    else:
        file = urllib.request.urlopen(song.media_url)
        source = Source(file, song)
    return source
