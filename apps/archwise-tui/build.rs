use std::fs;
use std::path::PathBuf;

fn main() {
    let manifest_path =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../libs/archwise-agent/pyproject.toml");
    println!("cargo:rerun-if-changed={}", manifest_path.display());

    let manifest = fs::read_to_string(&manifest_path).unwrap_or_else(|error| {
        panic!(
            "Could not read backend pyproject.toml at {}: {error}",
            manifest_path.display()
        )
    });
    let version = project_version(&manifest).unwrap_or_else(|| {
        panic!(
            "Could not find [project].version in {}",
            manifest_path.display()
        )
    });

    println!("cargo:rustc-env=ARCHWISE_BACKEND_API_VERSION={version}");
}

fn project_version(manifest: &str) -> Option<String> {
    let mut in_project = false;

    for line in manifest.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('[') {
            in_project = trimmed == "[project]";
            continue;
        }
        if !in_project || !trimmed.starts_with("version") {
            continue;
        }

        let (_, value) = trimmed.split_once('=')?;
        return Some(value.trim().trim_matches('"').to_owned());
    }

    None
}
