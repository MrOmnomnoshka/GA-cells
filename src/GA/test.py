import timeit

t = timeit.Timer('min(a, b), max(a, b)', setup='a = 10; b = 8')
print(sum(t.repeat(10)), "minmax")

t = timeit.Timer('if a > b: a, b = b, a', setup='a = 10; b = 8')
print(sum(t.repeat(10)), "hand")
