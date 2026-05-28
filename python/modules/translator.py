# modules/translator.py — Language translation using Ollama
# Supports all ~130+ Google Translate languages

from ai.ollama_client import ollama
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Full language map: key → (display name, ISO/Whisper code) ─────────────
LANGUAGES = {
    "afrikaans":           ("Afrikaans",              "af"),
    "albanian":            ("Albanian",               "sq"),
    "amharic":             ("Amharic",                "am"),
    "arabic":              ("Arabic",                 "ar"),
    "armenian":            ("Armenian",               "hy"),
    "assamese":            ("Assamese",               "as"),
    "aymara":              ("Aymara",                 "ay"),
    "azerbaijani":         ("Azerbaijani",            "az"),
    "bambara":             ("Bambara",                "bm"),
    "basque":              ("Basque",                 "eu"),
    "belarusian":          ("Belarusian",             "be"),
    "bengali":             ("Bengali",                "bn"),
    "bhojpuri":            ("Bhojpuri",               "bho"),
    "bosnian":             ("Bosnian",                "bs"),
    "bulgarian":           ("Bulgarian",              "bg"),
    "catalan":             ("Catalan",                "ca"),
    "cebuano":             ("Cebuano",                "ceb"),
    "chichewa":            ("Chichewa",               "ny"),
    "chinese_simplified":  ("Chinese (Simplified)",   "zh-CN"),
    "chinese_traditional": ("Chinese (Traditional)",  "zh-TW"),
    "corsican":            ("Corsican",               "co"),
    "croatian":            ("Croatian",               "hr"),
    "czech":               ("Czech",                  "cs"),
    "danish":              ("Danish",                 "da"),
    "dhivehi":             ("Dhivehi",                "dv"),
    "dogri":               ("Dogri",                  "doi"),
    "dutch":               ("Dutch",                  "nl"),
    "english":             ("English",                "en"),
    "esperanto":           ("Esperanto",              "eo"),
    "estonian":            ("Estonian",               "et"),
    "ewe":                 ("Ewe",                    "ee"),
    "filipino":            ("Filipino",               "tl"),
    "finnish":             ("Finnish",                "fi"),
    "french":              ("French",                 "fr"),
    "frisian":             ("Frisian",                "fy"),
    "galician":            ("Galician",               "gl"),
    "georgian":            ("Georgian",               "ka"),
    "german":              ("German",                 "de"),
    "greek":               ("Greek",                  "el"),
    "guarani":             ("Guarani",                "gn"),
    "gujarati":            ("Gujarati",               "gu"),
    "haitian_creole":      ("Haitian Creole",         "ht"),
    "hausa":               ("Hausa",                  "ha"),
    "hawaiian":            ("Hawaiian",               "haw"),
    "hebrew":              ("Hebrew",                 "iw"),
    "hindi":               ("Hindi",                  "hi"),
    "hmong":               ("Hmong",                  "hmn"),
    "hungarian":           ("Hungarian",              "hu"),
    "icelandic":           ("Icelandic",              "is"),
    "igbo":                ("Igbo",                   "ig"),
    "ilocano":             ("Ilocano",                "ilo"),
    "indonesian":          ("Indonesian",             "id"),
    "irish":               ("Irish",                  "ga"),
    "italian":             ("Italian",                "it"),
    "japanese":            ("Japanese",               "ja"),
    "javanese":            ("Javanese",               "jw"),
    "kannada":             ("Kannada",                "kn"),
    "kazakh":              ("Kazakh",                 "kk"),
    "khmer":               ("Khmer",                  "km"),
    "kinyarwanda":         ("Kinyarwanda",            "rw"),
    "konkani":             ("Konkani",                "gom"),
    "korean":              ("Korean",                 "ko"),
    "krio":                ("Krio",                   "kri"),
    "kurdish_kurmanji":    ("Kurdish (Kurmanji)",     "ku"),
    "kurdish_sorani":      ("Kurdish (Sorani)",       "ckb"),
    "kyrgyz":              ("Kyrgyz",                 "ky"),
    "lao":                 ("Lao",                    "lo"),
    "latin":               ("Latin",                  "la"),
    "latvian":             ("Latvian",                "lv"),
    "lingala":             ("Lingala",                "ln"),
    "lithuanian":          ("Lithuanian",             "lt"),
    "luganda":             ("Luganda",                "lg"),
    "luxembourgish":       ("Luxembourgish",          "lb"),
    "macedonian":          ("Macedonian",             "mk"),
    "maithili":            ("Maithili",               "mai"),
    "malagasy":            ("Malagasy",               "mg"),
    "malay":               ("Malay",                  "ms"),
    "malayalam":           ("Malayalam",              "ml"),
    "maltese":             ("Maltese",                "mt"),
    "maori":               ("Māori",                  "mi"),
    "marathi":             ("Marathi",                "mr"),
    "meitei":              ("Meitei (Manipuri)",      "mni-Mtei"),
    "mizo":                ("Mizo",                   "lus"),
    "mongolian":           ("Mongolian",              "mn"),
    "myanmar":             ("Myanmar (Burmese)",      "my"),
    "nepali":              ("Nepali",                 "ne"),
    "norwegian":           ("Norwegian",              "no"),
    "odia":                ("Odia (Oriya)",           "or"),
    "oromo":               ("Oromo",                  "om"),
    "pashto":              ("Pashto",                 "ps"),
    "persian":             ("Persian",                "fa"),
    "polish":              ("Polish",                 "pl"),
    "portuguese":          ("Portuguese",             "pt"),
    "punjabi":             ("Punjabi",                "pa"),
    "quechua":             ("Quechua",                "qu"),
    "romanian":            ("Romanian",               "ro"),
    "russian":             ("Russian",                "ru"),
    "samoan":              ("Samoan",                 "sm"),
    "sanskrit":            ("Sanskrit",               "sa"),
    "scots_gaelic":        ("Scots Gaelic",           "gd"),
    "sepedi":              ("Sepedi",                 "nso"),
    "serbian":             ("Serbian",                "sr"),
    "sesotho":             ("Sesotho",                "st"),
    "shona":               ("Shona",                  "sn"),
    "sindhi":              ("Sindhi",                 "sd"),
    "sinhala":             ("Sinhala",                "si"),
    "slovak":              ("Slovak",                 "sk"),
    "slovenian":           ("Slovenian",              "sl"),
    "somali":              ("Somali",                 "so"),
    "spanish":             ("Spanish",                "es"),
    "sundanese":           ("Sundanese",              "su"),
    "swahili":             ("Swahili",                "sw"),
    "swedish":             ("Swedish",                "sv"),
    "tajik":               ("Tajik",                  "tg"),
    "tamil":               ("Tamil",                  "ta"),
    "tatar":               ("Tatar",                  "tt"),
    "telugu":              ("Telugu",                 "te"),
    "thai":                ("Thai",                   "th"),
    "tigrinya":            ("Tigrinya",               "ti"),
    "tsonga":              ("Tsonga",                 "ts"),
    "turkish":             ("Turkish",                "tr"),
    "turkmen":             ("Turkmen",                "tk"),
    "twi":                 ("Twi",                    "ak"),
    "ukrainian":           ("Ukrainian",              "uk"),
    "urdu":                ("Urdu",                   "ur"),
    "uyghur":              ("Uyghur",                 "ug"),
    "uzbek":               ("Uzbek",                  "uz"),
    "vietnamese":          ("Vietnamese",             "vi"),
    "welsh":               ("Welsh",                  "cy"),
    "xhosa":               ("Xhosa",                  "xh"),
    "yiddish":             ("Yiddish",                "yi"),
    "yoruba":              ("Yoruba",                 "yo"),
    "zulu":                ("Zulu",                   "zu"),
}

