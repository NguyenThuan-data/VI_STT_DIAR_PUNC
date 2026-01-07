/**
 * Main Application Logic
 * Handles file upload, microphone recording, API calls, and UI interactions
 */

// API Configuration
const API_BASE_URL = window.location.origin + '/api';

// Global state
let audioPlayer = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordingStartTime = null;
let recordingTimer = null;

// Global transcript segments (for search and time jump)
let transcriptSegments = [];

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize audio player
    audioPlayer = new AudioPlayer();
    
    // Setup event listeners
    setupFileUpload();
    setupMicrophoneRecording();
    setupProcessButton();
    setupStatusCheck();
    setupTimeJump();
    setupSearch();
    setupChangeAudioButton();
    
    // Check API status on load
    checkAPIStatus();
});

// ===========================
// File Upload Handlers
// ===========================

function setupFileUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    // Click to upload
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File selection
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
}

function handleFileUpload(file) {
    // Validate file type
    if (!file.type.startsWith('audio/')) {
        showError('Vui lòng tải lên tệp âm thanh (MP3, WAV, M4A, OGG)');
        return;
    }

    // Validate file size (500MB = 524288000 bytes)
    if (file.size > 524288000) {
        showError('Kích thước tệp vượt quá giới hạn 500MB');
        return;
    }

    // Load into audio player
    audioPlayer.loadAudio(file).then(success => {
        if (success) {
            showLog('Đã tải tệp âm thanh thành công: ' + file.name);
            showLog('Kích thước tệp: ' + formatFileSize(file.size));
            
            // Show time jump section after audio loaded
            const timeJumpSection = document.getElementById('timeJumpSection');
            if (timeJumpSection) {
                timeJumpSection.style.display = 'block';
            }
        } else {
            showError('Không thể tải tệp âm thanh');
        }
    });
}

// ===========================
// Microphone Recording
// ===========================

function setupMicrophoneRecording() {
    const micBtn = document.getElementById('micBtn');
    
    micBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            stopRecording();
        } else {
            await startRecording();
        }
    });
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'audio/webm' });
            const file = new File([blob], 'recording.webm', { type: 'audio/webm' });
            handleFileUpload(file);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        recordingStartTime = Date.now();
        
        // Update UI
        const micBtn = document.getElementById('micBtn');
        const micBtnText = document.getElementById('micBtnText');
        const recordingTimer = document.getElementById('recordingTimer');
        
        micBtn.classList.add('recording');
        micBtnText.textContent = 'Dừng Ghi Âm';
        recordingTimer.style.display = 'flex';
        
        // Start timer
        updateRecordingTimer();
        recordingTimer = setInterval(updateRecordingTimer, 1000);
        
        showLog('Đã bắt đầu ghi âm...');
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        showError('Không thể truy cập microphone. Vui lòng cấp quyền.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        
        // Update UI
        const micBtn = document.getElementById('micBtn');
        const micBtnText = document.getElementById('micBtnText');
        const recordingTimerEl = document.getElementById('recordingTimer');
        
        micBtn.classList.remove('recording');
        micBtnText.textContent = 'Ghi Âm Từ Microphone';
        recordingTimerEl.style.display = 'none';
        
        // Clear timer
        if (recordingTimer) {
            clearInterval(recordingTimer);
            recordingTimer = null;
        }
        
        showLog('Đã dừng ghi âm');
    }
}

