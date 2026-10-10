# mini-arabic-gpt
A small GPT language model built from scratch and trained on Arabic text.

## Demo

The demo is a local Gradio app (`app/app.py`; specification in `docs/09-ui-spec.md`). It serves on `127.0.0.1` only and does not create a public link. The app does not exist yet; its launch command is expected to be:

```
.venv/Scripts/python.exe app/app.py
```

A short screen recording or GIF of the demo will be added here (task G19 of `docs/11-roadmap.md`).

## Troubleshooting

- **Hugging Face download fails with a xet/CAS error:** set `HF_HUB_DISABLE_XET=1` and retry.

## Contributors

- [Marwan280](https://github.com/Marwan280): data, model architecture, evaluation, generation.
- [ghadahamdy18](https://github.com/ghadahamdy18): tokenizer, training, testing, demo.

Tests are written first, by the author of the component or by the other person where that keeps them independent: Marwan also writes the tokenizer tests, and Ghada also writes the data tests and the core evaluation tests (`docs/11-roadmap.md`, P6).
