package main

import (
	"errors"
)

// Поле Галуа
const primPoly = 0x11D

var (
	gfExp [256]byte
	gfLog [256]byte
)

func Init() {
	x := 1
	for i := 0; i < 255; i++ {
		gfExp[i] = byte(x)
		gfLog[x] = byte(i)
		x <<= 1
		if x&256 != 0 {
			x ^= primPoly
		}
	}
	gfExp[255] = gfExp[0]
}

func gfMul(a, b byte) byte {
	if a == 0 || b == 0 {
		return 0
	}
	return gfExp[(int(gfLog[a])+int(gfLog[b]))%255]
}

func gfDiv(a, b byte) byte {
	if a == 0 {
		return 0
	}
	if b == 0 {
		panic("divide by zero")
	}
	return gfExp[(int(gfLog[a])-int(gfLog[b])+255)%255]
}

// Операции с полиномами
func stripLead(a []byte) []byte {
	for len(a) > 1 && a[0] == 0 {
		a = a[1:]
	}
	return a
}

func polyMul(a, b []byte) []byte {
	r := make([]byte, len(a)+len(b)-1)
	for i := range a {
		for j := range b {
			r[i+j] ^= gfMul(a[i], b[j])
		}
	}
	return stripLead(r)
}

func polyDiv(dividend, divisor []byte) []byte {
	out := append([]byte{}, dividend...)
	normalizer := divisor[0]

	for i := 0; i < len(out)-len(divisor)+1; i++ {
		coef := out[i]
		if coef != 0 {
			factor := gfDiv(coef, normalizer)
			for j := 0; j < len(divisor); j++ {
				out[i+j] ^= gfMul(divisor[j], factor)
			}
		}
	}
	remainder := out[len(out)-len(divisor)+1:]
	if len(remainder) == 0 {
		return []byte{0}
	}
	return stripLead(remainder)
}

func polyEval(poly []byte, x byte) byte {
	result := poly[0]
	for i := 1; i < len(poly); i++ {
		result = gfMul(result, x) ^ poly[i]
	}
	return result
}

// --- Генерация порождающего полинома ---
func GPoly(nsym int) []byte {
	g := []byte{1}
	for i := 0; i < nsym; i++ {
		g = polyMul(g, []byte{1, gfExp[i]})
	}
	return g
}

// --- Кодирование ---
func Encode(data []byte, nsym int) []byte {
	g := GPoly(nsym)
	msgPadded := append(data, make([]byte, nsym)...)
	remainder := polyDiv(msgPadded, g)
	encoded := append(data, remainder...)
	return encoded
}

func Syndromes(encoded []byte, nsym int) []byte {
	syndromes := make([]byte, nsym)
	for i := 0; i < nsym; i++ {
		alpha := gfExp[i]
		syndromes[i] = polyEval(encoded, alpha)
	}

	return syndromes
}

// --- Декодирование с исправлением ошибок ---
func isValid(encoded []byte, nsym int) bool {
	for i := 0; i < nsym; i++ {
		alpha := gfExp[i]
		if polyEval(encoded, alpha) != 0 {
			return false
		}
	}
	return true
}

func Decode(encoded []byte, nsym int) ([]byte, error) {
	if len(encoded) <= nsym {
		return nil, errors.New("данные слишком короткие для декодирования")
	}

	dataLen := len(encoded) - nsym
	data := encoded[:dataLen]

	// 1. Вычисляем синдромы
	syndromes := Syndromes(encoded, nsym)

	// 2. Проверяем, есть ли ошибки
	allZero := true
	for _, s := range syndromes {
		if s != 0 {
			allZero = false
			break
		}
	}
	if allZero {
		return data, nil
	}

	maxErr := nsym / 2
	if maxErr == 0 {
		return nil, errors.New("недостаточно символов для исправления ошибок")
	}

	if maxErr >= 1 {
		for pos := 0; pos < len(encoded); pos++ {
			for errVal := byte(1); errVal != 0; errVal++ {
				fixed := append([]byte{}, encoded...)
				fixed[pos] ^= errVal

				valid := true
				for i := 0; i < nsym; i++ {
					alpha := gfExp[i]
					if polyEval(fixed, alpha) != 0 {
						valid = false
						break
					}
				}
				if valid {
					return fixed[:dataLen], nil
				}
			}
		}
	}

	if maxErr >= 2 {
		for pos1 := 0; pos1 < len(encoded); pos1++ {
			for pos2 := pos1 + 1; pos2 < len(encoded); pos2++ {
				for err1 := byte(1); err1 != 0; err1++ {
					for err2 := byte(1); err2 != 0; err2++ {
						fixed := append([]byte{}, encoded...)
						fixed[pos1] ^= err1
						fixed[pos2] ^= err2

						valid := true
						for i := 0; i < nsym; i++ {
							alpha := gfExp[i]
							if polyEval(fixed, alpha) != 0 {
								valid = false
								break
							}
						}
						if valid {
							return fixed[:dataLen], nil
						}
					}
				}
			}
		}
	}

	return nil, errors.New("ошибки слишком велики для исправления")
}