function updateRecordingTimer() {
    if (!recordingStartTime) return;
    
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    const timerText = document.getElementById('timerText');
    if (timerText) {
        timerText.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// ===========================
// Process Transcription
// ===========================

function setupProcessButton() {
    const processBtn = document.getElementById('processBtn');
    
    processBtn.addEventListener('click', async () => {
        await processTranscription();
    });

    // Copy buttons
    const copyTranscriptBtn = document.getElementById('copyTranscriptBtn');
    const copySummaryBtn = document.getElementById('copySummaryBtn');
    
    if (copyTranscriptBtn) {
        copyTranscriptBtn.addEventListener('click', () => {
            copyToClipboard('transcriptContent', 'Đã sao chép văn bản!');
        });
    }
    
    if (copySummaryBtn) {
        copySummaryBtn.addEventListener('click', () => {
            copyToClipboard('summaryContent', 'Đã sao chép tóm tắt!');
        });
    }
}

async function processTranscription() {
    const audioFile = audioPlayer.getAudioFile();
    if (!audioFile) {
        showError('Vui lòng tải lên hoặc ghi âm trước');
        return;
    }

    const summaryEnabled = document.getElementById('summaryCheckbox').checked;

    // Show loading
    showLoading('Đang xử lý âm thanh... Có thể mất vài phút.');
    clearResults();
    showLog('Bắt đầu quá trình chuyển đổi...');

    try {
        // Step 1: Transcribe with diarization
        showLog('[1/2] Đang gọi API chuyển đổi giọng nói và nhận diện người nói...');
        const transcribeData = await callTranscribeAPI(audioFile);
        
        if (!transcribeData || transcribeData.status === 'error') {
            throw new Error(transcribeData?.message || 'Chuyển đổi thất bại');
        }

        // Display transcript
        displayTranscript(transcribeData.text, transcribeData.segments);
        showLog('✓ Chuyển đổi hoàn tất');

        // Step 2: Generate summary (if enabled)
        if (summaryEnabled) {
            showLog('[2/2] Đang tạo tóm tắt bằng AI...');
            showLoading('Đang tạo tóm tắt AI...');
            
            const summaryData = await callSummarizeAPI(transcribeData.text);
            
            if (summaryData && summaryData.summary) {
                displaySummary(summaryData.summary, summaryData.model_used);
                showLog(`✓ Đã tạo tóm tắt sử dụng ${summaryData.model_used}`);
            } else {
                showLog('⚠ Tạo tóm tắt thất bại hoặc bị bỏ qua');
            }
        } else {
            showLog('[2/2] Bỏ qua tóm tắt (không được bật)');
        }

        showLog('='.repeat(60));
        showLog('XỬ LÝ HOÀN TẤT');
        showLog('='.repeat(60));

    } catch (error) {
        console.error('Processing error:', error);
        showError('Lỗi: ' + error.message);
        showLog('✗ Xử lý thất bại: ' + error.message);
    } finally {
        hideLoading();
    }
}

// ===========================
// API Calls
// ===========================

async function callTranscribeAPI(audioFile) {
    const formData = new FormData();
    formData.append('file', audioFile);

    const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

async function callSummarizeAPI(text) {
    const response = await fetch(`${API_BASE_URL}/summarize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    });

    if (!response.ok) {
        console.warn('Summary API failed:', response.status);
        return null;
    }

    return await response.json();
}

// ===========================
// Status Check
// ===========================

function setupStatusCheck() {
    const checkStatusBtn = document.getElementById('checkStatusBtn');
    
    if (checkStatusBtn) {
        checkStatusBtn.addEventListener('click', async () => {
            await checkAPIStatus();
        });
    }
}

async function checkAPIStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET'
        });

        if (response.ok) {
            const data = await response.json();
            statusDot.className = 'status-dot online';
            statusText.textContent = 'API Trực Tuyến - Sẵn Sàng';
            showLog('✓ API đang hoạt động và sẵn sàng');
        } else {
            throw new Error('API không phản hồi đúng cách');
        }
    } catch (error) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'API Ngoại Tuyến';
        showLog('✗ API ngoại tuyến hoặc không thể truy cập');
    }
}

// ===========================
// UI Display Functions
// ===========================

function displayTranscript(text, segments) {
    const transcriptContent = document.getElementById('transcriptContent');
    const copyBtn = document.getElementById('copyTranscriptBtn');
    
    // Store segments globally for search
    transcriptSegments = segments || [];
    
    // Display transcript
    transcriptContent.textContent = text;
    copyBtn.style.display = 'inline-flex';
    
    // Show time jump and search sections
    const timeJumpSection = document.getElementById('timeJumpSection');
    const searchSection = document.getElementById('searchSection');
    
    if (timeJumpSection) timeJumpSection.style.display = 'block';
    if (searchSection) searchSection.style.display = 'block';
}

function displaySummary(summary, modelUsed) {
    const summaryCard = document.getElementById('summaryCard');
    const summaryContent = document.getElementById('summaryContent');

    summaryCard.style.display = 'block';
    summaryContent.textContent = summary;
}

function clearResults() {
    const transcriptContent = document.getElementById('transcriptContent');
    const summaryContent = document.getElementById('summaryContent');
    const summaryCard = document.getElementById('summaryCard');
    const logsContent = document.getElementById('logsContent');

    transcriptContent.innerHTML = '<p class="placeholder">Đang xử lý...</p>';
    summaryContent.innerHTML = '<p class="placeholder">Đang tạo tóm tắt...</p>';
    summaryCard.style.display = 'none';
    logsContent.textContent = '';
}

function showLog(message) {
    const logsContent = document.getElementById('logsContent');
    const timestamp = new Date().toLocaleTimeString();
    const logLine = `[${timestamp}] ${message}\n`;
    
    if (logsContent.textContent === '' || logsContent.querySelector('.placeholder')) {
        logsContent.textContent = logLine;
    } else {
        logsContent.textContent += logLine;
    }
    
    // Auto-scroll to bottom
    logsContent.scrollTop = logsContent.scrollHeight;
}

function showError(message) {
    alert('Lỗi: ' + message);
    showLog('✗ LỖI: ' + message);
}

function showLoading(message) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    
    loadingOverlay.style.display = 'flex';
    loadingText.textContent = message;
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'none';
}

// ===========================
// Utility Functions
// ===========================

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function copyToClipboard(elementId, successMessage) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        alert(successMessage);
        showLog(successMessage);
    }).catch(err => {
        console.error('Failed to copy:', err);
        showError('Không thể sao chép vào clipboard');
    });
}

// ===========================
// Time Jump Feature
// ===========================

function setupTimeJump() {
    const timeJumpBtn = document.getElementById('timeJumpBtn');
    const timeJumpInput = document.getElementById('timeJumpInput');
    
    if (timeJumpBtn) {
        timeJumpBtn.addEventListener('click', () => {
            jumpToTime();
        });
    }
    
    // Allow Enter key on any time input field
    const timeInputs = ['timeJumpHours', 'timeJumpMinutes', 'timeJumpSeconds'];
    timeInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    jumpToTime();
                }
            });
        }
    });
}

function jumpToTime() {
    const hoursInput = document.getElementById('timeJumpHours');
    const minutesInput = document.getElementById('timeJumpMinutes');
    const secondsInput = document.getElementById('timeJumpSeconds');
    
    const hours = parseInt(hoursInput.value) || 0;
    const minutes = parseInt(minutesInput.value) || 0;
    const seconds = parseInt(secondsInput.value) || 0;
    
    // Validate inputs
    if (hours === 0 && minutes === 0 && seconds === 0) {
        showError('Vui lòng nhập thời gian');
        return;
    }
    
    if (minutes > 59 || seconds > 59) {
        showError('Phút và giây phải nhỏ hơn 60');
        return;
    }
    
    // Calculate total seconds
    const totalSeconds = (hours * 3600) + (minutes * 60) + seconds;
    
    // Jump to time in audio player
    const success = audioPlayer.seekTo(totalSeconds);
    
    if (success) {
        showLog(`Đã nhảy đến ${formatTimeString(totalSeconds)}`);
        // Clear inputs
        hoursInput.value = '';
        minutesInput.value = '';
        secondsInput.value = '';
    } else {
        showError('Không thể nhảy đến thời điểm đó. Kiểm tra độ dài âm thanh.');
    }
}

function formatTimeString(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

// ===========================
// Search in Transcript
// ===========================

function setupSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            performSearch();
        });
    }
    
    if (searchInput) {
        // Allow Enter key to trigger search
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Real-time search as user types
        searchInput.addEventListener('input', () => {
            if (searchInput.value.length >= 2) {
                performSearch();
            }
        });
    }
}

function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const query = searchInput.value.trim().toLowerCase();
    
    if (!query || query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }
    
    if (transcriptSegments.length === 0) {
        searchResults.innerHTML = '<p style="color: #999; padding: 10px;">Chưa có văn bản. Vui lòng xử lý âm thanh trước.</p>';
        return;
    }
    
    // Search through segments
    const results = transcriptSegments.filter(seg => 
        seg.text.toLowerCase().includes(query)
    );
    
    if (results.length === 0) {
        searchResults.innerHTML = '<p style="color: #999; padding: 10px;">Không tìm thấy kết quả</p>';
        return;
    }
    
    // Display results
    let html = '';
    results.forEach(result => {
        const highlightedText = highlightText(result.text, query);
        const timeStr = formatTimeString(result.start);
        
        html += `
            <div class="search-result-item" onclick="jumpToSegment(${result.start})">
                <span class="search-result-time">[${timeStr}]</span>
                <span class="search-result-text">${result.speaker}: ${highlightedText}</span>
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
    showLog(`Tìm thấy ${results.length} kết quả cho "${query}"`);
}

function highlightText(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<span class="search-highlight">$1</span>');
}

function jumpToSegment(startTime) {
    audioPlayer.seekTo(startTime);
    showLog(`Đã nhảy đến ${formatTimeString(startTime)}`);
}

// Make jumpToSegment global for onclick
window.jumpToSegment = jumpToSegment;

// ===========================
// Change Audio Button
// ===========================

function setupChangeAudioButton() {
    const changeBtn = document.getElementById('changeAudioBtn');
    
    if (changeBtn) {
        changeBtn.addEventListener('click', () => {
            // Reset player
            audioPlayer.reset();
            
            // Clear results
            const transcriptContent = document.getElementById('transcriptContent');
            const summaryCard = document.getElementById('summaryCard');
            const logsContent = document.getElementById('logsContent');
            
            if (transcriptContent) {
                transcriptContent.innerHTML = '<p class="placeholder">Văn bản chuyển đổi sẽ hiển thị ở đây sau khi xử lý...</p>';
            }
            if (summaryCard) {
                summaryCard.style.display = 'none';
            }
            if (logsContent) {
                logsContent.textContent = '';
            }
            
            showLog('Đã xóa tệp âm thanh. Vui lòng tải lên tệp mới.');
        });
    }
}

