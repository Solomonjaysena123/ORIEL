const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');

function quote(value) { return `"${String(value).replace(/"/g, '""')}"`; }
function workspacePath() { return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath; }
function terminal(cwd) { const t=vscode.window.createTerminal({name:'ORIEL',cwd}); t.show(true); return t; }
function activeFile() { const e=vscode.window.activeTextEditor; if(!e||(!e.document.fileName.endsWith('.orl'))) { vscode.window.showErrorMessage('Open an ORIEL .orl file first.'); return null; } return e.document; }
async function saveAndRun(cmd) { const d=activeFile(); if(!d)return; if(d.isDirty)await d.save(); terminal(workspacePath()||path.dirname(d.fileName)).sendText(`oriel ${cmd} ${quote(d.fileName)}`); }
function projectCmd(cmd) { const cwd=workspacePath(); if(!cwd){vscode.window.showErrorMessage('Open an ORIEL project folder first.');return;} terminal(cwd).sendText(`oriel ${cmd}`); }
async function createProject(){const name=await vscode.window.showInputBox({prompt:'Enter the new ORIEL project name'});if(!name)return;const folders=await vscode.window.showOpenDialog({canSelectFiles:false,canSelectFolders:true,canSelectMany:false});if(!folders?.length)return;terminal(folders[0].fsPath).sendText(`oriel new ${quote(name)} --path ${quote(folders[0].fsPath)}`);}

function activate(context){
 const diagnostics=vscode.languages.createDiagnosticCollection('oriel');
 
  const databaseSchema = vscode.commands.registerCommand('oriel.databaseSchema',()=>saveAndRun('db schema'));
  const databaseMigrate = vscode.commands.registerCommand('oriel.databaseMigrate',()=>saveAndRun('db migrate'));
  const generateOpenApi = vscode.commands.registerCommand('oriel.generateOpenApi',()=>saveAndRun('api openapi'));
context.subscriptions.push(diagnostics, databaseSchema, databaseMigrate, generateOpenApi);
 const validate=(doc)=>{if(doc.languageId!=='oriel'&&!doc.fileName.endsWith('.orl'))return; cp.execFile('oriel',['check',doc.fileName],{cwd:workspacePath()||path.dirname(doc.fileName)},(err,stdout,stderr)=>{if(!err){diagnostics.delete(doc.uri);return;} const text=stderr||stdout||String(err); const m=text.match(/error\[([^\]]+)\]:\s*([^\n]+)[\s\S]*?-->\s*.*?:(\d+):(\d+)/); if(m){const line=Math.max(0,Number(m[3])-1), col=Math.max(0,Number(m[4])-1); const d=new vscode.Diagnostic(new vscode.Range(line,col,line,col+1),m[2],vscode.DiagnosticSeverity.Error); d.code=m[1]; d.source='ORIEL'; diagnostics.set(doc.uri,[d]);} else {const d=new vscode.Diagnostic(new vscode.Range(0,0,0,1),text.trim(),vscode.DiagnosticSeverity.Error); d.source='ORIEL'; diagnostics.set(doc.uri,[d]);}});};
 context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(validate),vscode.workspace.onDidOpenTextDocument(validate));
 vscode.workspace.textDocuments.forEach(validate);
 const items=['fn','let','var','return','if','else','while','for','in','true','false','none','print','len','range','push','read_file','write_file','json_encode','json_decode','type_of','Int','Float','Number','String','Text','Bool','List','Map','Any','entity','api','get','post','put','patch','delete','required','unique','default','Id','Decimal'];
 context.subscriptions.push(vscode.languages.registerCompletionItemProvider('oriel',{provideCompletionItems(){return items.map(x=>new vscode.CompletionItem(x,['fn','let','var','return','if','else','while','for','in'].includes(x)?vscode.CompletionItemKind.Keyword:vscode.CompletionItemKind.Function));}}));
 context.subscriptions.push(vscode.languages.registerHoverProvider('oriel',{provideHover(doc,pos){const r=doc.getWordRangeAtPosition(pos);if(!r)return;const w=doc.getText(r);if(items.includes(w))return new vscode.Hover(`**ORIEL 0.5** \`${w}\``);}}));
 context.subscriptions.push(
  vscode.commands.registerCommand('oriel.runFile',()=>saveAndRun('run')),
  vscode.commands.registerCommand('oriel.checkFile',()=>saveAndRun('check')),
  vscode.commands.registerCommand('oriel.formatFile',()=>saveAndRun('format')),
  vscode.commands.registerCommand('oriel.testProject',()=>projectCmd('test')),
  vscode.commands.registerCommand('oriel.buildProject',()=>projectCmd('build')),
  vscode.commands.registerCommand('oriel.newProject',createProject),
  vscode.commands.registerCommand('oriel.installPackages',()=>projectCmd('install')),
  vscode.commands.registerCommand('oriel.listPackages',()=>projectCmd('packages'))
 );
}
function deactivate(){}
module.exports={activate,deactivate};
