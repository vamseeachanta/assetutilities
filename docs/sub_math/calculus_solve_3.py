# Third party imports
import sympy as sp

N_L = 4.493
E = 30 * 10**6
I = 20.19
m1 = 1

x = sp.Symbol("x")

array_size = 101
L_b_max = 100
L_b_array = [item / (array_size - 1) * L_b_max for item in list(range(0, 1001))]
n_1 = [sp.sqrt(20.19) / item if item > 0 else 1000 for item in L_b_array]
n_1[0] = n_1[1]
N = [N_L**2 * E * I / item**2 if item > 0 else 1e10 for item in L_b_array]
N[0] = N[1]

m1 = 4.761e-8 / 3000

zipped_array = list(zip(L_b_array, n_1, N))
i_C_x = [
    m1
    / z[1] ** 4
    * (
        -sp.cos(z[1] * x) / sp.cos(z[1] * z[0])
        - z[1] ** 2 * x**2 / 2
        + z[1] ** 2 * z[0] ** 2 / 2
        + 1
    )
    for z in zipped_array
]

C_x = [sp.diff(item, x) for item in i_C_x]

zipped_array = list(zip(L_b_array, C_x))
B = [sp.sqrt(sp.integrate(item[1] ** 2, (x, 0, item[0]))) for item in zipped_array]

pass
