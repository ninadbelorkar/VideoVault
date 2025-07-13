let selectedMethod = '';
let currentMode = '';
let encode_selectedVideoPath = '';
let encode_filesToHide = [];
let decode_selectedVideoPath = '';
let decode_outputFolderPath = '';

const homePage = document.getElementById('home-page');
const processPage = document.getElementById('process-page');
const decodePage = document.getElementById('decode-page');
const progressSection = document.getElementById('progress-section');

const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');

const backButton = document.getElementById('back-to-home');
const processTitle = document.getElementById('process-title');
const selectVideoBtn = document.getElementById('select-video-btn');
const selectedVideoPathEl = document.getElementById('selected-video-path');
const addFilesBtn = document.getElementById('add-files-btn');
const fileList = document.getElementById('file-list');
const passwordInput = document.getElementById('password-input');
const startProcessBtn = document.getElementById('start-process-btn');

const backButtonDecode = document.getElementById('back-to-home-decode');
const decodeTitle = document.getElementById('decode-title');
const selectVideoDecodeBtn = document.getElementById('select-video-decode-btn');
const selectedVideoDecodePathEl = document.getElementById('selected-video-decode-path');
const passwordInputDecode = document.getElementById('password-input-decode');
const selectFolderDecodeBtn = document.getElementById('select-folder-decode-btn');
const selectedFolderDecodePathEl = document.getElementById('selected-folder-decode-path');
const startDecodeBtn = document.getElementById('start-decode-btn');

const suggestPasswordBtn = document.getElementById('suggest-password-btn');
const peekInsideBtn = document.getElementById('peek-inside-btn');
const manifestDisplay = document.getElementById('manifest-display');
const manifestText = document.getElementById('manifest-text');


function showPage(page) {
    homePage.classList.add('hidden');
    processPage.classList.add('hidden');
    decodePage.classList.add('hidden');
    progressSection.classList.add('hidden'); // Hide progress section on page change
    page.classList.remove('hidden');
}

document.querySelectorAll('.btn-encode').forEach(button => {
    button.addEventListener('click', () => setupProcessPage(button.dataset.method));
});
document.querySelectorAll('.btn-decode').forEach(button => {
    button.addEventListener('click', () => setupDecodePage(button.dataset.method));
});

backButton.addEventListener('click', () => {
    resetAllState();
    showPage(homePage);
});

backButtonDecode.addEventListener('click', () => {
    resetAllState();
    showPage(homePage);
});

function setupProcessPage(method) {
    selectedMethod = method;
    currentMode = 'encode';
    processTitle.textContent = `Encode: ${method.charAt(0).toUpperCase() + method.slice(1)} Method`;
    if (method === 'datareel') {
        selectVideoBtn.parentElement.classList.add('hidden');
    } else {
        selectVideoBtn.parentElement.classList.remove('hidden');
    }
    showPage(processPage);
}

function setupDecodePage(method) {
    selectedMethod = method;
    currentMode = 'decode';
    decodeTitle.textContent = `Decode: ${method.charAt(0).toUpperCase() + method.slice(1)} Method`;
    showPage(decodePage);
}

function resetAllState() {
    selectedMethod = '';
    currentMode = '';
    encode_selectedVideoPath = '';
    encode_filesToHide = [];
    fileList.innerHTML = '';
    selectedVideoPathEl.textContent = 'No video selected.';
    passwordInput.value = '';
    startProcessBtn.disabled = false;
    decode_selectedVideoPath = '';
    decode_outputFolderPath = '';
    selectedVideoDecodePathEl.textContent = 'No video selected.';
    passwordInputDecode.value = '';
    selectedFolderDecodePathEl.textContent = 'No folder selected.';
    startDecodeBtn.disabled = false;
    progressBar.style.width = '0%';
    progressBar.textContent = '';
    statusText.textContent = 'Waiting to start...';
}


selectVideoBtn.addEventListener('click', async () => {
    const filePaths = await window.electronAPI.openDialog({ title: 'Select Carrier Video', properties: ['openFile'], filters: [{ name: 'Videos', extensions: ['mp4', 'mov', 'avi'] }] });
    if (filePaths.length > 0) {
        encode_selectedVideoPath = filePaths[0];
        selectedVideoPathEl.textContent = encode_selectedVideoPath.split(/[\\/]/).pop();
    }
});

addFilesBtn.addEventListener('click', async () => {
    const filePaths = await window.electronAPI.openDialog({ title: 'Add Files to Hide', properties: ['openFile', 'multiSelections'] });
    encode_filesToHide.push(...filePaths);
    renderFileList();
});

function renderFileList() {
    fileList.innerHTML = '';
    encode_filesToHide.forEach(path => {
        const li = document.createElement('li');
        li.textContent = path.split(/[\\/]/).pop();
        fileList.appendChild(li);
    });
}

