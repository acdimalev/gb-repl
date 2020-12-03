Game Boy REPL
-------------

This is a toy interpreter.

It is:
  - inefficient
  - missing op codes
  - lacking support for either labels or expressions

That said, it's actually been pretty handy for building intuition around the
Game Boy DMG variant of the Z80.

Syntax is roughly based on RGBDS and mGBA (my current development environment).

    $ gb-repl
    > ; load example values
    >   ld sp, $c004
    >   ld bc, $1234
    >   push bc
    >   ld bc, $4321
    >   push bc
    > ; accumulate
    >   ld sp, $c002
    >   pop bc
    >   ld sp, $c000
    >   pop hl
    >   add hl, bc
    >   push hl
    > ; print results
    >   x/2 $c002, 2
    $c002: 1234 0000
    >
