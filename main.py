"""
Main Entry Point
Integrates audio processing, decision logic, and web interface
"""
import threading
import time
import argparse
from audio_processor import AudioProcessor
from decision_logic import DecisionLogic
from app import app, update_audio_state, update_decision_state


class BroadcastAudioSystem:
    """Main system coordinator"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the broadcast audio system"""
        self.config_path = config_path
        self.audio_processor = None
        self.decision_logic = None
        self.running = False
        self.processing_thread = None
    
    def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            # Initialize audio processor
            self.audio_processor = AudioProcessor(self.config_path)
            audio_initialized = self.audio_processor.initialize_audio()
            
            if not audio_initialized:
                print("Warning: Audio initialization failed. Running in simulation mode.")
                update_audio_state({
                    'initialized': False,
                    'error': 'Audio device not available - running in simulation mode'
                })
            else:
                device_info = self.audio_processor.get_device_info()
                update_audio_state({
                    'initialized': True,
                    'device_info': device_info,
                    'error': None
                })
                print(f"Audio initialized: {device_info.get('name', 'Unknown device')}")
            
            # Initialize decision logic
            self.decision_logic = DecisionLogic(self.config_path)
            camera_status = self.decision_logic.get_camera_status()
            update_decision_state({
                'current_camera': camera_status['current_camera']
            })
            print(f"Decision logic initialized. Default camera: {camera_status['current_camera']}")
            
            return True
        
        except Exception as e:
            print(f"Initialization error: {e}")
            update_audio_state({
                'initialized': False,
                'error': str(e)
            })
            return False
    
    def process_audio_loop(self):
        """Main audio processing loop"""
        print("Starting audio processing loop...")
        
        while self.running:
            try:
                # Analyze audio
                if self.audio_processor and self.audio_processor.stream:
                    analysis = self.audio_processor.analyze_audio()
                else:
                    # Simulation mode - no real audio
                    # Use configured number of channels
                    num_channels = self.audio_processor.channels if self.audio_processor else 4
                    analysis = {
                        'timestamp': time.time(),
                        'channel_volumes': {i: 0 for i in range(num_channels)},
                        'active_microphones': []
                    }
                
                # Update audio state
                update_audio_state({
                    'last_analysis': analysis
                })
                
                # Make camera decision
                if self.decision_logic:
                    active_mics = analysis.get('active_microphones', [])
                    decision = self.decision_logic.decide_camera(active_mics)
                    
                    # Update decision state
                    update_decision_state({
                        'current_camera': decision['camera'],
                        'last_decision': decision
                    })
                    
                    # Log camera switches
                    if decision['switched']:
                        print(f"[{time.strftime('%H:%M:%S')}] Camera switched to: {decision['camera']}")
                        print(f"  Reason: {decision['reason']}")
                
                # Small delay to avoid excessive CPU usage
                time.sleep(0.05)  # 20 FPS processing rate
            
            except Exception as e:
                print(f"Error in processing loop: {e}")
                update_audio_state({
                    'error': str(e)
                })
                time.sleep(1)
    
    def start(self):
        """Start the audio processing in background thread"""
        if self.running:
            print("System already running")
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_audio_loop, daemon=True)
        self.processing_thread.start()
        print("Audio processing started")
    
    def stop(self):
        """Stop the audio processing"""
        if not self.running:
            return
        
        print("Stopping audio processing...")
        self.running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        
        if self.audio_processor:
            self.audio_processor.close()
        
        print("Audio processing stopped")
    
    def run_web_interface(self, host: str = '0.0.0.0', port: int = 5000):
        """Run the Flask web interface"""
        print(f"Starting web interface on http://{host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Broadcast Audio System')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--host', default='0.0.0.0', help='Web interface host')
    parser.add_argument('--port', type=int, default=5000, help='Web interface port')
    parser.add_argument('--no-audio', action='store_true', help='Run without audio (simulation mode)')
    
    args = parser.parse_args()
    
    # Create system
    system = BroadcastAudioSystem(args.config)
    
    # Initialize
    if not system.initialize():
        if not args.no_audio:
            print("Failed to initialize system. Use --no-audio for simulation mode.")
            return
    
    # Start audio processing
    system.start()
    
    try:
        # Run web interface (blocking)
        system.run_web_interface(args.host, args.port)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        system.stop()


if __name__ == '__main__':
    main()
