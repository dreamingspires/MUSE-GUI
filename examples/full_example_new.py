from muse_gui.frontend.windows import (
    boot_initial_window,
    boot_tabbed_window,
    configure_theme,
)

if __name__ == "__main__":
    font = configure_theme()
    import_bool, import_file_path = boot_initial_window(font=font)
    if import_bool is not None:
        boot_tabbed_window(import_bool, font, import_file_path)
