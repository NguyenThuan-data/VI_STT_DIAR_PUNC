/**
 * Audio Player Module using WaveSurfer.js
 * Handles audio waveform visualization and playback controls
 * Key Features:
 * - No scrollbar (compressed waveform to fit container)
 * - Click-to-seek with automatic pause
 */

class AudioPlayer {
    constructor() {
        this.wavesurfer = null;
        this.isPlaying = false;
        this.audioFile = null;
    }

    /**
     * Initialize WaveSurfer with custom configuration
     */
    init() {
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
        }

        this.wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: '#cccccc',     // Grey when not playing
            progressColor: '#ffa500',  // Orange when playing
            cursorColor: '#cc8400',
            barWidth: 2,
            barRadius: 3,
            responsive: true,
            height: 128,
            normalize: true,
            // Critical settings for no-scrollbar requirement
            scrollParent: false,      // Remove scrollbar
            // minPxPerSec will be set dynamically after load to fit entire audio
            fillParent: true,         // Use full container width
            autoCenter: false,        // No auto-scrolling
            interact: true,           // Enable click interactions
            hideScrollbar: true       // Ensure scrollbar is hidden
        });

        this.setupEventListeners();
    }

    /**
     * Setup event listeners for WaveSurfer and player controls
     */
    setupEventListeners() {
        // Click-to-seek and pause feature
        this.wavesurfer.on('click', () => {
            // After seeking, pause the playback
            this.wavesurfer.pause();
            this.updatePlayPauseButton(false);
        });

        // Update time display during playback
        this.wavesurfer.on('audioprocess', () => {
            this.updateTimeDisplay();
        });

        // When playback finishes
        this.wavesurfer.on('finish', () => {
            this.isPlaying = false;
            this.updatePlayPauseButton(false);
        });

        // When audio is ready
        this.wavesurfer.on('ready', () => {
            // Calculate minPxPerSec to fit entire waveform in container
            const duration = this.wavesurfer.getDuration();
            const containerWidth = document.getElementById('waveform').clientWidth;
            
            // Calculate pixels per second needed to fit the entire audio
            // Subtract 20px for padding
            const minPxPerSec = Math.max(0.1, (containerWidth - 20) / duration);
            
            // Zoom to fit entire waveform without scrolling
            this.wavesurfer.zoom(minPxPerSec);
            
            this.updateTimeDisplay();
            const durationEl = document.getElementById('duration');
            if (durationEl) {
                durationEl.textContent = this.formatTime(this.wavesurfer.getDuration());
            }
        });

        // Play/Pause button
        const playPauseBtn = document.getElementById('playPauseBtn');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                this.togglePlayPause();
            });
        }
    }

    /**
     * Load audio file into WaveSurfer
     * @param {File|Blob} file - Audio file to load
     */
    async loadAudio(file) {
        this.audioFile = file;
        
        if (!this.wavesurfer) {
            this.init();
        }

        try {
            // Create object URL for the file
            const url = URL.createObjectURL(file);
            
            // Load audio into WaveSurfer
            await this.wavesurfer.load(url);
            
            // Hide upload section, show player container
            const uploadSection = document.getElementById('uploadSection');
            const container = document.getElementById('audioPlayerContainer');
            
            if (uploadSection) {
                uploadSection.style.display = 'none';
            }
            if (container) {
                container.style.display = 'block';
            }

            // Enable process button
            const processBtn = document.getElementById('processBtn');
            if (processBtn) {
                processBtn.disabled = false;
            }

            return true;
        } catch (error) {
            console.error('Error loading audio:', error);
            return false;
        }
    }

    /**
     * Toggle play/pause state
     */
    togglePlayPause() {
        if (!this.wavesurfer) return;

        if (this.wavesurfer.isPlaying()) {
            this.wavesurfer.pause();
            this.updatePlayPauseButton(false);
        } else {
            this.wavesurfer.play();
            this.updatePlayPauseButton(true);
        }
    }

    /**
     * Update play/pause button UI
     * @param {boolean} isPlaying - Current playback state
     */
    updatePlayPauseButton(isPlaying) {
        this.isPlaying = isPlaying;
        const playIcon = document.getElementById('playIcon');
        const pauseIcon = document.getElementById('pauseIcon');

        if (playIcon && pauseIcon) {
            if (isPlaying) {
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
            } else {
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
            }
        }
    }

    /**
     * Update current time display
     */
    updateTimeDisplay() {
        if (!this.wavesurfer) return;

        const currentTimeEl = document.getElementById('currentTime');
        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatTime(this.wavesurfer.getCurrentTime());
        }
    }

    /**
     * Format time in MM:SS format
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time string
     */
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Get the current audio file
     * @returns {File|Blob|null}
     */
    getAudioFile() {
        return this.audioFile;
    }

    /**
     * Reset player state
     */
    reset() {
        if (this.wavesurfer) {
            this.wavesurfer.stop();
            this.wavesurfer.empty();
        }
        
        this.isPlaying = false;
        this.audioFile = null;
        this.updatePlayPauseButton(false);

        // Show upload section, hide player
        const uploadSection = document.getElementById('uploadSection');
        const container = document.getElementById('audioPlayerContainer');
        
        if (uploadSection) {
            uploadSection.style.display = 'block';
        }
        if (container) {
            container.style.display = 'none';
        }

        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = true;
        }
        
        // Hide time jump and search sections
        const timeJumpSection = document.getElementById('timeJumpSection');
        const searchSection = document.getElementById('searchSection');
        if (timeJumpSection) timeJumpSection.style.display = 'none';
        if (searchSection) searchSection.style.display = 'none';
    }

    /**
     * Jump to specific time in seconds
     * @param {number} seconds - Time in seconds to jump to
     */
    seekTo(seconds) {
        if (!this.wavesurfer) return false;
        
        const duration = this.wavesurfer.getDuration();
        if (seconds < 0 || seconds > duration) {
            return false;
        }
        
        // Calculate position as percentage
        const position = seconds / duration;
        this.wavesurfer.seekTo(position);
        
        // Pause after seeking
        this.wavesurfer.pause();
        this.updatePlayPauseButton(false);
        
        return true;
    }

    /**
     * Get current playback position in seconds
     * @returns {number}
     */
    getCurrentTime() {
        if (!this.wavesurfer) return 0;
        return this.wavesurfer.getCurrentTime();
    }

    /**
     * Get total duration in seconds
     * @returns {number}
     */
    getDuration() {
        if (!this.wavesurfer) return 0;
        return this.wavesurfer.getDuration();
    }

    /**
     * Destroy WaveSurfer instance
     */
    destroy() {
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
            this.wavesurfer = null;
        }
    }
}

// Export as global for use in app.js
window.AudioPlayer = AudioPlayer;

