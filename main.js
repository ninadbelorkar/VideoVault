require('dotenv').config();
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
    const win = new BrowserWindow({
        width: 940,
        height: 780,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        }
    });

    win.loadFile('src/index.html');

}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

ipcMain.handle('dialog:openFile', async (event, options) => {
    const { canceled, filePaths } = await dialog.showOpenDialog(options);
    if (canceled) {
        return [];
    } else {
        return filePaths;
    }
});

ipcMain.handle('dialog:saveFile', async (event, options) => {
    const { canceled, filePath } = await dialog.showSaveDialog(options);
    if (canceled) {
        return null;
    } else {
        return filePath;
    }
});

ipcMain.on('run-python', (event, args) => {
    const isPackaged = app.isPackaged;

    const pythonExecutable = isPackaged

      ? path.join(process.resourcesPath, 'engine.exe')
      : 'python';

    const scriptPath = isPackaged
      ? ''
      : path.join(__dirname, 'backend', 'engine.py');

    const allArgs = scriptPath ? [scriptPath, ...args] : args;

    console.log(`Running command: ${pythonExecutable} ${allArgs.join(' ')}`);

    const pyProc = spawn(pythonExecutable, allArgs);

    pyProc.stdout.on('data', (data) => {
        const message = data.toString();
        event.sender.send('python-progress', message);
    });

    pyProc.stderr.on('data', (data) => {
        const errorMessage = `ERROR: ${data.toString()}`;
        console.error(errorMessage);
        event.sender.send('python-progress', errorMessage);
    });

    pyProc.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        event.sender.send('python-done', code);
    });
});

ipcMain.handle('run-ai-task', (event, args) => {
    return new Promise((resolve, reject) => {
        const isPackaged = app.isPackaged;
        const pythonExecutable = isPackaged ? path.join(process.resourcesPath, 'engine.exe') : 'python';
        const scriptPath = isPackaged ? '' : path.join(__dirname, 'backend', 'engine.py');
        
        const allArgs = scriptPath ? [scriptPath, ...args] : args;
        console.log(`Running AI command: ${pythonExecutable} ${allArgs.join(' ')}`);

        const pyProc = spawn(pythonExecutable, allArgs);
        
        let result = '';
        pyProc.stdout.on('data', (data) => {
            result += data.toString();
        });

        pyProc.stderr.on('data', (data) => {
            console.error(`AI Task Error: ${data}`);
            reject(data.toString());
        });

        pyProc.on('close', (code) => {
            if (code === 0) {
                if (result.startsWith('AI_RESULT:')) {
                    resolve(result.substring(10));
                } else {
                    resolve(result);
                }
            } else {
                reject(`AI Task process exited with code ${code}`);
            }
        });
    });
});