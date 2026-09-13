#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// Run the desktop shell.
///
/// The first desktop increment intentionally contains no agent or backend
/// integration. Tauri only owns the native window while React owns the UI.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running ArchWISE desktop application");
}
