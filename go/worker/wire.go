package worker

// Values and messages of the worker protocol (docs/packaging/protocol.md).
// Encoding trusts the parent's values; decoding trusts nothing and returns a
// violation for any message that breaks the protocol.

import (
	"encoding/binary"
	"fmt"
	"maps"
	"math"
	"math/big"
	"slices"
	"strings"
	"unicode/utf8"
)

const maxDepth = 200

const (
	msgInit    = 0x01
	msgEval    = 0x02
	msgExec    = 0x03
	msgCall    = 0x04
	msgGet     = 0x05
	msgSet     = 0x06
	msgDelete  = 0x07
	msgModule  = 0x08
	msgMount   = 0x09
	msgCollect = 0x0a
	msgOp      = 0x0b
	msgRelease = 0x0c
	msgHost    = 0x21
	msgLoad    = 0x22
	msgOutput  = 0x23
	msgResult  = 0x40
	msgRaise   = 0x41
)

// message frames a message of kind with fields, whose objects and functions
// must belong to the runtime of s.
func message(kind byte, s *shared, fields ...any) ([]byte, error) {
	out := []byte{0, 0, 0, 0, kind}
	var err error
	for _, field := range fields {
		if out, err = encode(out, field, s, 0); err != nil {
			return nil, err
		}
	}
	if len(out)-4 > math.MaxUint32 {
		return nil, invalid("message exceeds the limit")
	}
	binary.LittleEndian.PutUint32(out, uint32(len(out)-4))
	return out, nil
}

func encode(out []byte, x any, s *shared, depth int) ([]byte, error) {
	if depth > maxDepth {
		return nil, Raise("RecursionError", "value is too deeply nested to convert")
	}
	items := func(tag byte, items []any) ([]byte, error) {
		out = binary.LittleEndian.AppendUint32(append(out, tag), uint32(len(items)))
		var err error
		for _, item := range items {
			if out, err = encode(out, item, s, depth+1); err != nil {
				return nil, err
			}
		}
		return out, nil
	}
	pairs := func(dict Dict) ([]byte, error) {
		out = binary.LittleEndian.AppendUint32(append(out, 'd'), uint32(len(dict)))
		var err error
		for _, item := range dict {
			if out, err = encode(out, item.Key, s, depth+1); err != nil {
				return nil, err
			}
			if out, err = encode(out, item.Value, s, depth+1); err != nil {
				return nil, err
			}
		}
		return out, nil
	}
	switch x := x.(type) {
	case nil:
		return append(out, 'N'), nil
	case bool:
		if x {
			return append(out, 'T'), nil
		}
		return append(out, 'F'), nil
	case int:
		return integer(out, int64(x)), nil
	case int8:
		return integer(out, int64(x)), nil
	case int16:
		return integer(out, int64(x)), nil
	case int32:
		return integer(out, int64(x)), nil
	case int64:
		return integer(out, x), nil
	case uint:
		return unsigned(out, uint64(x)), nil
	case uint8:
		return integer(out, int64(x)), nil
	case uint16:
		return integer(out, int64(x)), nil
	case uint32:
		return integer(out, int64(x)), nil
	case uint64:
		return unsigned(out, x), nil
	case *big.Int:
		if x.IsInt64() {
			return integer(out, x.Int64()), nil
		}
		text := "0x" + new(big.Int).Abs(x).Text(16)
		if x.Sign() < 0 {
			text = "-" + text
		}
		return field(out, 'I', []byte(text)), nil
	case float32:
		return binary.LittleEndian.AppendUint64(append(out, 'f'), math.Float64bits(float64(x))), nil
	case float64:
		return binary.LittleEndian.AppendUint64(append(out, 'f'), math.Float64bits(x)), nil
	case complex64:
		return encode(out, complex128(x), s, depth)
	case complex128:
		out = binary.LittleEndian.AppendUint64(append(out, 'c'), math.Float64bits(real(x)))
		return binary.LittleEndian.AppendUint64(out, math.Float64bits(imag(x))), nil
	case string:
		if !surrogatepass(x) {
			return nil, Raise("UnicodeEncodeError", "the string is not UTF-8")
		}
		return field(out, 's', []byte(x)), nil
	case []byte:
		return field(out, 'b', x), nil
	case ByteArray:
		return field(out, 'B', x), nil
	case []any:
		return items('l', x)
	case Tuple:
		return items('t', x)
	case Set:
		return items('S', x)
	case FrozenSet:
		return items('z', x)
	case Dict:
		return pairs(x)
	case map[string]any:
		dict := make(Dict, 0, len(x))
		for _, key := range slices.Sorted(maps.Keys(x)) {
			dict = append(dict, Item{key, x[key]})
		}
		return pairs(dict)
	case *Object:
		if x.shared != s {
			return nil, invalid("the value belongs to another runtime")
		}
		return binary.LittleEndian.AppendUint64(append(out, 'h'), x.id), nil
	case *Function:
		if x.shared != s {
			return nil, invalid("the value belongs to another runtime")
		}
		out = binary.LittleEndian.AppendUint64(append(out, 'p'), x.id)
		return encode(out, x.name, s, depth)
	}
	return nil, Raise("TypeError", fmt.Sprintf("cannot convert %T to a Python value", x))
}

func integer(out []byte, n int64) []byte {
	return binary.LittleEndian.AppendUint64(append(out, 'i'), uint64(n))
}

