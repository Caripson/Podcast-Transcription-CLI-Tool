# Using Whisper Language Parameters

This page explains how to control language handling when using the local Whisper service (`--service whisper`).

- If you provide `--language`, the CLI passes a hint to Whisper.
- If you omit `--language` (or set it to `auto`), Whisper auto-detects the language.
- Regional variants like `en-US` are normalized to their primary code (e.g., `en`). Unsupported codes fall back to auto-detect.

## Quick Examples

```bash
# Force Swedish transcription
podcast-transcriber --url <URL|path> --service whisper --language sv --output out.txt

# English with a regional tag (normalized to `en`)
podcast-transcriber --url <URL|path> --service whisper --language en-US --output out.txt

# Auto-detect (omit or use an alias)
podcast-transcriber --url <URL|path> --service whisper --output out.txt
podcast-transcriber --url <URL|path> --service whisper --language auto --output out.txt
```

Requirements for Whisper: `ffmpeg` installed and Python package `openai-whisper`.

## Valid Language Codes

Whisper accepts the following primary language codes. Use these two-letter codes (regional variants like `pt-BR` normalize to `pt`).

```
en: english
zh: chinese
de: german
es: spanish
ru: russian
ko: korean
fr: french
ja: japanese
pt: portuguese
tr: turkish
pl: polish
ca: catalan
nl: dutch
ar: arabic
sv: swedish
it: italian
id: indonesian
hi: hindi
fi: finnish
vi: vietnamese
he: hebrew
uk: ukrainian
el: greek
ms: malay
cs: czech
ro: romanian
da: danish
hu: hungarian
ta: tamil
no: norwegian
th: thai
ur: urdu
hr: croatian
bg: bulgarian
lt: lithuanian
la: latin
mi: maori
ml: malayalam
cy: welsh
sk: slovak
te: telugu
fa: persian
lv: latvian
bn: bengali
sr: serbian
az: azerbaijani
sl: slovenian
kn: kannada
et: estonian
mk: macedonian
br: breton
eu: basque
is: icelandic
hy: armenian
ne: nepali
mn: mongolian
bs: bosnian
kk: kazakh
sq: albanian
sw: swahili
gl: galician
mr: marathi
pa: punjabi
si: sinhala
km: khmer
sn: shona
yo: yoruba
so: somali
af: afrikaans
oc: occitan
ka: georgian
be: belarusian
tg: tajik
sd: sindhi
gu: gujarati
am: amharic
yi: yiddish
lo: lao
uz: uzbek
fo: faroese
ht: haitian creole
ps: pashto
tk: turkmen
nn: nynorsk
mt: maltese
sa: sanskrit
lb: luxembourgish
my: myanmar
bo: tibetan
tl: tagalog
mg: malagasy
as: assamese
tt: tatar
haw: hawaiian
ln: lingala
ha: hausa
ba: bashkir
jw: javanese
su: sundanese
yue: cantonese
```

## Name Aliases Supported

You can also supply common language names, which the tool maps to the appropriate code. These aliases are recognized in addition to the names above:

- burmese → `my`
- valencian → `ca`
- flemish → `nl`
- haitian → `ht`
- letzeburgesch → `lb`
- pushto → `ps`
- panjabi → `pa`
- moldavian / moldovan → `ro`
- sinhalese → `si`
- castilian → `es`
- mandarin → `zh`

Note: Javanese may appear as `jv` in some contexts; Whisper expects `jw`, and the CLI normalizes this automatically.

## Behavior Details

- Unknown or unsupported codes: fall back to auto-detect (no error).
- Case/format tolerance: input is case-insensitive; underscores are treated like hyphens (e.g., `en_us` → `en-US` → `en`).
- Service scope: these codes apply to the local Whisper service only. For AWS/GCP languages, see the dedicated sections in the Services docs.

## Troubleshooting

- Ensure `ffmpeg` is on your `PATH`.
- Install Whisper: `pip install openai-whisper`.
- If results don’t match the expected language, try explicitly setting `--language` or removing it to allow auto-detect.
