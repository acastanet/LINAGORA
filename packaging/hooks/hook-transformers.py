"""Imports différés utilisés par le seul modèle Parakeet embarqué."""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

datas = collect_data_files('transformers', include_py_files=True)
datas += copy_metadata('transformers', recursive=True)
hiddenimports = collect_submodules('transformers.models.parakeet')
hiddenimports += collect_submodules('transformers.models.auto')
hiddenimports += collect_submodules('transformers.generation')
hiddenimports += collect_submodules('transformers.pipelines')
module_collection_mode = 'pyz+py'
