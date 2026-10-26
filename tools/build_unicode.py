"""Generate locale-independent Unicode properties with the pinned oracle."""

import argparse
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent.parent


def ranges(predicate):
    result = []
    start = None
    for code in range(0x110001):
        present = code < 0x110000 and predicate(chr(code))
        if present and start is None:
            start = code
        elif not present and start is not None:
            result.append((start, code - 1))
            start = None
    return result


def table(name, rows):
    return f'static const uint32_t {name}[][{len(rows[0])}] = {{\n' + ''.join(
        '    {' + ', '.join(f'0x{value:x}' for value in row) + '},\n' for row in rows) + '};\n'


DERIVED_PREFIXES = ("HANGUL SYLLABLE ", "CJK UNIFIED IDEOGRAPH-", "TANGUT IDEOGRAPH-", "CJK COMPATIBILITY IDEOGRAPH-",
                    "EGYPTIAN HIEROGLYPH-", "KHITAN SMALL SCRIPT CHARACTER-", "NUSHU CHARACTER-")


def byte_array(name, data):
    return f'static const unsigned char {name}[] = {{\n' + ''.join(
        '    ' + ','.join(map(str, data[start:start + 32])) + ',\n' for start in range(0, len(data), 32)) + '};\n'


def name_tables():
    """Character names and aliases for \\N{...}, as a word dictionary.

    Each record is the code point's delta from the previous record (LEB128),
    the length of its encoded words, and the words: ids below 128 take one
    byte, others two (0x80 | high, low). Words are numbered by frequency."""
    derived, entries = [], []
    for code in range(0x110000):
        name = unicodedata.name(chr(code), None)
        if name is None:
            continue
        prefix = next((index for index, prefix in enumerate(DERIVED_PREFIXES) if name.startswith(prefix)), None)
        if prefix is not None and (prefix == 0 or name == f'{DERIVED_PREFIXES[prefix]}{code:04X}'):
            if derived and derived[-1][2] == prefix and derived[-1][1] == code - 1:
                derived[-1][1] = code
            else:
                derived.append([code, code, prefix])
            continue
        entries.append((code, name))
    for line in (ROOT / 'tools' / 'NameAliases.txt').read_text().splitlines():
        if line and not line.startswith('#'):
            code, alias, _ = line.split(';')
            if unicodedata.lookup(alias) != chr(int(code, 16)):
                raise SystemExit(f'alias {alias} does not match the oracle')
            entries.append((int(code, 16), alias))
    entries.sort(key=lambda entry: entry[0])
    counts = {}
    for _, name in entries:
        for word in name.split(' '):
            counts[word] = counts.get(word, 0) + 1
    words = sorted(counts, key=lambda word: (-counts[word], word))
    ids = {word: index for index, word in enumerate(words)}
    text, offsets = bytearray(), []
    for word in words:
        offsets.append(len(text))
        text += word.encode('ascii') + b'\0'
    records, previous = bytearray(), 0
    for code, name in entries:
        delta = code - previous
        previous = code
        while True:
            records.append((delta & 127) | (128 if delta > 127 else 0))
            delta >>= 7
            if not delta:
                break
        encoded = bytearray()
        for word in name.split(' '):
            index = ids[word]
            encoded += bytes([index]) if index < 128 else bytes([128 | index >> 8, index & 255])
        records.append(len(encoded))
        records += encoded
    order = sorted(range(len(words)), key=lambda index: words[index])
    content = byte_array('unicode_name_words', text)
    content += 'static const uint32_t unicode_name_word_offsets[] = {\n' + ''.join(
        '    ' + ','.join(map(str, offsets[start:start + 16])) + ',\n' for start in range(0, len(offsets), 16)) + '};\n'
    content += 'static const uint16_t unicode_name_word_order[] = {\n' + ''.join(
        '    ' + ','.join(map(str, order[start:start + 16])) + ',\n' for start in range(0, len(order), 16)) + '};\n'
    content += byte_array('unicode_names', records)
    content += table('unicode_derived_names', derived)
    return content, len(entries), len(words)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sys.version_info[:3] != (3, 15, 0) or unicodedata.unidata_version != "17.0.0":
        raise SystemExit("Use the pinned Python 3.15.0 oracle with Unicode 17.0.0")
    nonprintable = ranges(lambda char: not char.isprintable())
    starts = ranges(str.isidentifier)
    continues = ranges(lambda char: ('A' + char).isidentifier())
    combining, decompositions, compositions, data = [], [], [], []
    for code in range(0x110000):
        char = chr(code)
        order = unicodedata.combining(char)
        if order:
            combining.append((code, order))
        # Hangul syllables use the algorithmic Unicode decomposition.
        if not 0xac00 <= code < 0xd7a4:
            decomposed = unicodedata.normalize('NFKD', char)
            if decomposed != char:
                decompositions.append((code, len(data), len(decomposed)))
                data.extend(map(ord, decomposed))
        canonical = unicodedata.decomposition(char).split()
        if len(canonical) == 2 and not canonical[0].startswith('<'):
            pair = [int(part, 16) for part in canonical]
            if unicodedata.normalize('NFC', ''.join(map(chr, pair))) == char:
                compositions.append((*pair, code))
    compositions.sort()
    # Case mappings are full mappings; final sigma is handled by the engine.
    cases, case_data = {}, []
    for kind in ('lower', 'upper', 'title', 'casefold'):
        rows = []
        for code in range(0x110000):
            char = chr(code)
            mapped = getattr(char, kind)()
            if mapped != char:
                rows.append((code, len(case_data), len(mapped)))
                case_data.extend(map(ord, mapped))
        cases[kind] = rows
    sigma_cased = lambda char: char.isupper() or char.islower() or unicodedata.category(char) == 'Lt'
    def case_ignorable(char):
        if sigma_cased(char):
            return ('A\u03a3' + char).lower()[1] == '\u03c2'
        return ('A' + char + '\u03a3').lower()[-1] == '\u03c2'
    decimal_runs = []
    for start, end in ranges(str.isdecimal):
        code = start
        while code <= end:
            value = unicodedata.decimal(chr(code))
            run = code
            while run + 1 <= end and unicodedata.decimal(chr(run + 1)) == unicodedata.decimal(chr(run)) + 1:
                run += 1
            decimal_runs.append((code, run, value))
            code = run + 1
    content = (
        "/* Generated by tools/build_unicode.py; do not edit.\n"
        " * Unicode 17.0.0, Python 3.15.0 properties, case mappings, normalization and names.\n"
        " * Unicode data license: docs/licenses/unicode.txt. */\n"
    )
    for name, rows in [('unicode_nonprintable', nonprintable), ('unicode_identifier_start', starts),
                       ('unicode_identifier_continue', continues), ('unicode_combining', combining),
                       ('unicode_decompositions', decompositions), ('unicode_compositions', compositions),
                       ('unicode_alpha', ranges(str.isalpha)), ('unicode_decimal', decimal_runs),
                       ('unicode_digit', ranges(str.isdigit)), ('unicode_numeric', ranges(str.isnumeric)),
                       ('unicode_space', ranges(str.isspace)), ('unicode_upper', ranges(str.isupper)),
                       ('unicode_lower', ranges(str.islower)),
                       ('unicode_titlecase', ranges(lambda char: unicodedata.category(char) == 'Lt')),
                       ('unicode_cased', ranges(sigma_cased)), ('unicode_case_ignorable', ranges(case_ignorable)),
                       ('unicode_to_lower', cases['lower']), ('unicode_to_upper', cases['upper']),
                       ('unicode_to_title', cases['title']), ('unicode_to_fold', cases['casefold'])]:
        content += table(name, rows)
    content += 'static const uint32_t unicode_decomposed[] = {\n'
    for start in range(0, len(data), 12):
        content += '    ' + ', '.join(f'0x{code:x}' for code in data[start:start + 12]) + ',\n'
    content += '};\n'
    content += 'static const uint32_t unicode_case_data[] = {\n'
    for start in range(0, len(case_data), 12):
        content += '    ' + ', '.join(f'0x{code:x}' for code in case_data[start:start + 12]) + ',\n'
    content += '};\n'
    names, name_count, word_count = name_tables()
    content += names
    path = ROOT / "spy-unicode.h"
    if args.check:
        if path.read_text() != content:
            raise SystemExit("spy-unicode.h is out of date")
    else:
        path.write_text(content)
    print(f'Unicode 17.0.0: {len(nonprintable)} non-printable ranges, '
          f'{len(starts)}/{len(continues)} identifier ranges, '
          f'{len(decompositions)} decompositions, {len(compositions)} compositions, '
          f'{name_count} names in {word_count} words')


if __name__ == "__main__":
    main()
