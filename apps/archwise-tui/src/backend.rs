use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::thread;

#[cfg(unix)]
use std::os::unix::process::CommandExt;
use std::time::Duration;

use color_eyre::eyre::{eyre, Result, WrapErr};

use crate::api::{BackendClient, DEFAULT_BACKEND_URL, REQUIRED_BACKEND_API_VERSION};

const STARTUP_ATTEMPTS: usize = 60;
const STARTUP_INTERVAL: Duration = Duration::from_millis(250);

pub struct BackendProcess {
    child: Option<Child>,
    client: BackendClient,
}

impl BackendProcess {
    pub fn start() -> Result<Self> {
        let client = BackendClient::new(DEFAULT_BACKEND_URL)?;

        // Reuse an already-running development backend instead of owning or
        // terminating a process started by another command.
        if let Ok(health) = client.health() {
            if health.status == "ok" && health.agent_ready {
                if health.api_version.as_deref() != Some(REQUIRED_BACKEND_API_VERSION) {
                    return Err(eyre!(
                        "An outdated ArchWise backend is already running. Restart the backend on port 8765 before starting the TUI."
                    ));
                }
                return Ok(Self {
                    child: None,
                    client,
                });
            }
        }

        let backend_dir = backend_directory()?;
        let uv = std::env::var_os("ARCHWISE_UV_BIN").unwrap_or_else(|| "uv".into());
        let mut command = Command::new(uv);
        command
            .args(["run", "python", "-m", "archwise_agent.backend.server"])
            .current_dir(&backend_dir)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        #[cfg(unix)]
        command.process_group(0);

        let child = command
            .spawn()
            .wrap_err("Could not start the ArchWise Python backend")?;

        let mut process = Self {
            child: Some(child),
            client,
        };
        process.wait_until_ready()?;
        Ok(process)
    }

    pub fn client(&self) -> BackendClient {
        self.client.clone()
    }

    fn is_ready(client: &BackendClient) -> bool {
        client
            .health()
            .map(|health| {
                health.status == "ok"
                    && health.agent_ready
                    && health.api_version.as_deref() == Some(REQUIRED_BACKEND_API_VERSION)
            })
            .unwrap_or(false)
    }

    fn wait_until_ready(&mut self) -> Result<()> {
        for _ in 0..STARTUP_ATTEMPTS {
            if Self::is_ready(&self.client) {
                return Ok(());
            }

            if let Some(child) = self.child.as_mut() {
                if let Some(status) = child
                    .try_wait()
                    .wrap_err("Could not inspect backend process")?
                {
                    return Err(eyre!("ArchWise backend exited during startup: {status}"));
                }
            }

            thread::sleep(STARTUP_INTERVAL);
        }

        Err(eyre!(
            "ArchWise backend did not become ready within {} seconds",
            STARTUP_ATTEMPTS as f64 * STARTUP_INTERVAL.as_secs_f64()
        ))
    }
}

impl Drop for BackendProcess {
    fn drop(&mut self) {
        let Some(child) = self.child.as_mut() else {
            return;
        };

        terminate_backend(child);
    }
}

#[cfg(unix)]
fn terminate_backend(child: &mut Child) {
    let process_group = child.id() as libc::pid_t;
    unsafe {
        libc::kill(-process_group, libc::SIGTERM);
    }

    for _ in 0..20 {
        match child.try_wait() {
            Ok(Some(_)) => return,
            Ok(None) => thread::sleep(Duration::from_millis(25)),
            Err(_) => break,
        }
    }

    unsafe {
        libc::kill(-process_group, libc::SIGKILL);
    }
    let _ = child.wait();
}

#[cfg(not(unix))]
fn terminate_backend(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

fn backend_directory() -> Result<PathBuf> {
    let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../libs/archwise-agent")
        .canonicalize()
        .wrap_err("Could not locate libs/archwise-agent")?;

    if !directory.is_dir() {
        return Err(eyre!(
            "Backend directory does not exist: {}",
            directory.display()
        ));
    }
    Ok(directory)
}
