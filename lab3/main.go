package main

import (
	"fmt"
)

func main() {
	Init()
	data := []byte{1, 2, 3, 4, 5, 6}
	nsym := 4

	encoded := Encode(data, nsym)
	fmt.Println("Encoded:", encoded)

	// портим два символа
	encoded[2] ^= 77
	encoded[5] ^= 99

	decoded, err := Decode(encoded, nsym)
	fmt.Println("Decoded:", decoded, "err:", err)
}
