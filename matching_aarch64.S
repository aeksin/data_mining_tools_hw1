#ifdef __APPLE__
#define MATCH_ASM _match_asm
#else
#define MATCH_ASM match_asm
#endif


/*
x0=ts1
x1 = ts1.size
x2 = ts2
x3 = ts2.size
x4 = res
*/
.text
.globl MATCH_ASM
.p2align 4
MATCH_ASM:
    cbz x1, return
    mov x5, #0 // j
    ldr d0, [x2], #8 // cur_b
    sub x8, x3, #1 // b_end
loop1:
    ldr d1, [x0], 8 // cur_a
    cbz x8, break
loop2:
    ldr d2, [x2]
    fsub d3, d2, d1
    fsub d4, d1, d0
    fcmp d3, d4
    b.ge break
    add x5, x5, #1
    add x2, x2, #8
    fmov d0, d2
    subs x8, x8, #1
    b.ne loop2
break:
    str x5, [x4], #8
    subs x1, x1, #1
    b.ne loop1
return:
    ret