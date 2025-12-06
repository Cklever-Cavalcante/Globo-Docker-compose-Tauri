use std::process::Command;
use std::path::PathBuf;
use std::fs;
use std::env;

#[tauri::command]
fn start_services() -> Result<String, String> {
    let tool = detect_compose_tool();
    let project_root = get_project_root();
    
    println!("Iniciando serviços Docker Compose...");
    println!("Diretório do projeto: {:?}", project_root);
    
    let output = Command::new(&tool)
        .args(["up", "-d"])
        .current_dir(&project_root)
        .output()
        .map_err(|e| format!("Erro ao executar {}: {}", tool, e))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        println!("Serviços iniciados com sucesso: {}", stdout);
        Ok(stdout)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        println!("Erro ao iniciar serviços: {}", stderr);
        Err(format!("Erro ao iniciar containers: {}", stderr))
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
    let project_root = get_project_root();
    
    let output = Command::new(&tool)
        .args(["ps"])
        .current_dir(&project_root)
        .output()
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn load_docker_images() -> Result<String, String> {
    println!("Carregando imagens Docker do bundle...");
    
    let resources_dir = get_resources_dir();
    let docker_images_dir = resources_dir.join("docker-images");
    
    if !docker_images_dir.exists() {
        return Err("Diretório de imagens Docker não encontrado".to_string());
    }
    
    let tar_files = ["postgres.tar", "backend.tar", "ia-service.tar"];
    let mut loaded_count = 0;
    
    for tar_file in &tar_files {
        let tar_path = docker_images_dir.join(tar_file);
        if tar_path.exists() {
            println!("Carregando {}...", tar_file);
            
            let output = Command::new("docker")
                .args(["load", "-i"])
                .arg(&tar_path)
                .output()
                .map_err(|e| format!("Erro ao carregar {}: {}", tar_file, e))?;
                
            if output.status.success() {
                loaded_count += 1;
                println!("{} carregada com sucesso", tar_file);
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                println!("Erro ao carregar {}: {}", tar_file, stderr);
            }
        } else {
            println!("Aviso: {} não encontrado", tar_file);
        }
    }
    
    Ok(format!("{} imagens Docker carregadas com sucesso", loaded_count))
}

#[tauri::command]
fn install_docker_desktop() -> Result<String, String> {
    println!("Verificando Docker Desktop...");
    
    // Verificar se Docker já está instalado
    if Command::new("docker").arg("version").output().is_ok() {
        return Ok("Docker Desktop já está instalado".to_string());
    }
    
    let resources_dir = get_resources_dir();
    
    #[cfg(target_os = "windows")]
    {
        let installer_path = resources_dir.join("installers").join("docker-desktop-installer.exe");
        
        if !installer_path.exists() {
            return Err("Instalador do Docker Desktop não encontrado no bundle".to_string());
        }
        
        println!("Instalando Docker Desktop...");
        
        let output = Command::new(&installer_path)
            .args(["install", "--quiet"])
            .output()
            .map_err(|e| format!("Erro ao executar instalador: {}", e))?;
            
        if output.status.success() {
            // Aguardar inicialização do Docker
            std::thread::sleep(std::time::Duration::from_secs(30));
            Ok("Docker Desktop instalado com sucesso".to_string())
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            Err(format!("Erro na instalação: {}", stderr))
        }
    }
    
    #[cfg(target_os = "macos")]
    {
        let installer_path = resources_dir.join("installers").join("Docker.dmg");
        
        if !installer_path.exists() {
            return Err("Instalador do Docker Desktop não encontrado no bundle".to_string());
        }
        
        println!("Instalando Docker Desktop para macOS...");
        
        // Montar o DMG e copiar o aplicativo
        let mount_output = Command::new("hdiutil")
            .args(&["attach", installer_path.to_str().unwrap()])
            .output()
            .map_err(|e| format!("Erro ao montar DMG: {}", e))?;
            
        if !mount_output.status.success() {
            let stderr = String::from_utf8_lossy(&mount_output.stderr);
            return Err(format!("Erro ao montar DMG: {}", stderr));
        }
        
        // Aguardar inicialização do Docker
        std::thread::sleep(std::time::Duration::from_secs(30));
        Ok("Docker Desktop instalado com sucesso no macOS".to_string())
    }
    
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        Err("Instalação automática disponível apenas para Windows e macOS".to_string())
    }
}

#[tauri::command]
fn setup_docker_environment() -> Result<String, String> {
    println!("Configurando ambiente Docker...");
    
    // 1. Verificar/instalar Docker Desktop
    match install_docker_desktop() {
        Ok(msg) => println!("{}", msg),
        Err(e) => println!("Aviso: {}", e),
    }
    
    // 2. Carregar imagens Docker
    match load_docker_images() {
        Ok(msg) => println!("{}", msg),
        Err(e) => println!("Aviso: {}", e),
    }
    
    Ok("Ambiente Docker configurado com sucesso".to_string())
}

fn get_resources_dir() -> PathBuf {
    let current_exe = env::current_exe().unwrap_or_else(|_| std::path::PathBuf::from("."));
    let exe_dir = current_exe.parent().unwrap_or_else(|| std::path::Path::new("."));
    
    // Procurar diretório de recursos
    let possible_paths = [
        exe_dir.join("resources"),
        exe_dir.parent().unwrap_or(exe_dir).join("resources"),
        PathBuf::from("resources"),
    ];
    
    for path in &possible_paths {
        if path.exists() {
            return path.clone();
        }
    }
    
    // Fallback para o diretório do executável
    exe_dir.to_path_buf()
}

fn get_project_root() -> PathBuf {
    // Tenta encontrar o diretório raiz do projeto
    let current_exe = std::env::current_exe().unwrap_or_else(|_| std::path::PathBuf::from("."));
    let mut path = current_exe.parent().unwrap_or_else(|| std::path::Path::new("."));
    
    // Sobe na hierarquia até encontrar o docker-compose.yml ou resources/docker-compose.yml
    while path.parent().is_some() {
        // Tenta docker-compose.yml no diretório raiz
        let compose_file = path.join("docker-compose.yml");
        if compose_file.exists() {
            return path.to_path_buf();
        }
        
        // Tenta resources/docker-compose.yml (para versão embarcada)
        let resources_compose_file = path.join("resources").join("docker-compose.yml");
        if resources_compose_file.exists() {
            return path.to_path_buf();
        }
        
        path = path.parent().unwrap();
    }
    
    // Fallback para o diretório atual
    std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."))
}

fn detect_compose_tool() -> String {
    if Command::new("docker").arg("compose").arg("version").output().is_ok() {
        "docker compose".to_string() // Docker Compose v2
    } else if Command::new("docker-compose").arg("version").output().is_ok() {
        "docker-compose".to_string() // Docker Compose v1
    } else if Command::new("podman-compose").arg("version").output().is_ok() {
        "podman-compose".to_string()
    } else {
        "docker compose".to_string() // Default fallback
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .invoke_handler(tauri::generate_handler![
        start_services, 
        stop_services, 
        check_status,
        load_docker_images,
        install_docker_desktop,
        setup_docker_environment
    ])
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
