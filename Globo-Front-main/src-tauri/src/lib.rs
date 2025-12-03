use std::process::Command;

#[tauri::command]
fn start_services() -> Result<String, String> {
    let tool = detect_compose_tool();
    let output = Command::new(&tool)
        .args(["up", "-d"])
        .current_dir("../../") // Assuming running from src-tauri, docker-compose is in root
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn stop_services() -> Result<String, String> {
    let tool = detect_compose_tool();
    let output = Command::new(&tool)
        .args(["down"])
        .current_dir("../../")
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn check_status() -> Result<String, String> {
    let tool = detect_compose_tool();
    let output = Command::new(&tool)
        .args(["ps"])
        .current_dir("../../")
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

fn detect_compose_tool() -> String {
    if Command::new("docker-compose").arg("version").output().is_ok() {
        "docker-compose".to_string()
    } else if Command::new("podman-compose").arg("version").output().is_ok() {
        "podman-compose".to_string()
    } else {
        "docker-compose".to_string() // Default fallback
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .invoke_handler(tauri::generate_handler![start_services, stop_services, check_status])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
