"""Vérifications Windows : focus, clic/glissement, erreurs et insertion ciblée."""
import unittest
from unittest.mock import patch, Mock
import threading
import tkinter as tk
from affichage_bouton import WS_EX_LAYERED
from dictee_windows import DictationApp, get_long, ANIMATED, BUTTON_SIZE, STATES
from dictee import insert_text

class WindowsTests(unittest.TestCase):
    def setUp(self):
        self.app = DictationApp(preview=True)
        self.app.root.update()

    def tearDown(self):
        self.app.close()

    def test_no_activation_and_button_drag(self):
        app = self.app
        self.assertTrue(get_long(app.hwnd, -20) & 0x08000000)
        self.assertEqual(app.window_proc(app.hwnd, 0x21, 0, 0), 3)
        app.canvas.event_generate('<ButtonPress-1>', x=28, y=28)
        app.canvas.event_generate('<ButtonRelease-1>', x=28, y=28)
        self.assertEqual(app.state, 'recording')
        app.canvas.event_generate('<ButtonPress-1>', x=28, y=28)
        app.canvas.event_generate('<B1-Motion>', x=40, y=35)
        app.canvas.event_generate('<ButtonRelease-1>', x=40, y=35)
        self.assertEqual(app.state, 'recording', 'Un glissement ne doit pas arrêter le micro')

    def test_button_frames(self):
        frames = self.app.frames
        self.assertEqual(set(frames), set(STATES))
        for state, images in frames.items():
            if state not in ANIMATED:
                self.assertEqual(len(images), 3, state)
            for image in images:
                self.assertEqual(len(image), BUTTON_SIZE*BUTTON_SIZE*4)
                self.assertEqual(image[3], 0, 'Coin transparent')
                center = ((BUTTON_SIZE//2)*BUTTON_SIZE + BUTTON_SIZE//2)*4
                self.assertGreater(image[center+3], 120, 'Centre visible pendant les animations')
                # BGRA prémultiplié : aucun canal ne dépasse l'alpha.
                self.assertTrue(all(max(image[i:i+3]) <= image[i+3] for i in range(0, len(image), 4)))

    def test_layered_hover_press(self):
        app = self.app
        self.assertTrue(app.layered)
        self.assertTrue(get_long(app.hwnd, -20) & WS_EX_LAYERED)
        self.assertIs(app.shown, app.frames['ready'][0])
        app.canvas.event_generate('<Enter>', x=28, y=28)
        self.assertIs(app.shown, app.frames['ready'][1])
        app.canvas.event_generate('<ButtonPress-1>', x=28, y=28)
        self.assertIs(app.shown, app.frames['ready'][2])
        app.canvas.event_generate('<ButtonRelease-1>', x=28, y=28)
        self.assertEqual(app.state, 'recording')
        self.assertIn(app.shown, app.frames['recording'])
        app.canvas.event_generate('<Leave>')
        self.assertFalse(app.hover)

    def test_animation_advances(self):
        app = self.app
        app.set_state('recording')
        first = app.shown
        app.poll()
        self.assertIsNot(app.shown, first)
        self.assertIn(app.shown, app.frames['recording'])

    def test_windows_theme_change_preserves_state(self):
        app = self.app
        app.set_state('recording')
        other = 'sombre' if app.theme == 'clair' else 'clair'
        with patch('dictee_windows.windows_theme', return_value=other):
            app.window_proc(app.hwnd, 0x001A, 0, 0)
            app.poll()
        self.assertEqual(app.theme, other)
        self.assertEqual(app.state, 'recording')
        self.assertIn(app.shown, app.frames_by_theme[other]['recording'])

    def test_both_theme_assets(self):
        for theme, frames in self.app.frames_by_theme.items():
            self.assertEqual(set(frames), set(STATES), theme)
            for state, images in frames.items():
                self.assertEqual(len(images), 16 if state == 'recording' else 12 if state in ANIMATED else 3)
                self.assertTrue(all(len(frame) == BUTTON_SIZE * BUTTON_SIZE * 4 for frame in images))

    def prepare_transcription(self):
        app = self.app
        app.asr = Mock(return_value={'text': 'Bonjour été 😀'})
        app.sample_rate = 16000
        app.state = 'busy'
        return app

    def drain(self):
        self.app.poll()

    def test_focus_change_keeps_text_for_copy(self):
        app = self.prepare_transcription()
        with patch('dictee_windows.user32') as win, patch('dictee_windows.insert_text') as insert:
            win.GetAsyncKeyState.return_value = 0
            win.IsWindow.return_value = True
            win.GetForegroundWindow.return_value = 22
            app.transcribe([], 11)
            self.drain()
            insert.assert_not_called()
        self.assertEqual(app.last_text, 'Bonjour été 😀')
        self.assertEqual(app.state, 'recover')
        with patch.object(app.root, 'clipboard_clear') as clear, patch.object(app.root, 'clipboard_append') as copy:
            app.copy_text()
            clear.assert_called_once()
            copy.assert_called_once_with(app.last_text)
        self.assertEqual(app.state, 'ready')

    def test_same_window_inserts_and_returns_ready(self):
        app = self.prepare_transcription()
        with patch('dictee_windows.user32') as win, patch('dictee_windows.insert_text') as insert:
            win.GetAsyncKeyState.return_value = 0
            win.IsWindow.return_value = True
            win.GetForegroundWindow.return_value = 11
            app.transcribe([], 11)
            self.drain()
            insert.assert_called_once_with('Bonjour été 😀', 11, app.cancelled)
        self.assertEqual(app.state, 'ready')

    def test_failure_keeps_transcription(self):
        app = self.prepare_transcription()
        with self.assertLogs(level='ERROR'), patch('dictee_windows.user32') as win, patch('dictee_windows.insert_text', side_effect=OSError('test')):
            win.GetAsyncKeyState.return_value = 0
            win.IsWindow.return_value = True
            win.GetForegroundWindow.return_value = 11
            app.transcribe([], 11)
            self.drain()
        self.assertEqual(app.state, 'error')
        self.assertEqual(app.last_text, 'Bonjour été 😀')

    def test_close_cancels_insertion(self):
        app = self.prepare_transcription()
        app.cancelled.set()
        with patch('dictee_windows.user32') as win, patch('dictee_windows.insert_text') as insert:
            win.GetAsyncKeyState.return_value = 0
            app.transcribe([], 11)
            insert.assert_not_called()

    def test_record_stop_and_busy_guard(self):
        app = self.app
        app.preview = False
        app.sd = Mock()
        app.np = Mock()
        app.sample_rate = 16000
        stream = app.sd.InputStream.return_value
        with patch('dictee_windows.user32') as win, patch.object(app, 'beep'), patch('dictee_windows.threading.Thread') as worker:
            win.GetForegroundWindow.return_value = 11
            app.toggle()
            self.assertEqual(app.state, 'recording')
            stream.start.assert_called_once()
            data = Mock()
            app.capture(data, 10, None, None)
            app.toggle()
            self.assertEqual(app.state, 'busy')
            stream.stop.assert_called_once()
            stream.close.assert_called_once()
            worker.return_value.start.assert_called_once()
            app.toggle()
            app.sd.InputStream.assert_called_once()

    def test_unicode_and_foreground_guard(self):
        with patch('dictee.user32') as win, patch('dictee.time.sleep'):
            win.GetForegroundWindow.return_value = 11
            win.SendInput.return_value = 2
            insert_text('é😀', 11)
            self.assertEqual(win.SendInput.call_count, 3)  # 1 + paire UTF-16
            win.GetForegroundWindow.return_value = 22
            with self.assertRaises(RuntimeError):
                insert_text('x', 11)
            self.assertEqual(win.SendInput.call_count, 3)

if __name__ == '__main__':
    unittest.main()