# Script guidance per language — tells Ollama what writing system to use
SCRIPT_HINTS = {
    "arabic":              "Arabic script (right-to-left)",
    "armenian":            "Armenian script",
    "assamese":            "Bengali/Assamese script",
    "bengali":             "Bengali script",
    "chinese_simplified":  "Simplified Chinese characters",
    "chinese_traditional": "Traditional Chinese characters",
    "dhivehi":             "Thaana script (right-to-left)",
    "georgian":            "Georgian (Mkhedruli) script",
    "greek":               "Greek script",
    "gujarati":            "Gujarati script",
    "hebrew":              "Hebrew script (right-to-left)",
    "hindi":               "Devanagari script",
    "japanese":            "Japanese (mix of Hiragana, Katakana, Kanji)",
    "kannada":             "Kannada script",
    "khmer":               "Khmer script",
    "korean":              "Hangul script",
    "lao":                 "Lao script",
    "malayalam":           "Malayalam script",
    "marathi":             "Devanagari script",
    "myanmar":             "Myanmar (Burmese) script",
    "nepali":              "Devanagari script",
    "odia":                "Odia script",
    "persian":             "Persian script (right-to-left)",
    "punjabi":             "Gurmukhi script",
    "russian":             "Cyrillic script",
    "sanskrit":            "Devanagari script",
    "sinhala":             "Sinhala script",
    "tamil":               "Tamil script",
    "telugu":              "Telugu script",
    "thai":                "Thai script",
    "tibetan":             "Tibetan script",
    "tigrinya":            "Ge'ez (Ethiopic) script",
    "ukrainian":           "Cyrillic script",
    "urdu":                "Nastaliq script (right-to-left)",
    "uyghur":              "Arabic/Perso-Arabic script",
    "yiddish":             "Hebrew script (right-to-left)",
}


