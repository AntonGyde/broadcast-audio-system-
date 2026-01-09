"""
Audio Processor Module
Handles USB audio device capture and real-time audio analysis
"""
import pyaudio
import numpy as np
import json
import time
from typing import List, Dict, Optional


class AudioProcessor:
    """Processes audio from USB multitrack device and detects active microphones"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize audio processor with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.sample_rate = self.config['audio']['sample_rate']
        self.chunk_size = self.config['audio']['chunk_size']
        self.channels = self.config['audio']['channels']
        self.device_index = self.config['audio'].get('device_index')
        
        self.volume_threshold = self.config['thresholds']['volume_threshold']
        self.min_active_frames = self.config['thresholds']['min_active_frames']
        
        self.pyaudio_instance = None
        self.stream = None
        
        # Track active frames per channel
        self.active_frame_counts = [0] * self.channels
        
    def initialize_audio(self) -> bool:
        """Initialize PyAudio and open audio stream"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # If device_index is not specified, use default input device
            if self.device_index is None:
                self.device_index = self.pyaudio_instance.get_default_input_device_info()['index']
            
            # Open audio stream
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            return True
        except Exception as e:
            print(f"Error initializing audio: {e}")
            return False
    
    def process_frame(self, audio_data: bytes) -> Dict[int, float]:
        """
        Process a single audio frame and calculate volume levels per channel
        
        Args:
            audio_data: Raw audio bytes from stream
            
        Returns:
            Dictionary mapping channel index to volume level
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Reshape to separate channels
        audio_array = audio_array.reshape(-1, self.channels)
        
        # Calculate RMS (Root Mean Square) volume for each channel
        channel_volumes = {}
        for ch in range(self.channels):
            channel_data = audio_array[:, ch]
            rms = np.sqrt(np.mean(channel_data**2))
            channel_volumes[ch] = float(rms)
        
        return channel_volumes
    
    def detect_active_microphones(self, channel_volumes: Dict[int, float]) -> List[int]:
        """
        Detect which microphones are currently active based on volume threshold
        
        Args:
            channel_volumes: Dictionary mapping channel index to volume level
            
        Returns:
            List of active channel indices
        """
        active_channels = []
        
        for ch, volume in channel_volumes.items():
            # Check if volume exceeds threshold
            if volume > self.volume_threshold:
                self.active_frame_counts[ch] += 1
            else:
                self.active_frame_counts[ch] = 0
            
            # Only consider active if threshold exceeded for minimum frames
            if self.active_frame_counts[ch] >= self.min_active_frames:
                active_channels.append(ch)
        
        return active_channels
    
    def read_audio_frame(self) -> Optional[bytes]:
        """Read a single frame from the audio stream"""
        if self.stream is None or not self.stream.is_active():
            return None
        
        try:
            audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            return audio_data
        except Exception as e:
            print(f"Error reading audio frame: {e}")
            return None
    
    def analyze_audio(self) -> Dict[str, any]:
        """
        Perform complete audio analysis for current frame
        
        Returns:
            Dictionary containing volume levels and active microphones
        """
        audio_data = self.read_audio_frame()
        
        if audio_data is None:
            return {
                'timestamp': time.time(),
                'channel_volumes': {},
                'active_microphones': [],
                'error': 'No audio data available'
            }
        
        channel_volumes = self.process_frame(audio_data)
        active_microphones = self.detect_active_microphones(channel_volumes)
        
        return {
            'timestamp': time.time(),
            'channel_volumes': channel_volumes,
            'active_microphones': active_microphones
        }
    
    def update_threshold(self, new_threshold: float):
        """Update the volume threshold for detection"""
        self.volume_threshold = new_threshold
        self.config['thresholds']['volume_threshold'] = new_threshold
    
    def get_device_info(self) -> Dict:
        """Get information about the current audio device"""
        if self.pyaudio_instance is None:
            return {}
        
        try:
            device_info = self.pyaudio_instance.get_device_info_by_index(self.device_index)
            return {
                'name': device_info.get('name', 'Unknown'),
                'channels': device_info.get('maxInputChannels', 0),
                'sample_rate': device_info.get('defaultSampleRate', 0)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        """Clean up audio resources"""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.pyaudio_instance is not None:
            self.pyaudio_instance.terminate()
