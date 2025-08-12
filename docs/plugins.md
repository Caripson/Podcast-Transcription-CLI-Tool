# Plugins: Add Your Own Service

You can extend the CLI with new transcription services by publishing a Python package that registers an entry point in the `podcast_transcriber.services` group.

Requirements

- Export either a subclass of `TranscriptionService` or a zero-argument factory function returning an instance.
- Your package must be installed in the same environment as `podcast-transcriber`.

Entry point registration (in your plugin’s `pyproject.toml`)

```
[project.entry-points."podcast_transcriber.services"]
myservice = "my_package.my_module:MyService"
```

Minimal service interface

```
from podcast_transcriber.services.base import TranscriptionService

class MyService(TranscriptionService):
    name = "myservice"

    def transcribe(self, local_path: str, language: str | None = None) -> str:
        # Implement transcription and optionally set:
        #   self.last_segments = [{"start": 0.0, "end": 1.0, "text": "...", "speaker": "A"}, ...]
        #   self.last_words = [{"start": 0.00, "end": 0.12, "word": "Hello"}, ...]
        return "..."
```

How it’s discovered

- The CLI calls `importlib.metadata.entry_points(group="podcast_transcriber.services")` and loads each entry point.
- Plugin names become valid values for `--service` and are listed in `--interactive` mode.

Debugging tips

- Verify your entry points: `python -c "import importlib.metadata as m; print(m.entry_points(group='podcast_transcriber.services'))"`
- Ensure your service raises clear `RuntimeError`s when misconfigured (e.g., missing API keys) to surface good CLI errors.

Example plugin in this repo

- See `examples/plugin_echo/` for a minimal `echo` service you can install locally with `pip install -e examples/plugin_echo`.
