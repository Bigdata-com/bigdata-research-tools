from functools import lru_cache

def levenshtein_distance(a: str, b: str) -> int:
    @lru_cache(maxsize=None)
    def dist(i: int, j: int) -> int:
        if i == 0: return j
        if j == 0: return i

        if a[i-1] == b[j-1]:
            return dist(i-1, j-1)
        return min(
            dist(i-1, j) + 1,   # delete a char from string 1
            dist(i, j-1) + 1,   # insert a char into string 1
            dist(i-1, j-1) + 1  # substitute a char in string 1 from a char in string 2
        )
    return dist(len(a), len(b))