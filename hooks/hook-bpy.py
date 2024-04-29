from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# hiddenimports = collect_submodules('bpy')
# datas = collect_data_files('bpy')
datas, binaries, hiddenimports = collect_all('bpy')
hiddenimports = collect_submodules('uuid')