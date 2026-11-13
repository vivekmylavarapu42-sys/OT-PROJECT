"""Hungarian algorithm: min-cost perfect assignment on a square matrix, O(n^3)."""
import math


def hungarian(a):
    n = len(a)
    u = [0] * (n + 1); v = [0] * (n + 1); p = [0] * (n + 1); way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i; j0 = 0; minv = [math.inf] * (n + 1); used = [False] * (n + 1)
        while True:
            used[j0] = True; i0 = p[j0]; d = math.inf; j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    c = a[i0 - 1][j - 1] - u[i0] - v[j]
                    if c < minv[j]:
                        minv[j] = c; way[j] = j0
                    if minv[j] < d:
                        d = minv[j]; j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += d; v[j] -= d
                else:
                    minv[j] -= d
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
    return [(p[j] - 1, j - 1) for j in range(1, n + 1) if p[j]]
