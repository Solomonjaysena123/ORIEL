const vscode = require('vscode');
const path = require('path');
const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
let client;
function activeFile(){const e=vscode.window.activeTextEditor;if(!e||!e.document.fileName.endsWith('.orl')){vscode.window.showErrorMessage('Open an ORIEL .orl file first.');return null;}return e.document;}
async function runInTerminal(command){const doc=activeFile();if(!doc)return;if(doc.isDirty)await doc.save();const t=vscode.window.createTerminal({name:'ORIEL',cwd:vscode.workspace.workspaceFolders?.[0]?.uri.fsPath||path.dirname(doc.fileName)});t.show(true);t.sendText(`oriel ${command} "${doc.fileName}"`);}
function activate(context){
  const serverOptions={command:'oriel',args:['lsp'],transport:TransportKind.stdio};
  const clientOptions={documentSelector:[{scheme:'file',language:'oriel'}],synchronize:{fileEvents:vscode.workspace.createFileSystemWatcher('**/*.orl')}};
  client=new LanguageClient('orielLanguageServer','ORIEL Language Server',serverOptions,clientOptions);
  context.subscriptions.push(client.start());
  context.subscriptions.push(
    vscode.commands.registerCommand('oriel.runFile',()=>runInTerminal('run')),
    vscode.commands.registerCommand('oriel.checkFile',()=>runInTerminal('check')),
    vscode.commands.registerCommand('oriel.compileFile',()=>runInTerminal('compile')),
    vscode.commands.registerCommand('oriel.profileFile',()=>runInTerminal('compile'))
  );
}
async function deactivate(){if(client)await client.stop();}
module.exports={activate,deactivate};
