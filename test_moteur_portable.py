"""Contrats du chargement portable, sans charger les poids en tests unitaires."""
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import moteur_dictee as engine

class EngineTests(unittest.TestCase):
    def tearDown(self):
        engine.get_asr.cache_clear()

    def test_portable_requires_its_own_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(engine,'PORTABLE',True), patch.object(engine,'MODEL_DIR',Path(tmp)):
            with self.assertRaisesRegex(FileNotFoundError,'modele'):
                engine.get_asr()

    def test_portable_cpu_offline_and_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/'model.safetensors').touch()
            pipeline=Mock()
            torch=types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=Mock(return_value=True)), set_num_threads=Mock())
            transformers=types.SimpleNamespace(pipeline=pipeline)
            with patch.object(engine,'PORTABLE',True), patch.object(engine,'MODEL_DIR',folder), patch.object(engine,'data_dir',return_value=folder), patch.dict('sys.modules',torch=torch,transformers=transformers), patch.dict(os.environ):
                first=engine.get_asr()
                self.assertIs(engine.get_asr(),first)
                pipeline.assert_called_once_with('automatic-speech-recognition',model=str(folder),device=-1)
                self.assertEqual(os.environ['HF_HUB_OFFLINE'],'1')
                self.assertEqual(os.environ['HF_HOME'],str(folder/'cache'))
                torch.cuda.is_available.assert_not_called()

    def test_source_keeps_cuda_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            pipeline=Mock()
            torch=types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda:True))
            with patch.object(engine,'PORTABLE',False), patch.object(engine,'MODEL_DIR',Path(tmp)), patch.dict('sys.modules',torch=torch,transformers=types.SimpleNamespace(pipeline=pipeline)):
                engine.get_asr()
                pipeline.assert_called_once_with('automatic-speech-recognition',model=engine.MODEL,device=0)

    def test_gpu_light_requires_local_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(engine, 'PORTABLE', False), patch.object(engine, 'MODEL_DIR', Path(tmp)), patch.dict(os.environ, {'DICTEE_GPU_LIGHT': '1'}):
            with self.assertRaisesRegex(FileNotFoundError, 'modele'):
                engine.get_asr()

    def test_gpu_light_uses_cuda_and_never_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'model.safetensors').touch()
            pipeline = Mock()
            cuda = types.SimpleNamespace(is_available=Mock(return_value=False))
            torch = types.SimpleNamespace(cuda=cuda)
            with patch.object(engine, 'PORTABLE', False), patch.object(engine, 'MODEL_DIR', folder), patch.object(engine, 'data_dir', return_value=folder), patch.dict(os.environ, {'DICTEE_GPU_LIGHT': '1'}), patch.dict('sys.modules', torch=torch, transformers=types.SimpleNamespace(pipeline=pipeline)):
                with self.assertRaisesRegex(RuntimeError, 'CUDA indisponible'):
                    engine.get_asr()
                pipeline.assert_not_called()
                cuda.is_available.return_value = True
                engine.get_asr()
                pipeline.assert_called_once_with('automatic-speech-recognition', model=str(folder), device=0)
                self.assertEqual(os.environ['HF_HUB_OFFLINE'], '1')

if __name__=='__main__':
    unittest.main()