func unsigned(out []byte, n uint64) []byte {
	if n > math.MaxInt64 {
		return field(out, 'I', []byte(fmt.Sprintf("%#x", n)))
	}
	return integer(out, int64(n))
}

func field(out []byte, tag byte, data []byte) []byte {
	out = binary.LittleEndian.AppendUint32(append(out, tag), uint32(len(data)))
	return append(out, data...)
}

// A decoder decodes the values of one message (without its length), after
// the kind.
type decoder struct {
	data   []byte
	at     int
	shared *shared
}

// A violation is what the worker broke.
type violation string

func (v violation) Error() string { return string(v) }

// decode decodes exactly n values, which must use up message.
func decode(message []byte, s *shared, n int) ([]any, error) {
	r := &decoder{message, 1, s}
	values := make([]any, n)
	for i := range values {
		var err error
		if values[i], err = r.value(0); err != nil {
			return nil, err
		}
	}
	if r.at != len(r.data) {
		return nil, violation("trailing bytes in message")
	}
	return values, nil
}

func (r *decoder) take(n int) ([]byte, error) {
	if n > len(r.data)-r.at {
		return nil, violation("truncated message")
	}
	r.at += n
	return r.data[r.at-n : r.at], nil
}

func (r *decoder) u64() (uint64, error) {
	b, err := r.take(8)
	if err != nil {
		return 0, err
	}
	return binary.LittleEndian.Uint64(b), nil
}

// count reads a count of items at least minimum bytes long each.
func (r *decoder) count(minimum int) (int, error) {
	b, err := r.take(4)
	if err != nil {
		return 0, err
	}
	n := int(binary.LittleEndian.Uint32(b))
	if uint64(n)*uint64(minimum) > uint64(len(r.data)-r.at) {
		return 0, violation("count exceeds the message")
	}
	return n, nil
}

func (r *decoder) bytes() ([]byte, error) {
	n, err := r.count(1)
	if err != nil {
		return nil, err
	}
	return r.take(n)
}

func (r *decoder) value(depth int) (any, error) {
	if depth > maxDepth {
		return nil, violation("value nested too deeply")
	}
	b, err := r.take(1)
	if err != nil {
		return nil, err
	}
	switch tag := b[0]; tag {
	case 'N':
		return nil, nil
	case 'F', 'T':
		return tag == 'T', nil
	case 'i':
		n, err := r.u64()
		return int64(n), err
	case 'I':
		return r.big()
	case 'f':
		x, err := r.u64()
		return math.Float64frombits(x), err
	case 'c':
		re, err := r.u64()
		if err != nil {
			return nil, err
		}
		im, err := r.u64()
		return complex(math.Float64frombits(re), math.Float64frombits(im)), err
	case 's':
		text, err := r.bytes()
		if err != nil {
			return nil, err
		}
		if !surrogatepass(string(text)) {
			return nil, violation("invalid UTF-8")
		}
		return string(text), nil
	case 'b', 'B':
		data, err := r.bytes()
		if tag == 'b' {
			return slices.Clone(data), err
		}
		return ByteArray(slices.Clone(data)), err
	case 'l', 't', 'S', 'z':
		n, err := r.count(1)
		if err != nil {
			return nil, err
		}
		items := make([]any, n)
		for i := range items {
			if items[i], err = r.value(depth + 1); err != nil {
				return nil, err
			}
		}
		switch tag {
		case 't':
			return Tuple(items), nil
		case 'S':
			return Set(items), nil
		case 'z':
			return FrozenSet(items), nil
		}
		return items, nil
	case 'd':
		n, err := r.count(2)
		if err != nil {
			return nil, err
		}
		dict := make(Dict, n)
		for i := range dict {
			if dict[i].Key, err = r.value(depth + 1); err != nil {
				return nil, err
			}
			if dict[i].Value, err = r.value(depth + 1); err != nil {
				return nil, err
			}
		}
		return dict, nil
	case 'h':
		id, err := r.u64()
		if err != nil {
			return nil, err
		}
		return newObject(id, r.shared), nil
	default:
		return nil, violation(fmt.Sprintf("unknown value tag %#x", tag))
	}
}

// big reads an int beyond 64 bits, which must be in canonical form.
func (r *decoder) big() (any, error) {
	b, err := r.bytes()
	if err != nil {
		return nil, err
	}
	text := string(b)
	digits, ok := strings.CutPrefix(strings.TrimPrefix(text, "-"), "0x")
	if !ok || digits == "" || digits[0] == '0' || strings.Trim(digits, "0123456789abcdef") != "" {
		return nil, violation("invalid integer")
	}
	n, _ := new(big.Int).SetString(text, 0)
	if n.IsInt64() {
		return nil, violation("integer should have been sent as 'i'")
	}
	return n, nil
}

// surrogatepass reports whether s is UTF-8 in which lone surrogates may
// appear as their three-byte forms (CPython's surrogatepass).
func surrogatepass(s string) bool {
	for i := 0; i < len(s); {
		r, n := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError && n == 1 {
			if len(s)-i < 3 || s[i] != 0xed || s[i+1] < 0xa0 || s[i+1] > 0xbf || s[i+2] < 0x80 || s[i+2] > 0xbf {
				return false
			}
			n = 3
		}
		i += n
	}
	return true
}
