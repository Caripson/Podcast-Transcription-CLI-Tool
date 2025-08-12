# Echo Plugin (Example)

This is a minimal example plugin for `podcast-transcriber` that registers an `echo` service via entry points.

Install locally (editable):

```
pip install -e examples/plugin_echo
```

Use in CLI:

```
podcast-transcriber --url ./examples/tone.wav --service echo --output out.txt
```

The service returns a trivial transcript like `ECHO: <path>` and demonstrates plugin discovery.