startProcessBtn.addEventListener('click', async () => {
    if ((selectedMethod !== 'datareel' && !encode_selectedVideoPath) || encode_filesToHide.length === 0) {
        statusText.textContent = "Error: Please select a video and files to hide.";
        progressSection.classList.remove('hidden');
        return;
    }
    if (selectedMethod === 'datareel' && encode_filesToHide.length === 0) {
        statusText.textContent = "Error: Please select files to hide.";
        progressSection.classList.remove('hidden');
        return;
    }

    // const filePath = await window.electronAPI.saveDialog({ title: 'Save Output File As', buttonLabel: 'Save', filters: [{ name: 'MP4 Video', extensions: ['mp4'] }]});
    let saveOptions = {
        title: 'Save Output File As',
        buttonLabel: 'Save',
    };

    
    if (selectedMethod === 'steganography') {
        saveOptions.filters = [{ name: 'AVI Video', extensions: ['avi'] }];
        saveOptions.defaultPath = 'encoded_steg.avi';
    } else {
        saveOptions.filters = [{ name: 'MP4 Video', extensions: ['mp4'] }];
        saveOptions.defaultPath = 'encoded.mp4';
    }
    const filePath = await window.electronAPI.saveDialog(saveOptions);


    if (!filePath) {
        statusText.textContent = "Save cancelled.";
        progressSection.classList.remove('hidden');
        return;
    }
    
    startProcessBtn.disabled = true;
    progressSection.classList.remove('hidden');

    const password = passwordInput.value;
    const args = ['--method', selectedMethod, '--mode', 'encode', '--output', filePath];
    if (password) { args.push('--password', password); }
    
    let inputFiles = [];
    if (selectedMethod !== 'datareel') { inputFiles.push(encode_selectedVideoPath); }
    inputFiles.push(...encode_filesToHide);
    args.push(...inputFiles);

    statusText.textContent = "Starting encoding...";
    progressBar.style.width = '0%';
    window.electronAPI.runPython(args);
});


selectVideoDecodeBtn.addEventListener('click', async () => {
    const filePaths = await window.electronAPI.openDialog({ title: 'Select Video to Decode', properties: ['openFile'], filters: [{ name: 'Videos', extensions: ['mp4', 'mov', 'avi'] }] });
    if (filePaths.length > 0) {
        decode_selectedVideoPath = filePaths[0];
        selectedVideoDecodePathEl.textContent = decode_selectedVideoPath.split(/[\\/]/).pop();
    }
});

selectFolderDecodeBtn.addEventListener('click', async () => {
    const filePaths = await window.electronAPI.openDialog({ title: 'Select Output Folder', properties: ['openDirectory'] });
    if (filePaths.length > 0) {
        decode_outputFolderPath = filePaths[0];
        selectedFolderDecodePathEl.textContent = decode_outputFolderPath;
    }
});

startDecodeBtn.addEventListener('click', async () => {
    if (!decode_selectedVideoPath || !decode_outputFolderPath) {
        statusText.textContent = "Error: Please select a video and an output folder.";
        progressSection.classList.remove('hidden');
        return;
    }

    startDecodeBtn.disabled = true;
    progressSection.classList.remove('hidden');

    const password = passwordInputDecode.value;
    const args = ['--method', selectedMethod, '--mode', 'decode', '--output', decode_outputFolderPath];
    if (password) { args.push('--password', password); }
    
    args.push(decode_selectedVideoPath);

    statusText.textContent = "Starting decoding...";
    progressBar.style.width = '0%';
    window.electronAPI.runPython(args);
});


suggestPasswordBtn.addEventListener('click', async () => {
    suggestPasswordBtn.disabled = true;
    suggestPasswordBtn.textContent = '🧠';

    try {
        const args = ['--mode', 'ai', '--ai-task', 'password'];
        const suggestedPassword = await window.electronAPI.runAiTask(args);
        
        passwordInput.value = suggestedPassword.trim();
        passwordInputDecode.value = suggestedPassword.trim();

    } catch (error) {
        console.error('Failed to suggest password:', error);
    } finally {
       
        suggestPasswordBtn.disabled = false;
        suggestPasswordBtn.textContent = '✨';
    }
});

peekInsideBtn.addEventListener('click', async () => {
    if (!decode_selectedVideoPath) {
        alert("Please select a video file first.");
        return;
    }

    manifestDisplay.classList.remove('hidden');
    manifestText.textContent = 'Analyzing... please wait.';
    peekInsideBtn.disabled = true;

    try {
        const args = ['--mode', 'ai', '--ai-task', 'peek', decode_selectedVideoPath];
        const result = await window.electronAPI.runAiTask(args);
        manifestText.textContent = result.trim();
    } catch (error) {
        console.error('Failed to peek inside:', error);
        manifestText.textContent = `Error: ${error}`;
    } finally {
        peekInsideBtn.disabled = false;
    }
});


window.electronAPI.onPythonProgress((message) => {
    console.log(`Python stdout: ${message}`);
    const progressMatch = message.match(/^PROGRESS:(\d+):(.*)$/);
    if (progressMatch) {
        const percentage = parseInt(progressMatch[1], 10);
        const statusMsg = progressMatch[2];
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${percentage}%`;
        statusText.textContent = statusMsg;
    } else {
        statusText.textContent = message;
    }
});

window.electronAPI.onPythonDone((code) => {
    console.log(`Python finished with code ${code}`);
    if (code === 0) {
        statusText.textContent = "Process completed successfully!";
        progressBar.style.width = `100%`;
        progressBar.textContent = `100%`;
    } else {
        statusText.textContent += " An error occurred. Check console for details.";
    }

    startProcessBtn.disabled = false;
    startDecodeBtn.disabled = false;
});