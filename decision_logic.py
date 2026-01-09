"""
Decision Logic Module
Handles camera switching decisions based on active microphones
"""
import json
import time
from typing import List, Optional


class DecisionLogic:
    """Makes camera switching decisions based on audio analysis"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize decision logic with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.default_camera = self.config['cameras']['default_camera']
        self.camera_mappings = self.config['cameras']['camera_mappings']
        self.priority_mode = self.config['decision']['priority_mode']
        self.idle_timeout = self.config['decision']['idle_timeout_seconds']
        
        self.current_camera = self.default_camera
        self.last_activity_time = time.time()
        self.last_active_microphone = None
    
    def decide_camera(self, active_microphones: List[int]) -> Dict[str, any]:
        """
        Decide which camera to switch to based on active microphones
        
        Args:
            active_microphones: List of active microphone/channel indices
            
        Returns:
            Dictionary containing camera decision and reasoning
        """
        current_time = time.time()
        decision = {
            'timestamp': current_time,
            'active_microphones': active_microphones,
            'camera': self.current_camera,
            'reason': '',
            'switched': False
        }
        
        # Case 1: No one speaking
        if len(active_microphones) == 0:
            # Check if idle timeout has elapsed
            if current_time - self.last_activity_time >= self.idle_timeout:
                if self.current_camera != self.default_camera:
                    self.current_camera = self.default_camera
                    decision['camera'] = self.current_camera
                    decision['reason'] = 'No activity detected - switching to default wide shot'
                    decision['switched'] = True
                else:
                    decision['reason'] = 'No activity - maintaining default wide shot'
            else:
                decision['reason'] = f'No activity - waiting for idle timeout ({self.idle_timeout}s)'
        
        # Case 2: One person speaking
        elif len(active_microphones) == 1:
            mic_index = active_microphones[0]
            target_camera = self.camera_mappings.get(str(mic_index), self.default_camera)
            
            if self.current_camera != target_camera:
                self.current_camera = target_camera
                decision['camera'] = self.current_camera
                decision['reason'] = f'Single speaker on microphone {mic_index} - cutting to {target_camera}'
                decision['switched'] = True
            else:
                decision['reason'] = f'Maintaining camera on single speaker (mic {mic_index})'
            
            self.last_activity_time = current_time
            self.last_active_microphone = mic_index
        
        # Case 3: Multiple people speaking
        else:
            # Prioritize based on mode
            if self.priority_mode == 'first_active':
                # Use the first microphone in the list (lowest index)
                mic_index = min(active_microphones)
            elif self.priority_mode == 'last_active':
                # Use the last active microphone
                if self.last_active_microphone in active_microphones:
                    mic_index = self.last_active_microphone
                else:
                    mic_index = active_microphones[0]
            else:
                # Default to first in list
                mic_index = active_microphones[0]
            
            target_camera = self.camera_mappings.get(str(mic_index), self.default_camera)
            
            if self.current_camera != target_camera:
                self.current_camera = target_camera
                decision['camera'] = self.current_camera
                decision['reason'] = f'Multiple speakers - prioritizing microphone {mic_index} ({self.priority_mode} mode)'
                decision['switched'] = True
            else:
                decision['reason'] = f'Multiple speakers - maintaining camera on microphone {mic_index}'
            
            self.last_activity_time = current_time
            self.last_active_microphone = mic_index
        
        return decision
    
    def get_camera_status(self) -> Dict[str, any]:
        """Get current camera status and configuration"""
        return {
            'current_camera': self.current_camera,
            'default_camera': self.default_camera,
            'priority_mode': self.priority_mode,
            'idle_timeout': self.idle_timeout,
            'last_activity_time': self.last_activity_time,
            'last_active_microphone': self.last_active_microphone,
            'camera_mappings': self.camera_mappings
        }
    
    def update_default_camera(self, camera: str):
        """Update the default camera setting"""
        self.default_camera = camera
        self.config['cameras']['default_camera'] = camera
    
    def update_priority_mode(self, mode: str):
        """Update the priority mode for multiple speakers"""
        if mode in ['first_active', 'last_active']:
            self.priority_mode = mode
            self.config['decision']['priority_mode'] = mode
    
    def update_idle_timeout(self, timeout: float):
        """Update the idle timeout in seconds"""
        self.idle_timeout = timeout
        self.config['decision']['idle_timeout_seconds'] = timeout
    
    def reset(self):
        """Reset to default state"""
        self.current_camera = self.default_camera
        self.last_activity_time = time.time()
        self.last_active_microphone = None
