import os
import sys
import json
import ollama

model = os.getenv('OLLAMA_MODEL', 'translategemma:4b')

# allow passing an input file path as first arg, default to 'batch.json'
input_path = sys.argv[1] if len(sys.argv) > 1 else 'batch.json'

def translate_item(item, targets=None):
    text = item.get('text') or item.get('content') or item.get('source')
    # default sequence if not provided: English (reference), Malayalam, Kannada, Tamil, Telugu
    seq = targets or ['English', 'Malayalam', 'Kannada', 'Tamil', 'Telugu']
    results = {}
    for lang in seq:
        if lang.lower() == 'english':
            results['English'] = text
            continue
        prompt = f'Translate "{text}" to {lang}.'
        try:
            resp = ollama.chat(model=model, messages=[{'role':'user','content':prompt}])
            results[lang] = resp.get('message', {}).get('content')
        except Exception as e:
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
            file_sequence = data.get('sequence')
            items = data.get('items', [])
        else:
            items = data

        for item in items:
            translation = translate_item(item, targets=file_sequence)
            outputs.append({'input': item, 'translation': translation})
            # print in requested order
            seq = file_sequence or ['English', 'Malayalam', 'Kannada', 'Tamil', 'Telugu']
            for lang in seq:
                print(f'[{lang}]')
                print(translation.get(lang, ''))

        out_path = 'batch_output.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(outputs, f, ensure_ascii=False, indent=2)
        print(f'Wrote results to {out_path}')
    else:
        # fallback single example: translate the paragraph into the default sequence
        print('No batch.json found — running single default example')
        fallback_item = {
            'text': (
                'Ah bearer of gourmet delights, glad you found the leisure to attend to my gastronomical requirements. '
                'I am feeling quite peckish, and a trifle breakfasty, if you get my drift, though it’s closer to lunch. '
                'Two eggs, lightly fried, sunny side up would just about hit the spot. And if you can manage some fried tomatoes, '
                'with bacon and sausages to go with it, my cup of joy will run over. And speaking of cups, a pot of black coffee, '
                'with a cosy to cover it, will be perfect. I will eschew sugar. Mildly diabetic, you know. Doctor’s orders. '
                'And an unchipped cup and saucer, Wedgwood or Royal Doulton preferably'
            )
        }
        seq = file_sequence or ['English', 'Malayalam', 'Kannada', 'Tamil', 'Telugu']
        translation = translate_item(fallback_item, targets=seq)
        for lang in seq:
            print(f'[{lang}]')
            print(translation.get(lang, ''))

if __name__ == '__main__':
    main()