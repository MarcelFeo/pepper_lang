import "math.pep";

fun main(): int {

    let a$int -> 0;

    for (let i$int = 0; i < 10, i -> i + 1) {
        if (i == 2) {
            printf("i + 5 = %i\n", add(i, 8));
        }

        if (i == 5) { break; }

        printf("i = %i\n", i);

        a -> i;

    }

    return a;

}
