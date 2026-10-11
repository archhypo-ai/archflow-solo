fn main() {
    // Avoid a blank WebKitGTK window on Linux/Wayland drivers affected by
    // DMA-BUF allocation issues.
    #[cfg(target_os = "linux")]
    if std::env::var_os("WEBKIT_DISABLE_DMABUF_RENDERER").is_none() {
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }

    archwise_desktop_lib::run();
}
