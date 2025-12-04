/**
 * AI Interviewer - Frontend Application
 * Handles audio recording, API communication, and UI updates
 */

const API_BASE = 'http://localhost:8000';

// State management
const state = {
    sessionId: null,
    profile: 'pleno',
    stack: 'backend',
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    currentTab: 'voice'
};

// DOM Elements
const elements = {
    setupPanel: document.getElementById('setupPanel'),
    interviewPanel: document.getElementById('interviewPanel'),
    profileSelect: document.getElementById('profileSelect'),
    stackInput: document.getElementById('stackInput'),
    startBtn: document.getElementById('startBtn'),
    chatMessages: document.getElementById('chatMessages'),
    recordBtn: document.getElementById('recordBtn'),
    voiceVisualizer: document.getElementById('voiceVisualizer'),
    voiceInput: document.getElementById('voiceInput'),
    codeInput: document.getElementById('codeInput'),
    codeTextarea: document.getElementById('codeTextarea'),
    sendCodeBtn: document.getElementById('sendCodeBtn'),
    evaluateBtn: document.getElementById('evaluateBtn'),
    newInterviewBtn: document.getElementById('newInterviewBtn'),
    evaluationModal: document.getElementById('evaluationModal'),
    evaluationContent: document.getElementById('evaluationContent'),
    closeModal: document.getElementById('closeModal'),
    audioPlayer: document.getElementById('audioPlayer'),
    status: document.getElementById('status')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkMicrophonePermission();
});

// Event Listeners
function setupEventListeners() {
    elements.startBtn.addEventListener('click', startInterview);
    elements.recordBtn.addEventListener('click', toggleRecording);
    elements.sendCodeBtn.addEventListener('click', sendCode);
    elements.evaluateBtn.addEventListener('click', evaluateInterview);
    elements.newInterviewBtn.addEventListener('click', resetInterview);
    elements.closeModal.addEventListener('click', closeEvaluationModal);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Modal overlay click
    elements.evaluationModal.querySelector('.modal-overlay').addEventListener('click', closeEvaluationModal);
}

// Check microphone permission
async function checkMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        console.log('Microphone permission granted');
    } catch (error) {
        console.error('Microphone permission denied:', error);
        showNotification('⚠️ Permissão de microfone necessária', 'error');
    }
}

// Start Interview
async function startInterview() {
    state.profile = elements.profileSelect.value;
    state.stack = elements.stackInput.value.trim() || 'backend';
    
    updateStatus('Iniciando entrevista...', 'processing');
    
    try {
        const response = await fetch(`${API_BASE}/api/interview/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile: state.profile,
                stack: state.stack
            })
        });
        
        if (!response.ok) throw new Error('Failed to start interview');
        
        const data = await response.json();
        state.sessionId = data.session_id;
        
        // Switch to interview panel
        elements.setupPanel.classList.add('hidden');
        elements.interviewPanel.classList.remove('hidden');
        
        // Clear welcome message
        elements.chatMessages.innerHTML = '';
        
        // Add initial message
        addAssistantMessage(data.falar, data.codigo);
        
        // Synthesize and play initial message
        if (data.falar) {
            await synthesizeAndPlay(data.falar);
        }
        
        updateStatus('Entrevista em andamento', 'active');
        
    } catch (error) {
        console.error('Error starting interview:', error);
        showNotification('❌ Erro ao iniciar entrevista', 'error');
        updateStatus('Erro', 'error');
    }
}

// Toggle Recording
async function toggleRecording() {
    if (state.isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

// Start Recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        state.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
            await processAudio(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        
        // Update UI
        elements.recordBtn.classList.add('recording');
        elements.recordBtn.querySelector('.record-text').textContent = 'Gravando... Clique para parar';
        elements.voiceVisualizer.classList.remove('hidden');
        
        updateStatus('Gravando...', 'recording');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('❌ Erro ao acessar microfone', 'error');
    }
}

// Stop Recording
function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        
        // Update UI
        elements.recordBtn.classList.remove('recording');
        elements.recordBtn.querySelector('.record-text').textContent = 'Clique para falar';
        elements.voiceVisualizer.classList.add('hidden');
        
        updateStatus('Processando...', 'processing');
    }
}

// Process Audio
async function processAudio(audioBlob) {
    try {
        // Transcribe audio
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('session_id', state.sessionId);
        
        updateStatus('Transcrevendo...', 'processing');
        
        const transcribeResponse = await fetch(`${API_BASE}/api/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!transcribeResponse.ok) throw new Error('Transcription failed');
        
        const transcribeData = await transcribeResponse.json();
        const transcription = transcribeData.transcription;
        
        if (!transcription || transcription.trim() === '') {
            showNotification('⚠️ Nenhuma fala detectada', 'warning');
            updateStatus('Entrevista em andamento', 'active');
            return;
        }
        
        // Add user message
        addUserMessage(transcription);
        
        // Send to LLM
        await sendMessage(transcription, false);
        
    } catch (error) {
        console.error('Error processing audio:', error);
        showNotification('❌ Erro ao processar áudio', 'error');
        updateStatus('Entrevista em andamento', 'active');
    }
}

