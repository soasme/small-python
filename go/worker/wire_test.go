package worker

import (
	"encoding/binary"
	"testing"
)

func TestSurrogatesPassAndOverlongFormsDoNot(t *testing.T) {
	for text, want := range map[string]bool{"a\xed\xb2\x80b": true, "�": true, "\xc0\x80": false, "\xed\xa0": false} {
		if surrogatepass(text) != want {
			t.Errorf("%q", text)
		}
	}
}

func TestBigIntegersAreCanonical(t *testing.T) {
	s := &shared{}
	decodeBig := func(text string) (any, error) {
		data := binary.LittleEndian.AppendUint32([]byte{msgResult, 'I'}, uint32(len(text)))
		values, err := decode(append(data, text...), s, 1)
		if err != nil {
			return nil, err
		}
		return values[0], nil
	}
	for _, good := range []string{"0x8000000000000000", "-0x8000000000000001"} {
		if _, err := decodeBig(good); err != nil {
			t.Errorf("%s: %v", good, err)
		}
	}
	for _, bad := range []string{"0x7fffffffffffffff", "-0x8000000000000000", "0x0", "-0x0", "0x01", "0xABC", "12", "0x", "--0x1"} {
		if _, err := decodeBig(bad); err == nil {
			t.Errorf("%s decoded", bad)
		}
	}
}
