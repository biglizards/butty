import threading
import time
import urllib
from collections import deque

import discord

import cogs.voice_lib.mkvparse as mkvparse

import logging

# dumb buffer stuff
import io, queue, subprocess


class Handler(mkvparse.MatroskaHandler):
    def __init__(self, packet_buffer):
        self.packet_buffer = packet_buffer

    # dispatched for each frame by mkvparse
    def frame(self, track_id, timestamp, data, more_laced_frames, duration, keyframe, invisible, discardable):
        while len(self.packet_buffer) > 10000:
            time.sleep(1)  # block until packet buffer size is reduced
        self.packet_buffer.append(data)


class Buffer:
    def __init__(self, raw_packets):
        self.raw_packets = raw_packets
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
        try:
            return self.raw_packets.read(n)
        except ConnectionError as e:
            raise e


# this is a little over-engineered -- we only call self.read() with a fixed value
# so a lot about this could be simplified if it turns out to be a performance problem
class StreamBuffer(io.BufferedIOBase):
    def __init__(self, file, *args, **kwargs):
        super(StreamBuffer, self).__init__(*args, **kwargs)

        self.CHUNK_SIZE = 1024 * 16
        self.MAX_QUEUE_SIZE = 160 * 4  # 10 MiB max per buffer

        self.file = file
        self.finished_downloading = False
        self.current_buffer = io.BytesIO()
        self.buffers = queue.Queue(self.MAX_QUEUE_SIZE)

        self.downloader = threading.Thread(target=self.top_up_buffers, args=())
        self.downloader.daemon = True
        self.downloader.start()

    def read(self, size=-1):
        if size is None or size < 0:
            size = float('inf')
        total = 0
        data = []
        size_remaining = size if isinstance(size, int) else -1
        while total < size:
            x = self.current_buffer.read(size_remaining)
            total += len(x)
            size_remaining -= len(x)
            data.append(x)
            if len(x) == 0:
                while True:
                    try:
                        self.current_buffer = self.buffers.get(timeout=0.2)
                        break
                    except queue.Empty:
                        if self.finished_downloading:
                            return b''.join(data)
        return b''.join(data)

    def top_up_buffers(self):
        while not self.finished_downloading:
            data = self.file.read(self.CHUNK_SIZE)
            if data == b'':
                self.finished_downloading = True
                break
            self.buffers.put(io.BytesIO(data))
        logging.info("finished downloading")

    def fileno(self) -> int:
        raise OSError()

    def register_sink(self, stdin):
        self.sink = threading.Thread(target=self._register_sink, args=(stdin,))
        self.sink.daemon = True
        self.sink.start()

    def _register_sink(self, stdin):
        while True:
            data = self.read(self.CHUNK_SIZE)
            if data == b'':
                logging.info("Finished playing song")
                stdin.close()
                break
            stdin.write(data)


class Source(discord.AudioSource):
    def __init__(self, file, song=None, buffer=Buffer):
        self.buffer = buffer(file)
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


def get_source(song, use_opus=True):
    song.refresh_info()

    if song.codec != 'opus' or not use_opus:
        buf = StreamBuffer(urllib.request.urlopen(song.media_url))

        # wait until buffer is non-empty (takes about a second)
        # if we don't do this, discord glitches and the first few seconds are sped up
        while buf.buffers.empty() and not buf.finished_downloading:
            time.sleep(0.1)

        source = discord.FFmpegPCMAudio(subprocess.PIPE, pipe=True)
        buf.register_sink(source._process.stdin)
    else:
        file = urllib.request.urlopen(song.media_url)
        source = Source(file, song)
    return source
