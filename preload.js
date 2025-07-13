const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {

    runAiTask: (args) => ipcRenderer.invoke('run-ai-task', args),

    openDialog: (options) => ipcRenderer.invoke('dialog:openFile', options),

    saveDialog: (options) => ipcRenderer.invoke('dialog:saveFile', options),
    
    runPython: (args) => ipcRenderer.send('run-python', args),
    
    onPythonProgress: (callback) => ipcRenderer.on('python-progress', (_event, value) => callback(value)),
    onPythonDone: (callback) => ipcRenderer.on('python-done', (_event, value) => callback(value)),
});