import random
import pandas as pd

def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))

def find_code(n, M=18, d=5, attempts=2000):
    all_vecs = [tuple(map(int, format(i, f'0{n}b'))) for i in range(2**n)]
    for _ in range(attempts):
        code = []
        for v in random.sample(all_vecs, len(all_vecs)):
            if all(hamming(v, c) >= d for c in code):
                code.append(v)
                if len(code) >= M:
                    return code
    return None

# Поиск кода
for n in range(10, 16):
    if codebook := find_code(n, attempts=3000):
        found_n = n
        break
else:
    raise RuntimeError("ош")

# Кодирование/декодирование
encode_msg = lambda m: list(codebook[m])
decode_word = lambda word: min(enumerate(codebook), key=lambda x: hamming(word, x[1]))

# Тестирование ошибок
single_fails, double_fails = [], []
for m in range(18):
    c = encode_msg(m)
    
    # Одиночные ошибки
    for i in range(found_n):
        err, idx = c.copy(), decode_word(tuple(c[:i] + [1-c[i]] + c[i+1:]))[0]
        if idx != m: single_fails.append((m, i, idx))
    
    # Двойные ошибки  
    for i in range(found_n):
        for j in range(i+1, found_n):
            err = c.copy()
            err[i] ^= 1; err[j] ^= 1
            if decode_word(err)[0] != m: double_fails.append((m, (i,j)))

# Вывод результатов
df = pd.DataFrame({'message': range(18), 'codeword': [''.join(map(str, c)) for c in codebook]})
min_dist = min(hamming(codebook[i], codebook[j]) for i in range(18) for j in range(i+1, 18))

print("КОДОВАЯ ТАБЛИЦА")
print(df.to_string(index=False))
print(f"\nСВОДКА: n={found_n}, M=18, d≥5")
print(f"Ошибки: одинарные {len(single_fails)}, двойные {len(double_fails)}")
print(f"Реальное d: {min_dist}")