import os
import sys
import json
import re
import ollama

model = os.getenv('OLLAMA_MODEL', 'translategemma:4b')

# allow passing an input file path as first arg, default to 'batch.json'
input_path = sys.argv[1] if len(sys.argv) > 1 else 'batch.json'

def translate_item(item, targets=None):
    print(f'targets passed to translate_item: {targets}')
    text = item.get('text') or item.get('content') or item.get('source')
    # honor per-item meta flag: if meta.translate is False, do not translate
    meta = item.get('meta', {}) if isinstance(item, dict) else {}
    if meta.get('translate') is False:
        return {'Source': text}
    # default sequence if not provided: English (reference), Malayalam, Kannada, Tamil, Telugu
    seq = targets or ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']
    results = {}
    for lang in seq:
        if lang.lower() in ('english', 'source'):
            results['Source'] = text
            continue
        # build prompt with deterministic single-sentence heuristic and per-language hints
        sentences = re.split(r'(?<=[.!?])\s+', text.strip()) if text else [""]
        force_single = (len([s for s in sentences if s.strip()]) == 1 and len(text) <= 250)

        # Use system message for instruction and user message for source text to avoid prompt-echo
        style_example = load_ref_example(lang)
        # For Malayalam and Kannada, include a short exemplar pair (source -> reference) to bias register
        pair_example = None
        if style_example and lang in ('Malayalam', 'Kannada'):
            src_example = sentences[0].strip() if sentences else ''
            pair_example = f"Example (source → {lang}):\n{src_example}\n{style_example}"
            instruction = build_prompt(lang, "", force_single_sentence=force_single, style_example=pair_example)
        else:
            instruction = build_prompt(lang, "", force_single_sentence=force_single, style_example=style_example)
        user_text = text or ""

        try:
            print(f'Translating to {lang}...')
            resp = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': instruction},
                    {'role': 'user', 'content': user_text}
                ]
            )
            # strip surrounding whitespace/newlines
            val = (resp.get('message', {}) or {}).get('content', '') or ''
            val = val.strip()

            # validation: if model echoed instruction block or the English source, retry once with a minimal prompt
            def looks_like_instruction_echo(s):
                if not s:
                    return False
                lower = s.lower()
                # contains explicit prompt markers
                if 'text:' in lower or '\n-' in s or '\n•' in s:
                    return True
                # echoed the source exactly (strong signal)
                if user_text.strip() and user_text.strip() in s:
                    return True
                return False

            if looks_like_instruction_echo(val):
                print(f'Validation: detected instruction-echo for {lang}, retrying with minimal prompt...')
                resp2 = ollama.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': f'Translate only: {user_text}'}]
                )
                val = (resp2.get('message', {}) or {}).get('content', '') or ''
                val = val.strip()

            # post-process: remove obvious instruction remnants (leading bullets/labels)
            clean_lines = []
            for ln in val.splitlines():
                s = ln.strip()
                if not s:
                    continue
                if s.startswith('-') or s.lower().startswith('text:') or s.lower().startswith('use '):
                    continue
                clean_lines.append(ln)
            final = '\n'.join(clean_lines).strip() or val

            # Additional cleaning: collapse excessive repeated words/phrases (common model artifact)
            def remove_repeated_patterns(text):
                # collapse repeated adjacent single words appearing 3+ times -> single instance
                text = re.sub(r"(\b\w+\b)(?:\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)
                # collapse repeated adjacent multi-word phrases (2+ words) repeated immediately
                text = re.sub(r"((?:\b\w+\b\s+){2,}\b\w+\b)(?:\s+\1){1,}", r"\1", text, flags=re.IGNORECASE)
                return text

            final = remove_repeated_patterns(final)

            print(f'-> {lang}: {len(final)} chars')
            results[lang] = final
        except Exception as e:
            print(f'ERROR translating to {lang}: {e}')
            results[lang] = f'ERROR: {e}'
    return results

def main():
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        outputs = []
        # user-specific sequence can be provided in file-level key 'sequence'
        file_sequence = None
        if isinstance(data, dict) and 'sequence' in data:
            file_sequence = data.get('sequence') or []
            # normalize: map 'English' -> 'Source' and ensure required langs present
            file_sequence = [ ('Source' if (isinstance(l, str) and l.lower()=='english') else l) for l in file_sequence if l ]
            required = ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']
            for lang in required:
                if lang not in file_sequence:
                    file_sequence.append(lang)
            print(f'file_sequence loaded from batch.json (normalized): {file_sequence}')
            items = data.get('items', [])
        else:
            items = data

        i = 0
        while i < len(items):
            item = items[i]
            # detect short header followed by longer content -> print header plain and handle next as main
            next_item = items[i+1] if i+1 < len(items) else None
            if next_item and len(item.get('text','')) < 80 and len(next_item.get('text','')) > len(item.get('text','')) + 20:
                # print header without English label
                print(item.get('text',''))
                # now translate the next_item as the main content
                translation = translate_item(next_item, targets=file_sequence)
                outputs.append({'input': next_item, 'translation': translation})
                seq = file_sequence or ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']
                for lang in seq:
                    # skip empty English placeholder for header; print content translations
                    key = 'Source' if lang.lower() in ('english','source') else lang
                    print(f'[{lang}] {translation.get(key, "")}')
                i += 2
                continue

            # default: translate this item normally
            translation = translate_item(item, targets=file_sequence)
            outputs.append({'input': item, 'translation': translation})
            seq = file_sequence or ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']
            for lang in seq:
                key = 'Source' if lang.lower() in ('english','source') else lang
                print(f'[{lang}] {translation.get(key, "")}')
            i += 1

        out_path = 'batch_output.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(outputs, f, ensure_ascii=False, indent=2)
        print(f'Wrote results to {out_path}')
    else:
        # fallback single example: translate the paragraph into the default sequence
        print('No batch.json found — running single default example')
        fallback_item = {
            'text': (
                'In the cacophonous theatre of our public discourse, nuance is routinely sacrificed at the altar of indignation, subtlety is throttled by the stranglehold of sensationalism, and reasoned dissent is caricatured as disloyalty by those who mistake decibel levels for intellectual depth.'
            )
        }
        seq = file_sequence or ['Source', 'Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']
        translation = translate_item(fallback_item, targets=seq)
        for lang in seq:
            print(f'[{lang}]')
            key = 'Source' if lang.lower() in ('english','source') else lang
            print(translation.get(key, ''))


def load_ref_example(lang):
    """Load first non-empty line from refs/<lang>.txt if present."""
    try:
        fname = os.path.join('refs', f"{lang.lower()}.txt")
        if os.path.exists(fname):
            with open(fname, 'r', encoding='utf-8') as f:
                for ln in f:
                    s = ln.strip()
                    if s:
                        return s
    except Exception:
        pass
    return None


def build_prompt(lang, text, force_single_sentence=False, style_example=None):
    """Construct a deterministic, language-aware translation prompt.

    - `lang` is the target language name (string)
    - `text` is the source text to translate
    - `force_single_sentence` when True will add an explicit note to keep translation to one sentence
    """
    lang = (lang or '').strip()
    base = (
        f"Translate to {lang}:\n"
        "- Use a formal, natural literary tone appropriate to standard written " + (lang or "the target language") + ".\n"
        "- Preserve full meaning, details, metaphors, and rhetorical style; do not summarize or simplify.\n"
        "- Do not add explanations, notes, transliterations, language tags, or metadata.\n"
        "- Preserve original punctuation and sentence structure where possible.\n"
        "- Output only the translated text (no surrounding quotes).\n"
        "- If any phrase cannot be translated, output exactly: UNABLE_TO_TRANSLATE\n\n"
    )

    # per-language strict preferences
    suffix_map = {
        'Hindi': 'Use formal standard Hindi; avoid Hinglish and casual Romanized words.',
        'Tamil': 'Prefer pure Tamil vocabulary appropriate to formal writing; avoid excessive Sanskrit/English insertions.',
        'Malayalam': 'Use formal written Malayalam (standard literary register), not colloquial dialect. Do not use Latin (English) script in the translation; render all terms in Malayalam script and avoid transliterations in Roman letters.',
        'Telugu': 'Use formal written Telugu style appropriate for literary texts.',
        'Kannada': 'Use standard formal Kannada appropriate for written prose.'
    }

    if lang in suffix_map:
        base += "\n" + suffix_map[lang]

    if style_example:
        base += "\n\nStyle example (do not copy verbatim; match tone and register):\n" + style_example

    if force_single_sentence:
        base += "\n\nNote: The source is a single short sentence; keep the translation to one sentence only."

    # Do NOT include the source text in the system instruction; pass it as the user message.
    return base

if __name__ == '__main__':
    main()