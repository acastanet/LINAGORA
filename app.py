"""Mini-interface locale pour tester le modèle de transcription LinTO."""

import warnings

import gradio as gr
import librosa
from moteur_dictee import MODEL, SAMPLE_RATE, get_asr


def transcribe(audio_path):
    if not audio_path:
        raise gr.Error("Enregistrez ou importez d'abord un fichier audio.")
    try:
        audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        if not len(audio):
            raise ValueError("Le fichier audio est vide.")
        # Parakeet calcule sa limite selon la durée audio ; l'avertissement
        # générique de Transformers ne reconnaît pas ce calcul automatique.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"Using the model-agnostic default `max_length`.*",
                category=UserWarning,
                module=r"transformers\.generation\.utils",
            )
            result = get_asr()({"array": audio, "sampling_rate": SAMPLE_RATE})
        return result["text"]
    except Exception as exc:
        raise gr.Error(f"Impossible de transcrire l'audio : {exc}") from exc


def prepare_recording(audio_path):
    if not audio_path:
        raise gr.Error("Aucun enregistrement disponible. Réessayez avec le micro.")
    return audio_path, None


def transcribe_recording(audio_path):
    return transcribe(audio_path), None


with gr.Blocks(title="Test LinTO STT français", delete_cache=(60, 60)) as demo:
    gr.Markdown(
        "# Test LinTO STT français\n"
        "Cliquez sur le micro pour parler, puis cliquez sur Arrêter : "
        "la transcription démarre automatiquement et le micro est prêt pour un nouvel essai. "
        "Le premier lancement télécharge et charge le modèle ; il peut prendre quelques minutes. "
        "Pour un premier essai, utilisez un extrait court (environ 30 secondes)."
    )
    with gr.Tab("Microphone"):
        microphone = gr.Audio(sources=["microphone"], type="filepath", label="Enregistrer")
    with gr.Tab("Fichier audio"):
        audio_input = gr.Audio(sources=["upload"], type="filepath", label="Fichier audio")
        button = gr.Button("Transcrire", variant="primary")
    output = gr.Textbox(label="Transcription", lines=8, interactive=True, buttons=["copy"])
    recording = gr.State()
    button.click(transcribe, inputs=audio_input, outputs=output, concurrency_id="transcription")
    microphone.stop_recording(
        prepare_recording, inputs=microphone, outputs=[recording, microphone], queue=False
    ).then(
        transcribe_recording, inputs=recording, outputs=[output, recording],
        concurrency_id="transcription"
    )


if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", inbrowser=True)
