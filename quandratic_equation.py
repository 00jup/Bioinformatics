# 이차 방정식 근 계산 프로그램
# ax^2 + bx + c = 0의 근을 구합니다

import math

# 계수 입력받기
a = float(input("a 값을 입력하세요: "))
b = float(input("b 값을 입력하세요: "))
c = float(input("c 값을 입력하세요: "))

# 판별식 계산
D = b**2 - 4*a*c

if D > 0:
    # 두 실근
    x1 = (-b + math.sqrt(D)) / (2*a)
    x2 = (-b - math.sqrt(D)) / (2*a)
    print(f"두 실근: x1 = {x1}, x2 = {x2}")
elif D == 0:
    # 중근
    x = -b / (2*a)
    print(f"중근: x = {x}")
else:
    # 복소근
    real = -b / (2*a)
    imag = math.sqrt(-D) / (2*a)
    print(f"복소근: x1 = {real} + {imag}i, x2 = {real} - {imag}i")