import os
import sys
import json
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
        # clearer instructions to preserve meaning and detail in a single-line translation
        prompt = (
            f'Translate the following text to {lang}. '
            f'Provide a fluent, natural translation that preserves the full meaning and level of detail. '
            f'Output a single sentence only and do NOT include explanations, breakdowns, or transliterations. '
            f'If you cannot translate a phrase, write UNABLE_TO_TRANSLATE. Text: "{text}"'
        )
        try:
            print(f'Translating to {lang}...')
            resp = ollama.chat(model=model, messages=[{'role':'user','content':prompt}])
            # strip surrounding whitespace/newlines
            val = resp.get('message', {}).get('content') or ''
            val = val.strip()
            print(f'-> {lang}: {len(val)} chars')
            results[lang] = val
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

if __name__ == '__main__':
    main()