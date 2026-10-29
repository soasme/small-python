"""Generate locale-independent Unicode properties with the pinned oracle.

The encodings follow QuickJS's libunicode: properties are run lengths with a
sparse index, mappings are runs of equal offsets, and decompositions are
single-level, so the engine expands them recursively."""

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


def array(kind, name, values, width=16):
    return f'static const {kind} {name}[] = {{\n' + ''.join(
        '    ' + ','.join(map(str, values[start:start + width])) + ',\n'
        for start in range(0, len(values), width)) + '};\n'


def property_table(name, predicate):
    """QuickJS's compressed run lengths, alternating false and true from U+0000:
    00..3F two packed 3-bit lengths, 40..5F 13 bits, 60..7F 21 bits and
    80..FF 7 bits; lengths are stored minus one. Every 32 bytes the index
    holds the code point of the first false run starting there (21 bits) and
    its distance past the block boundary (3 bits); its last entry ends the
    table."""
    runs, code = [], 0
    for start, end in ranges(predicate):
        runs += [start - code - 1, end - start]
        code = end + 1
    data, index, code, at = bytearray(), bytearray(), 0, 0
    while at < len(runs):
        due = len(data) >= 32 * (len(index) // 3 + 1)
        if due and at % 2 == 0:
            offset = len(data) - 32 * (len(index) // 3 + 1)
            assert offset <= 7
            index += (code | offset << 21).to_bytes(3, 'little')
            due = False
        value = runs[at]
        code += value + 1
        # A due entry waits for a false run, so it does not pack two runs.
        if value < 8 and at + 1 < len(runs) and runs[at + 1] < 8 and not due:
            code += runs[at + 1] + 1
            data.append(value << 3 | runs[at + 1])
            at += 2
            continue
        if value < 128:
            data.append(0x80 + value)
        elif value < 1 << 13:
            data += bytes([0x40 + (value >> 8), value & 255])
        else:
            data += bytes([0x60 + (value >> 16), value >> 8 & 255, value & 255])
        at += 1
    index += code.to_bytes(3, 'little')
    return array('uint8_t', f'unicode_prop_{name}', list(data), 32) + array('uint8_t', f'unicode_prop_{name}_index', list(index), 30)


def mapping_table(name, mapping, data):
    """Rows of start << 11 | count << 2 | kind and then a value. Kind 0 maps a run
    of count code points by an offset, kind 1 maps every second one, and kind
    2 maps one code point to count characters at value in the data."""
    rows = []
    for code in sorted(mapping):
        mapped = mapping[code]
        if len(mapped) != 1:
            rows.append([code, len(mapped), 2, len(data)])
            data.extend(map(ord, mapped))
            continue
        offset = (ord(mapped) - code) & 0xffffffff
        if rows and rows[-1][2] != 2 and rows[-1][3] == offset and rows[-1][1] < 511:
            start, count, kind, _ = rows[-1]
            if count == 1 and (code == start + 1 or code == start + 2 and code - 1 not in mapping):
                rows[-1][1:3] = [2, code - start - 1]
                continue
            if count > 1 and code == start + count * (kind + 1) and (kind == 0 or code - 1 not in mapping):
                rows[-1][1] += 1
                continue
        rows.append([code, 1, 0, offset])
    assert all(count < 512 and code < 1 << 21 and (kind != 2 or count <= 3) for code, count, kind, _ in rows)
    return f'static const uint32_t {name}[] = {{\n' + ''.join(
        f'    0x{code << 11 | count << 2 | kind:x}, 0x{value:x},\n' for code, count, kind, value in rows) + '};\n'


def case_tables():
    """Full case mappings above ASCII; title case is stored where it differs
    from upper case and case folding where it differs from lower case."""
    mappings = {kind: {} for kind in ('lower', 'upper', 'title', 'casefold')}
    for code in range(128, 0x110000):
        char = chr(code)
        for kind, mapping in mappings.items():
            mapped = getattr(char, kind)()
            if mapped != char:
                mapping[code] = mapped

    def differences(mapping, base):
        return {code: mapping.get(code, chr(code)) for code in mapping.keys() | base.keys()
                if mapping.get(code, chr(code)) != base.get(code, chr(code))}

    data = []
    content = mapping_table('unicode_to_lower', mappings['lower'], data)
    content += mapping_table('unicode_to_upper', mappings['upper'], data)
    content += mapping_table('unicode_to_title', differences(mappings['title'], mappings['upper']), data)
    content += mapping_table('unicode_to_fold', differences(mappings['casefold'], mappings['lower']), data)
    return content + array('uint32_t', 'unicode_case_data', data, 12)


def normalization_tables():
    """Single-level canonical and compatibility decompositions as runs of
    start << 8 | count. A run's characters are UTF-8 from its offset to the
    next one; the first is advanced by the code point's position in the run.
    Hangul syllables are algorithmic. Compositions list the composite
    characters ordered by their canonical pair."""
    decompositions, compositions = {}, []
    for code in range(0x110000):
        if 0xac00 <= code < 0xd7a4:
            continue
        parts = unicodedata.decomposition(chr(code)).split()
        if not parts:
            continue
        if not parts[0].startswith('<') and len(parts) == 2 and unicodedata.normalize('NFC', chr(code)) == chr(code):
            compositions.append(code)
        decompositions[code] = [int(part, 16) for part in parts if not part.startswith('<')]
        assert len(decompositions[code]) <= 18
    rows, offsets, data = [], [], bytearray()
    for code, parts in sorted(decompositions.items()):
        if rows and len(parts) == 1 and rows[-1][0] + rows[-1][1] == code and rows[-1][1] < 255:
            first = decompositions[rows[-1][0]]
            if len(first) == 1 and first[0] - rows[-1][0] == parts[0] - code:
                rows[-1][1] += 1
                continue
        rows.append([code, 1])
        offsets.append(len(data))
        data += ''.join(map(chr, parts)).encode()
    offsets.append(len(data))
    assert len(data) < 1 << 16
    compositions.sort(key=lambda code: decompositions[code])
    combining, previous = [], 0
    for code in range(0x110000):
        order = unicodedata.combining(chr(code))
        if order != previous:
            combining.append(code << 8 | order)
            previous = order
    return (array('uint32_t', 'unicode_combining', combining, 12) +
            array('uint32_t', 'unicode_decompositions', [code << 8 | count for code, count in rows], 12) +
            array('uint16_t', 'unicode_decomposition_offsets', offsets) +
            array('uint8_t', 'unicode_decomposed', list(data), 32) +
            array('uint32_t', 'unicode_compositions', compositions, 12))


DERIVED_PREFIXES = ("HANGUL SYLLABLE ", "CJK UNIFIED IDEOGRAPH-", "TANGUT IDEOGRAPH-", "CJK COMPATIBILITY IDEOGRAPH-",
                    "EGYPTIAN HIEROGLYPH-", "KHITAN SMALL SCRIPT CHARACTER-", "NUSHU CHARACTER-")


def name_tables():
    """Character names and aliases for \\N{...}, as a word dictionary.

    Words are length-prefixed and numbered by frequency. Each record is the
    code point's delta from the previous record (LEB128), a byte holding the
    number of leading words shared with the previous record and the number
    of words that follow, and those words: ids below 128 take one byte,
    others two (0x80 | high, low)."""
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
    text = b''.join(bytes([len(word)]) + word.encode('ascii') for word in words)
    records, previous, before = bytearray(), 0, []
    for code, name in entries:
        delta = code - previous
        previous = code
        while True:
            records.append((delta & 127) | (128 if delta > 127 else 0))
            delta >>= 7
            if not delta:
                break
        current = name.split(' ')
        shared = 0
        while shared < min(len(current), len(before)) and current[shared] == before[shared]:
            shared += 1
        assert len(current) < 16
        records.append(shared << 4 | len(current) - shared)
        for word in current[shared:]:
            index = ids[word]
            records += bytes([index]) if index < 128 else bytes([128 | index >> 8, index & 255])
        before = current
    content = array('uint8_t', 'unicode_name_words', list(text), 32)
    content += array('uint8_t', 'unicode_names', list(records), 32)
    content += f'static const uint32_t unicode_derived_names[][3] = {{\n' + ''.join(
        f'    {{0x{start:x}, 0x{end:x}, {prefix}}},\n' for start, end, prefix in derived) + '};\n'
    return content, len(entries), len(words)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sys.version_info[:3] != (3, 15, 0) or unicodedata.unidata_version != "17.0.0":
        raise SystemExit("Use the pinned Python 3.15.0 oracle with Unicode 17.0.0")
    sigma_cased = lambda char: char.isupper() or char.islower() or unicodedata.category(char) == 'Lt'
    def case_ignorable(char):
        if sigma_cased(char):
            return ('AΣ' + char).lower()[1] == 'ς'
        return ('A' + char + 'Σ').lower()[-1] == 'ς'
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
    for name, predicate in [('printable', str.isprintable), ('identifier_start', str.isidentifier),
                            ('identifier_continue', lambda char: ('A' + char).isidentifier()),
                            ('alpha', str.isalpha), ('digit', str.isdigit), ('numeric', str.isnumeric),
                            ('space', str.isspace), ('upper', str.isupper), ('lower', str.islower),
                            ('titlecase', lambda char: unicodedata.category(char) == 'Lt'),
                            ('cased', sigma_cased), ('case_ignorable', case_ignorable)]:
        content += property_table(name, predicate)
    content += 'static const uint32_t unicode_decimal[][3] = {\n' + ''.join(
        f'    {{0x{start:x}, 0x{end:x}, {value}}},\n' for start, end, value in decimal_runs) + '};\n'
    content += case_tables()
    content += normalization_tables()
    names, name_count, word_count = name_tables()
    content += names
    path = ROOT / "spy-unicode.h"
    if args.check:
        if path.read_text() != content:
            raise SystemExit("spy-unicode.h is out of date")
    else:
        path.write_text(content)
    print(f'Unicode 17.0.0: {name_count} names in {word_count} words')


if __name__ == "__main__":
    main()
