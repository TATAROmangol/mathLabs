
#3.1 и 3.3

# Алгоритм:
#представляем многочл битовыми списками (старший коэф инд 0)
# кодируем
#строим образ. матр. путём кодирования единичных информ. векторов
#проверяем принятую комбинацию (деление на g)
#проверяем можно ли остаток получить одиноч. ошибкой (остаток== x^i)
#находим пары двухбитных ошибок с тем же остатком (для демонстрвции)

from typing import List,Tuple

def trim(poly: List[int])->List[int]:
    # убираем ведущие нули
    i = 0
    while i < len(poly) and poly[i]==0:
        i += 1
    return poly[i:] if i <len(poly) else [0]
def deg(poly: List[int])->int:
    p = trim(poly)
    if p == [0]:

        return -1
    return len(p)-1

def poly_xor(a: List[int], b: List[int]) -> List[int]:
    # a и b-старший бит первым; выравниваем по правому концу
    la, lb = len(a), len(b)
    if la < lb:
        a = [0]*(lb-la) + a
    elif lb < la:
        b = [0]*(la-lb) + b

    return [(ai ^ bi) for ai,bi in zip(a,b)]

def poly_div_mod(dividend: List[int], divisor: List[int]) -> Tuple[List[int], List[int]]:
    # возвращает (quotient, remainder), полиномы с старшим коэф первым
    A = dividend.copy()
    A = trim(A)
    B = trim(divisor)

    if B == [0]:
        raise ZeroDivisionError("Делитель нулевой многочл")
    n = len(A); m = len(B)
    if A == [0]:
        return [0], [0]
    Q = [0]*(max(0,n-m+1))

    R = A.copy()

    while len(R) >= len(B) and R != [0]:
        shift = len(R) - len(B)
        # множитель x^shift -> просто ставим 1 на позицию shift в частном
        Q[shift] = 1
        B_shifted = B + [0]*shift
        R = poly_xor(R, B_shifted)

        R = trim(R)
        if R == []:
            R = [0]

    if Q == []:
        Q = [0]
    if R == []:
        R = [0]

    return trim(Q),trim(R)

def bits_to_poly(bits: List[int]) -> List[int]:
    # bits: старший бит первый -> возвращаем полином в том же формате
    return trim(bits.copy())

def poly_to_bits(poly: List[int], length: int=None)-> List[int]:
    p = trim(poly)
    if length is None:
        return p
    #старший бит первый
    if len(p) < length:
        return [0]*(length - len(p)) + p
    return p[-length:]

# вар 4
g_bits = [1,0,1,0,1]  # образующий полином
u_bits = [0,1,0,1,1]   # инф часть

g = bits_to_poly(g_bits)
u = bits_to_poly(u_bits)
r = deg(g)  # число провероч разрядов
k = len(u_bits)
n = k + r

print("Параметры:")
print("  g (коэф старш->младш):", g)
print("  степ. g =", r, ", k =", k, ", n =", n)
print()

# 3.1) Формирование избыточного циклич. кода для ю
u_shifted = u + [0]*r
_, rem = poly_div_mod(u_shifted,g)
# кодовое слово
c_poly = poly_xor(u_shifted, poly_to_bits(rem, len(u_shifted)))
c_bits = poly_to_bits(c_poly, n)


print("Информац часть u:",u_bits)
print("u * x^r =", u_shifted)
print("Остаток rem (u*x^r / g):", rem)
print("Кодовое слово c (длина n):",c_bits)
print()

# 2) Построение образующей матрицы G
G = []
for i in range(k):
    e = [0]*k
    e[i] = 1
    e_shifted = e + [0]*r
    _, rem_e = poly_div_mod(e_shifted, g)
    c_e = poly_xor(e_shifted, poly_to_bits(rem_e, len(e_shifted)))
    G.append(poly_to_bits(c_e, n))
print("Образующая матрица G (k={} x n={}):".format(k,n))
for row in G:
    print(" ", row)
print()

# 3) Проверка комбинации из задания
_, rem_check = poly_div_mod(c_bits, g)
print("Проверка c /g -> остаток:", rem_check, "(должен быть 0)")
print()

#              3.3           4)одиноч ошибка
def single_error_vector(pos:int, n:int)->List[int]:
    v = [0]*n
    v[pos] = 1
    return v

# остаток для одиноч ошибки в позиции pos
def remainder_for_error_pos(pos:int)-> List[int]:
    e = single_error_vector(pos,n)
    _, rem_e = poly_div_mod(e,g)
    return poly_to_bits(rem_e, len(rem_e))

# Пример pos 2
pos_example = 2
c_err = c_bits.copy()
c_err[pos_example] ^= 1
_, rem_err = poly_div_mod(c_err, g)
print(f"Пример: ошибка в поз {pos_example}-> остаток:",rem_err)
# провер, равен ли остаток остатку одиночной ошибки в этой позиции:
rem_single = remainder_for_error_pos(pos_example)
print(" Остаток одиноч ошибки в той же позиции:", rem_single)
print(" Совпадают ли остатки?", rem_err == rem_single)
print()

# 5)соотв ли остаток какой-либо одиночной ошибке
def detect_single_error_from_remainder(rem: List[int]) -> int:
    for pos in range(n):
        reme = remainder_for_error_pos(pos)
        if trim(reme) == trim(rem):
            return pos

    return None

#для c_err выше
det_pos = detect_single_error_from_remainder(rem_err)
if det_pos is not None:
    print(f"Остаток может быть результатом одиночной ошибки в позиции {det_pos}")
else:
    print("Остаток НЕ соотв. ни одной одиночной ошибке (в пределах длины n).")
print()

# 6) Привести примеры двухкратных ошибок, дающих тот же остаток (перебор всех пар)
pairs_same_rem = []
target_rem = rem_err
for p1 in range(n):
    for p2 in range(p1+1, n):
        e = single_error_vector(p1, n)
        e2 = single_error_vector(p2, n)
        e12 = [ (a^b) for a,b in zip(e,e2) ]
        _, rem12 = poly_div_mod(e12, g)
        if trim(rem12) == trim(target_rem):
            pairs_same_rem.append((p1,p2))
            if len(pairs_same_rem) >= 6:
                break
    if len(pairs_same_rem) >= 6:
        break

print("Пары двухбитных ошибок (p1,p2), дающих тот же остаток (первые найденные):", pairs_same_rem)
if not pairs_same_rem:
    print(" пар двухбитных ошибок с тем же остатком нет")