def get_display_name(key: str) -> str:
    """Return the human-readable name for a language key."""
    entry = LANGUAGES.get(key.lower())
    return entry[0] if entry else key.title()


def translate(
    text:        str,
    source_lang: str,
    target_lang: str,
    formal:      bool = True,
) -> dict:
    """
    Translate text from source to target language.

    Args:
        text:        Text to translate
        source_lang: Language key e.g. 'english', 'hindi', 'japanese'
        target_lang: Language key e.g. 'french', 'arabic'
        formal:      True = native script, False = Roman/Latin transliteration

    Returns:
        Dict with translation and metadata
    """
    src_entry = LANGUAGES.get(source_lang.lower())
    tgt_entry = LANGUAGES.get(target_lang.lower())

    src_name = src_entry[0] if src_entry else source_lang.title()
    tgt_name = tgt_entry[0] if tgt_entry else target_lang.title()

    logger.info(f"Translating {src_name} → {tgt_name}: '{text[:60]}'")

    # Script / formality instruction
    if formal:
        script_hint = SCRIPT_HINTS.get(target_lang.lower(), "")
        if script_hint:
            script_instruction = (
                f"Write the translation in {tgt_name} using {script_hint}."
            )
        else:
            script_instruction = (
                f"Write the translation in {tgt_name} using its native writing system."
            )
    else:
        script_instruction = (
            f"Write the translation using Roman/Latin alphabet transliteration only. "
            f"Do NOT use any native script. "
            f"Example for Hindi: 'Namaste, aap kaise hain?' not 'नमस्ते, आप कैसे हैं?'"
        )

    prompt = f"""You are an expert multilingual translator.
Translate the following text from {src_name} to {tgt_name}.

{script_instruction}

Rules:
- Translate accurately and naturally
- Preserve the tone and formality of the original
- Return ONLY the translated text — no labels, no explanations, no quotes
- Do not add anything before or after the translation

Text to translate:
{text}

Translation:"""

    try:
        translation = ollama.prompt(prompt).strip()

        # Strip common unwanted prefixes that LLMs sometimes add
        unwanted_prefixes = [
            "Translation:", "Translated:", f"{tgt_name}:",
            f"In {tgt_name}:", "Here is the translation:",
            "Here's the translation:", "The translation is:",
            "Output:", "Result:",
        ]
        for prefix in unwanted_prefixes:
            if translation.lower().startswith(prefix.lower()):
                translation = translation[len(prefix):].strip()

        # Strip surrounding quotes if the model wrapped the answer
        if translation.startswith(("\"", "'", "\u201c", "\u2018")) and \
           translation.endswith(("\"", "'", "\u201d", "\u2019")):
            translation = translation[1:-1].strip()

        logger.info(f"Translated: '{translation[:80]}'")
        return {
            "success":     True,
            "original":    text,
            "translation": translation,
            "source":      src_name,
            "target":      tgt_name,
            "formal":      formal,
        }

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return {
            "success":  False,
            "error":    str(e),
            "original": text,
        }


def detect_language(text: str) -> dict:
    """
    Detect the language of a given text.
    Returns the language name and its key if recognised.
    """
    lang_list = ", ".join(name for name, _ in LANGUAGES.values())

    prompt = f"""Detect the language of the following text.
Return ONLY the language name — one of these options:
{lang_list}, or "Unknown" if none match.

Do not explain. Just the language name.

Text: "{text}"

Language:"""

    try:
        detected = ollama.prompt(prompt).strip().rstrip(".")

        # Find matching key
        matched_key = None
        for key, (name, _) in LANGUAGES.items():
            if name.lower() == detected.lower():
                matched_key = key
                break

        return {
            "language": detected,
            "key":      matched_key,
            "text":     text,
        }
    except Exception as e:
        return {"language": "Unknown", "key": None, "text": text, "error": str(e)}