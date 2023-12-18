**What it does**

`hexer.py` lets you practice doing arithmetic operations without a calculator.

It does not teach you how to do arithmetic, it just lets you practice and drill.

It is a command-line Python script that runs in a terminal. There is no graphical user interface.

`hexer.py` generates a random pair of numbers to be multiplied, added, subtracted, or divided, and then awaits your input. You can type in the answer that you calculated or guessed, or simply hit Enter. You'll see if your answer was right, and then a new pair of numbers appears and again awaits your input. The program loops indefinitely until you interrupt it with Ctrl-C.

**Functionality**

By default, the program does multiplication, but you can specify one of the other three arithmetic operations.

By default, the program uses 1-digit numbers, but you can specify any length.

By default, the program uses regular base-10 numbers, but you can specify hexadecimal (base 16), binary (base 2), quaternary (base 4), or octal (base 8).

By default, the digits 0 and 1 are usually excluded when generating the random pairs of numbers, because adding or multiplying by 0 or 1 is trivial. But they aren't excluded for subtraction (because a calculation like 11−6 is not purely trivial). However you can specify that 0 and 1 should be allowed. Or conversely, you can disallow other digits as well.

By default, all arithmetic operations involve only a pair of random numbers. But for addition alone you can instead specify that three or more numbers should be added together.

You can optionally type in the digits of an answer in reverse order (because that's the order in which they're calculated). This is done by appending a comma. For example, `654321,` is interpreted as the number `123456`

If you are using a lengthy set of options (for instance, complicated rules for which digits are allowed to pair off against which other digits), you can store it with a simple name in a file called `hexer_menu.json` (a sample version of this file is included, which can modify any way you want).

**Quick start**

You need Python version 3.6 or higher.

Most Linux distributions already have Python installed. You can `cd` (change directory) to the directory where `hexer.py` is installed, and run the program via
`./hexer.py`

On Windows, you can download Windows Terminal and Python for free from the Microsoft Store, and run the program via
`python ./hexer.py`

Various command line options are available, and you can get standard argparse-style help via:

`./hexer.py --help` (on Linux)

`python ./hexer.py --help` (on Windows)

**Some sample sessions**

First we run it with no command-line options to drill the traditional times-table (multiplication of one-digit base-10 numbers).

```
python ./hexer.py
        5
    ×   8
40
        4
    ×   3

       ══
       12

        9
    ×   4
46
       ══
       36

        7
    ×   3
```

In the above:
* 5 × 8 = 40, and we answered correctly
* 4 × 3 = 12, and we didn't calculate or guess the answer but simply hit Enter
* 9 × 4 = 36, but we incorrectly entered `46` so the program provided the correct answer
* 7 × 3 would equal 21, but we interrupted the program (usually done by simultaneously pressing the Ctrl key and C)

---

Next we use `-x` for hexadecimal, and `-l 3` (lowercase L) to specify 3-digit numbers, and `-o +` to specify addition.

```
python ./hexer.py -x -l 3 -o +
          9d3
      +   2a9  ₕₑₓ

          ═══
          c7c

          bdd
      +   fc8  ₕₑₓ
5ba1,
```

In the above:
* 9d3 + 2a9 = c7c, and we simply hit Enter to get that answer
* bdd + fc8 = 1ba5, and we answered correctly (entered as `5ba1,` with comma appended to indicate digits entered in reverse order)
* Note that a little subscript "hex" appears each time as a reminder

---

Finally we return to base 10, and use `-o /` to specify division.

* The program always provides numbers that divide evenly with no remainder

```
python ./hexer.py -o /
       10
    ÷   2
5
       72
    ÷   9
8
```
