#include <stddef.h>
#include <stdint.h>

void match_c(const double *a, size_t n, const double *b, size_t m,
             int64_t *out)
{
    if (n == 0)
        return;

    size_t j = 0;
    double cur_b = *b;
    b++;
    size_t remaining = m - 1;

    while (n--) {
        double cur_a = *a;
        a++;

        while (remaining) {
            double next_b = *b;
            if (next_b - cur_a >= cur_a - cur_b)
                break;

            j++;
            b++;
            cur_b = next_b;
            remaining--;
        }

        *out = j;
        out++;
    }
}