// Send Code
async function sendCode() {
    const code = elements.codeTextarea.value.trim();
    
    if (!code) {
        showNotification('⚠️ Digite algum código primeiro', 'warning');
        return;
    }
    
    addUserMessage(code, true);
    elements.codeTextarea.value = '';
    
    await sendMessage(code, true);
}

// Send Message to LLM
async function sendMessage(text, isCode) {
    try {
        updateStatus('Pensando...', 'processing');
        
        const response = await fetch(`${API_BASE}/api/interview/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                text: text,
                is_code: isCode
            })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        const data = await response.json();
        
        // Add assistant message
        addAssistantMessage(data.falar, data.codigo);
        
        // Synthesize and play response
        if (data.falar) {
            await synthesizeAndPlay(data.falar);
        } else {
            updateStatus('Entrevista em andamento', 'active');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('❌ Erro ao enviar mensagem', 'error');
        updateStatus('Entrevista em andamento', 'active');
    }
}

// Synthesize and Play Audio
async function synthesizeAndPlay(text) {
    try {
        updateStatus('Falando...', 'speaking');
        
        const response = await fetch(`${API_BASE}/api/synthesize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                text: text
            })
        });
        
        if (!response.ok) throw new Error('TTS failed');
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        elements.audioPlayer.src = audioUrl;
        
        // Play audio
        await elements.audioPlayer.play();
        
        // Update status when audio ends
        elements.audioPlayer.onended = () => {
            updateStatus('Entrevista em andamento', 'active');
            URL.revokeObjectURL(audioUrl);
        };
        
    } catch (error) {
        console.error('Error synthesizing speech:', error);
        showNotification('⚠️ Erro ao sintetizar voz (continuando sem áudio)', 'warning');
        updateStatus('Entrevista em andamento', 'active');
    }
}

// Evaluate Interview
async function evaluateInterview() {
    try {
        elements.evaluationModal.classList.remove('hidden');
        elements.evaluationContent.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Gerando avaliação final...</p>
            </div>
        `;
        
        const response = await fetch(`${API_BASE}/api/interview/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId
            })
        });
        
        if (!response.ok) throw new Error('Evaluation failed');
        
        const data = await response.json();
        
        // Render evaluation with markdown
        elements.evaluationContent.innerHTML = marked.parse(data.evaluation);
        
    } catch (error) {
        console.error('Error evaluating interview:', error);
        elements.evaluationContent.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <p style="color: #ef4444; font-size: 1.25rem;">❌ Erro ao gerar avaliação</p>
                <p style="color: #a1a1aa; margin-top: 0.5rem;">Tente novamente mais tarde</p>
            </div>
        `;
    }
}

// Close Evaluation Modal
function closeEvaluationModal() {
    elements.evaluationModal.classList.add('hidden');
}

// Reset Interview
function resetInterview() {
    if (confirm('Deseja realmente iniciar uma nova entrevista? O progresso atual será perdido.')) {
        state.sessionId = null;
        elements.interviewPanel.classList.add('hidden');
        elements.setupPanel.classList.remove('hidden');
        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">👋</div>
                <h3>Bem-vindo ao Entrevistador IA!</h3>
                <p>Aguardando início da entrevista...</p>
            </div>
        `;
        updateStatus('Pronto', 'ready');
    }
}

// Switch Tab
function switchTab(tab) {
    state.currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    // Update input content
    if (tab === 'voice') {
        elements.voiceInput.classList.remove('hidden');
        elements.codeInput.classList.add('hidden');
    } else {
        elements.voiceInput.classList.add('hidden');
        elements.codeInput.classList.remove('hidden');
    }
}

// Add User Message
function addUserMessage(text, isCode = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    
    const icon = isCode ? '💻' : '👤';
    const label = isCode ? 'Você (Código)' : 'Você';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">${icon}</span>
            <span>${label}</span>
        </div>
        <div class="message-content">
            ${isCode ? `<pre><code>${escapeHtml(text)}</code></pre>` : escapeHtml(text)}
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Add Assistant Message
function addAssistantMessage(falar, codigo) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    let content = '';
    
    if (falar) {
        content += `<div style="margin-bottom: 1rem; padding: 0.75rem; background: rgba(99, 102, 241, 0.1); border-radius: 8px; border-left: 3px solid #6366f1;">
            <strong>🔊 Falando:</strong> ${escapeHtml(falar)}
        </div>`;
    }
    
    if (codigo) {
        content += marked.parse(codigo);
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-icon">🤖</span>
            <span>Entrevistador IA</span>
        </div>
        <div class="message-content">
            ${content}
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Update Status
function updateStatus(text, type = 'ready') {
    const statusText = elements.status.querySelector('.status-text');
    const statusDot = elements.status.querySelector('.status-dot');
    
    statusText.textContent = text;
    
    // Update dot color based on type
    const colors = {
        ready: '#14b8a6',
        active: '#14b8a6',
        recording: '#ef4444',
        processing: '#f59e0b',
        speaking: '#6366f1',
        error: '#ef4444'
    };
    
    statusDot.style.background = colors[type] || colors.ready;
}

// Show Notification
function showNotification(message, type = 'info') {
    // Simple console notification for now
    // You can enhance this with a toast notification library
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Scroll to Bottom
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
