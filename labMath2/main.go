package main

import (
	"fmt"
	"os"
)

const (
	marker byte = 1
)

func addByte(b byte, cnt int, res []byte) []byte {
	n := cnt / 255
	for j := 0; j < n; j++ {
		res = append(res, b)
		res = append(res, marker)
		res = append(res, 255)
	}

	next := cnt % 255
	if next <= 3 && b != marker {
		for i := 0; i < next; i++ {
			res = append(res, b)
		}
		return res
	}

	res = append(res, b)
	res = append(res, marker)
	res = append(res, byte(cnt))

	return res
}

func RLEEncode(data []byte) []byte {
	if len(data) == 0 {
		return nil
	}

	res := make([]byte, 0)

	cnt := 1
	cur := data[0]

	for i := 1; i < len(data); i++ {
		if data[i] == cur {
			cnt++
			continue
		}

		res = addByte(cur, cnt, res)

		cur = data[i]
		cnt = 1
	}

	res = addByte(cur, cnt, res)
	return res
}

func RLEDecode(data []byte) []byte {
	if len(data) == 0 {
		return nil
	}

	res := make([]byte, 0)

	i := 0
	for i < len(data)-2 {
		b := data[i]
		if b != marker && (data[i+1] != marker || (data[i+1] == marker && data[i+2] == marker)) {
			res = append(res, b)
			i++
			continue
		}

		cnt := int(data[i+2])
		for j := 0; j < cnt; j++ {
			res = append(res, b)
		}
		i += 3

	}

	if i < len(data) {
		res = append(res, data[i:]...)
	}

	return res
}

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Использование:")
		fmt.Println("  rle -c input output    # сжать файл")
		fmt.Println("  rle -d input output   # распаковать файл")
		return
	}

	mode := os.Args[1]
	inputFile := os.Args[2]
	outputFile := os.Args[3]

	data, err := os.ReadFile(inputFile)
	if err != nil {
		fmt.Println("Ошибка чтения файла:", err)
		return
	}

	var result []byte

	switch mode {
	case "-c":
		result = RLEEncode(data)
	case "-d":
		result = RLEDecode(data)
	default:
		fmt.Println("Неизвестный режим:", mode)
		return
	}

	if err := os.WriteFile(outputFile, result, 0644); err != nil {
		fmt.Println("Ошибка записи файла:", err)
		return
	}

	fmt.Printf("Успешно! %s → %s (%d байт → %d байт)\n",
		inputFile, outputFile, len(data), len(result))
	fmt.Println("Входные данные:", data)
	fmt.Println("Результат:", result)
}
