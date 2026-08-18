use serde::Serialize;
use std::{env, fs, path::{Path, PathBuf}, process::Command};

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStatus { connected: bool, binary: String, version: String, error: String }

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CommandResult { success: bool, code: Option<i32>, stdout: String, stderr: String }

#[derive(Serialize)]
struct TreeItem { name: String, path: String, kind: String, children: Vec<TreeItem> }

fn oriel_binary() -> String { env::var("ORIEL_BIN").unwrap_or_else(|_| "oriel".into()) }

#[tauri::command]
fn runtime_status() -> RuntimeStatus {
    let binary = oriel_binary();
    match Command::new(&binary).arg("version").output() {
        Ok(out) => RuntimeStatus { connected: out.status.success(), binary, version: String::from_utf8_lossy(&out.stdout).trim().into(), error: String::from_utf8_lossy(&out.stderr).trim().into() },
        Err(e) => RuntimeStatus { connected: false, binary, version: String::new(), error: e.to_string() },
    }
}

#[tauri::command]
fn pick_folder() -> Option<String> { rfd::FileDialog::new().pick_folder().map(|p| p.to_string_lossy().into_owned()) }

fn ignored(name: &str) -> bool { matches!(name, ".git" | "node_modules" | "target" | "dist" | "build" | "__pycache__") }
fn scan(path: &Path, depth: usize) -> Vec<TreeItem> {
    if depth > 8 { return vec![]; }
    let mut out = vec![];
    if let Ok(rd) = fs::read_dir(path) {
        for e in rd.flatten() {
            let p=e.path(); let name=e.file_name().to_string_lossy().into_owned();
            if p.is_dir() && ignored(&name) { continue; }
            out.push(TreeItem { name, path:p.to_string_lossy().into_owned(), kind:if p.is_dir(){"folder".into()}else{"file".into()}, children:if p.is_dir(){scan(&p,depth+1)}else{vec![]} });
        }
    }
    out.sort_by(|a,b| (a.kind!="folder").cmp(&(b.kind!="folder")).then(a.name.to_lowercase().cmp(&b.name.to_lowercase()))); out
}

#[tauri::command]
fn scan_project(path: String) -> Vec<TreeItem> { scan(Path::new(&path),0) }
#[tauri::command]
fn read_file(path: String) -> Result<String,String> { fs::read_to_string(&path).map_err(|e|e.to_string()) }
#[tauri::command]
fn save_file(path: String, content: String) -> Result<(),String> { fs::write(&path,content).map_err(|e|e.to_string()) }

#[tauri::command]
fn run_oriel(cwd: String, args: Vec<String>) -> Result<CommandResult,String> {
    let out=Command::new(oriel_binary()).args(args).current_dir(PathBuf::from(cwd)).output().map_err(|e|e.to_string())?;
    Ok(CommandResult{success:out.status.success(),code:out.status.code(),stdout:String::from_utf8_lossy(&out.stdout).into_owned(),stderr:String::from_utf8_lossy(&out.stderr).into_owned()})
}

pub fn run() {
    tauri::Builder::default()
      .invoke_handler(tauri::generate_handler![runtime_status,pick_folder,scan_project,read_file,save_file,run_oriel])
      .run(tauri::generate_context!()).expect("error while running ORIEL IDE");
}
