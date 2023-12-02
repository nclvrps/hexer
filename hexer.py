#! /usr/bin/python3

import sys
import os
import argparse
import random
import itertools
import operator
import functools
import re
import math
import json
import shlex
from typing import FrozenSet, Sequence, Callable

# Importing readline lets arrow keys etc. work in the input line
# Usually not available on Windows
# pylint: disable-next=unused-import
try:
    import readline
except ModuleNotFoundError:
    pass

base_opts = None
menu = None
menu_filename = "hexer_menu.json"
set_of_all_digits = None

def build_integer_from_list(digits: Sequence) -> int:
    digit_string = "".join(digits).lstrip("0")
    # when stripping leading zeros, don't reduce 0 itself to an empty string
    if digit_string == "":
        digit_string = "0"
    return int(digit_string, base_opts.base)


def digit_set(digits: str) -> FrozenSet:
    set_of_digits = frozenset(digits.lower())
    if set_of_digits.issubset(set_of_all_digits):
        return set_of_digits

    msg = f"invalid digit string for base {base_opts.base}: '{digits}'"
    raise argparse.ArgumentTypeError(msg)


# all operators other than add, sub, mul, floordiv
non_arithmetic_operators = [operator.add,
       operator.abs, operator.and_, operator.attrgetter,
       operator.concat, operator.contains, operator.countOf,
       operator.delitem, operator.eq, operator.ge, operator.getitem, operator.gt, operator.iadd, operator.iand,
       operator.iconcat, operator.ifloordiv, operator.ilshift, operator.imatmul, operator.imod, operator.imul,
       operator.index, operator.indexOf, operator.inv, operator.invert, operator.ior, operator.ipow, operator.irshift,
       operator.is_, operator.is_not, operator.isub, operator.itemgetter, operator.itruediv, operator.ixor, operator.le,
       operator.length_hint, operator.lshift, operator.lt, operator.matmul, operator.methodcaller, operator.mod,
       operator.ne, operator.neg, operator.not_, operator.or_, operator.pos, operator.pow, operator.rshift,
       operator.setitem, operator.truediv, operator.truth, operator.xor]

def arithmetic_operation(op_str: str) -> Callable:
    if op_str in ('*', '.', '×', 'x'):
        return operator.mul
    # Kludge for allowing more than 2 operands in case of addition, see below
    #elif op_str == '+':
    #    return operator.add
    elif op_str in ('-', '\u2212'):
        return operator.sub
    elif op_str in ('/', '÷'):
        return operator.floordiv
    # Allow +, ++, +++ for multiple operands for addition only
    # This is a kludge: will be converted to operator.add elsewhere in this program
    elif op_str.strip('+') == '':
        if len(op_str) - 1 < len(non_arithmetic_operators):
            return non_arithmetic_operators[len(op_str) - 1]
        else:
            msg = f"number of + exceeds maximum of {len(non_arithmetic_operators)}: '{op_str}'"
            raise argparse.ArgumentTypeError(msg)

    msg = f"invalid operation: '{op_str}'"
    raise argparse.ArgumentTypeError(msg)


table = str.maketrans({ "0":"00", "1":"01", "2":"02", "3":"03",
                        "4":"10", "5":"11", "6":"12", "7":"13",
                        "8":"20", "9":"21", "a":"22", "b":"23",
                        "c":"30", "d":"31", "e":"32", "f":"33" })

def hex_no0x(num: int) -> str:
    """
    Convert an integer into a hex (or some other bases) string, only without the "0x" prefix

    Also handles negative numbers, e.g. -452 becomes -1C4 instead of -0x1C4
    """

    if base_opts.base == 16:
        digitstr = f'{num:x}'
    elif base_opts.base == 10:
        digitstr = f'{num:d}'
    elif base_opts.base == 8:
        digitstr = f'{num:o}'
    elif base_opts.base == 4:
        digitstr = f'{num:x}'.translate(table).lstrip('0')
        if digitstr == "":
            digitstr = '0'
    elif base_opts.base == 2:
        digitstr = f'{num:b}'

    return digitstr


def pattern_stuff(stuff: str) -> Sequence:
    anything = re.compile('.*')

    patterns = [anything for i in range(base_opts.base)]

    for b in stuff.lower().split(','):
        a = b.split(':')
        a1offset = 1 if a[1].startswith('^') else 0
        if len(a) != 2 or \
                        len(a[0]) == 0 or \
                        len(a[1][a1offset:]) == 0 or \
                        not frozenset(a[0]).issubset(set_of_all_digits) or \
                        not frozenset(a[1][a1offset:]).issubset(set_of_all_digits):
            msg = f"invalid pattern specification: '{b}'"
            raise argparse.ArgumentTypeError(msg)

        pattern = re.compile('[' + a[1].lower() + ']*')

        for d in a[0]:
            i = int(d, base_opts.base)
            patterns[i] = pattern

    return patterns


def do_the_parser(args):
    global base_opts
    base_opts, leftover = base_parser.parse_known_args(args)

    global menu
    try:
        with open(menu_filename) as f:
            menu = json.load(f)
    except FileNotFoundError:
        try:
            script_directory = os.path.dirname(__file__)
            with open(os.path.join(script_directory, menu_filename)) as f:
                menu = json.load(f)
        except FileNotFoundError:
            if base_opts.menu_item:
                raise
            else:
                pass

    if base_opts.menu_item:
        try:
            args = shlex.split(menu[base_opts.menu_item]["args"])
            base_opts, leftover = base_parser.parse_known_args(args)
        except KeyError:
            print(f"\nError: No such menu item {base_opts.menu_item} found in {menu_filename}, ignoring")

    if base_opts.hex:
        base_opts.base = 16

    global set_of_all_digits
    set_of_all_digits = frozenset("0123456789abcdef"[0:base_opts.base])

    ## opts = parse_opts(leftover)

    ## if leftover is not None:
    newopts, foo = parser.parse_known_args(leftover)

    if len(foo) > 0:
        print("\nWarning: Some bad arguments were ignored.", foo)
        #continue

    opts = newopts

    opts.length = max(opts.length, 1)

    if opts.op is None:
        opts.op = operator.mul

    if len(opts.allowed_digits) == 0:
        if not opts.allow_trivial and base_opts.base > 4 and operator.sub != opts.op:
            opts.allowed_digits = set_of_all_digits - frozenset("01")
        else:
            opts.allowed_digits = set_of_all_digits

    opts.allowed_digits -= opts.disallowed_digits
    opts.allowed_digits |= opts.required_digits

    opts.allowed_digits &= set_of_all_digits

    # Kludge for allowing more than 2 operands in case of addition
    if opts.op not in (operator.sub, operator.mul, operator.floordiv):
        opts.num_operands = non_arithmetic_operators.index(opts.op) + 2
        opts.op = operator.add
    else:
        opts.num_operands = 2

    return base_opts, opts

def subscript_coda() -> str:
    if opts.show_subscripts == 'none':
        return ''

    if base_opts.base == 2:
        return '\N{SUBSCRIPT TWO}'
    elif base_opts.base == 4:
        return '\N{SUBSCRIPT FOUR}'
    elif base_opts.base == 8:
        return '\N{SUBSCRIPT EIGHT}'
    elif base_opts.base == 10 and opts.show_subscripts == 'all':
        return '\N{LATIN SUBSCRIPT SMALL LETTER T}\N{LATIN SUBSCRIPT SMALL LETTER E}\N{LATIN SUBSCRIPT SMALL LETTER N}'
    elif base_opts.base == 16:
        return '\N{LATIN SUBSCRIPT SMALL LETTER H}\N{LATIN SUBSCRIPT SMALL LETTER E}\N{LATIN SUBSCRIPT SMALL LETTER X}'
    else:
        return ''


args = None

base_opts = None
base_parser = argparse.ArgumentParser(add_help=False)
base_parser.add_argument('-t', '--menu-item', default=None, action='store',
                    help=f'use an options package from {menu_filename} and IGNORE ALL OTHER command-line options')
base_parser.add_argument('-b', '--base', default=10, type=int, choices=[2, 4, 8, 10, 16],
                    help='number base (default is 10)')
base_parser.add_argument('-x', '--hex', action='store_true',
                    help='same as -b 16 (and overrides any -b setting in the command line)')

# use "parents" argument so that -h help gives expected results
parser = argparse.ArgumentParser(parents=[base_parser], description='Prints random operands (in base 10 by default, or hex, binary, base 4, or octal) to be added, subtracted, multiplied, or divided. Awaits input. Type in the answer to test your arithmetic skills, or just hit Enter to see the answer. Appending a comma to your answer means that the digits are to be read in reverse order of what you typed, i.e., the order in which they are calculated. Usually there are two operands, but addition can have more. For division, operands are chosen so that there is never a remainder.')

parser.add_argument('-o', '--op', action='store', type=arithmetic_operation,
                    help='operation to perform: \'*\' or x or . for multiplication, + for addition, - for subtraction, / or ÷ for division; ++ (or +++ or ...) for addition with 3 (or 4 or more, max 52) addends. Default is multiplication')
parser.add_argument('-l', '--length', default = 1, type=int,
        help='maximum length in digits of each operand (default = 1). May be shorter, since leading zeros are omitted. For subtraction, minuend will have an extra leading 1 if it would otherwise be smaller than subtrahend')

group = parser.add_argument_group('specifying digits', 'You can specify that certain digits are required, allowed, or disallowed to occur in operands. You can also specify that certain digits of one operand must or cannot interact with certain digits of other operands. Unless the digits 0 or 1 are specified in ALLOWED_DIGITS or REQUIRED_DIGITS, or the --allow-trivial flag is set, the digits 0 or 1 are disallowed in addends, multiplicands, divisors and their resultant quotients, even if not specified in DISALLOWED_DIGITS, and subtrahends cannot be 0 or 1 if LENGTH is not 1.')

group.add_argument('-r', '--required-digits', default=frozenset(), type=digit_set,
                    help='string of required digits. Each digit found in this string must appear at least once in at least one operand. If a digit is found in this string, that overrides its also being found in DISALLOWED_DIGITS')
group.add_argument('-a', '--allowed-digits', default=frozenset(), type=digit_set,
        help='string of allowed digits, e.g., 02468ace for even hex digits if base is 16. If this flag is given, digits found in this string are allowed to occur in operands unless they are also found in DISALLOWED_DIGITS, and all other digits are disallowed unless they are found in REQUIRED_DIGITS. If this flag is omitted, then all digits are allowed except the ones that are found in DISALLOWED_DIGITS, except for the special handling of 0 and 1 as described above')
group.add_argument('-d', '--disallowed-digits', default=frozenset(), type=digit_set,
        help='string of disallowed digits. Digits found in this string cannot occur in any operand. If a digit is found in this string, that overrides its also being found in ALLOWED_DIGITS. However, if a digit is found in REQUIRED_DIGITS, that overrides its also being found in this string. Note that due to the special handling of 0 and 1 as described above, those digits may be disallowed even if they are not found in this string')
group.add_argument('-m', '--match', type=pattern_stuff,
        help='example: 357:6ae,6ae:357,f:^bd means that digits 6,a,e can only pair with 3,5, or 7; f cannot pair with b or d\n'
                         'For addition or subtraction, each digit of one operand pairs with the corresponding digit at the same digit position (column) of the other operand.\n'
                         'For multiplication, by the distributive property, each digit of one operand pairs with every digit of the other operand.\n'
                         'For division, each digit of the divisor pairs with each digit of the quotient produced by the dividend and divisor')
group.add_argument('-k', '--allow-trivial', action="store_true",
                    help='disable the special handling of digits 0 and 1, treating them like any other digits')
group.add_argument('-v', '--verbose', action='count',
                    help='display verbose information about random operands that were rejected because they do not meet the criteria given by MATCH')

parser.add_argument('--show-work-multiplication', action="store_true",
                    help='"show work" (summands) for multiplication if no answer or a wrong answer was given')
parser.add_argument('--show-subscripts', type=str, default='some', choices=['none','some','all'],
                    help='show none, some, or all of subscripted 2, 4, 8, "ten", "hex" after numbers in bases 2, 4, 8, 10, 16, respectively. Default is "some", which means show all but "ten"')

operator_string = { operator.mul : "×", operator.add : "+", operator.sub : "\u2212", operator.floordiv : "÷" }

base_opts, opts = do_the_parser(args)

while True:
    # Avoid possibility of infinite loop if more required digits are specified than the combined lengths of the operands can hold
    if len(opts.required_digits) > opts.num_operands * opts.length:
        # raise ValueError("Too many required digits")
        print("\nError: Too many required digits")
        operands_as_str_of_digits = ["0" * opts.length for i in range(opts.num_operands)]
    else:
        attempt = 0
        while True:
            operands_as_str_of_digits = ["".join(random.choices(list(opts.allowed_digits), k=opts.length)) for i in range(opts.num_operands)]
            attempt += 1

            if attempt > 100000:
                # raise RuntimeError("Infinite loop?")
                print("\nError: Infinite loop? Can't find suitable operands")
                operands_as_str_of_digits = ["0" * opts.length for i in range(opts.num_operands)]
                break

            if opts.required_digits.issubset(frozenset(itertools.chain.from_iterable(operands_as_str_of_digits))):
                for i in range(opts.num_operands):
                    for j in range(i + 1, opts.num_operands):
                        op1 = operands_as_str_of_digits[i]
                        op2 = operands_as_str_of_digits[j]

                        if opts.op in (operator.mul, operator.floordiv):
                            if opts.match is not None:
                                if not all(opts.match[int(d,base_opts.base)].fullmatch(op2) for d in op1):
                                    if opts.verbose is not None:
                                        print(f"Non-matching pattern of digits within: {op1},{op2}")
                                    break
                                if not all(opts.match[int(d,base_opts.base)].fullmatch(op1) for d in op2):
                                    if opts.verbose is not None:
                                        print(f"Non-matching pattern of digits within: {op1},{op2}")
                                    break

                        if opts.op in (operator.add, operator.sub):
                            if opts.match is not None:
                                if not all(opts.match[int(op1[k],base_opts.base)].fullmatch(op2[k]) for k in range(opts.length)):
                                    if opts.verbose is not None:
                                        print(f"Non-matching pattern of digits within: {op1},{op2}")
                                    break
                                if not all(opts.match[int(op2[k],base_opts.base)].fullmatch(op1[k]) for k in range(opts.length)):
                                    if opts.verbose is not None:
                                        print(f"Non-matching pattern of digits within: {op1},{op2}")
                                    break

                    else:
                        continue

                    break
                else:
                    break

    operands = [build_integer_from_list(i) for i in operands_as_str_of_digits]

    # Add a leading 1 and sufficient number of zeros if minuend would otherwise be smaller than subtrahend
    # If minuend and subtrahend are identical (difference = 0), then disallow
    if operator.sub == opts.op:
        zero_count = 0
        while operands[0] < operands[1]:
            new = '1' + zero_count * '0' + operands_as_str_of_digits[0].lstrip('0')
            operands = [build_integer_from_list(i) for i in (new, *operands_as_str_of_digits[1:])]
            zero_count += 1
        if operands[0] == operands[1]:
            continue

    # Disallow division by zero
    if operator.floordiv == opts.op:
        operands[0] = math.prod(operands)
        if operands[0] == 0:
            continue

    # Disallow operands to be 0 or 1 unless allow-trivial flag is set.
    # However, if we have one-digit operands and we have explicitly required those digits,
    # then we should allow such operands regardless.
    # But for base 2, always allow 0 and 1 if we have one-digit length
    if not opts.allow_trivial:
        if opts.length > 1:
            if 0 in operands or 1 in operands:
                continue
        elif base_opts.base > 2:
            if '0' not in opts.required_digits:
                if 0 in operands:
                    continue
            if '1' not in opts.required_digits:
                if 1 in operands:
                    continue

#       print(("\n".join("{:>{}}".format(hex_no0x(op),opts.length) for op in operands)))
    not_the_first: bool = False
    for i, operand in enumerate(operands):
        operand_str = hex_no0x(operand)
        print((2 + opts.length + opts.length - len(operand_str) - 0) * " ", operator_string[opts.op] if not_the_first else " ", " ", operand_str, sep=" ", end="")
        if i != len(operands) - 1:
            print()
        else:
            print(" ", subscript_coda())
        not_the_first = True

    # Typically just press Enter,
    # but could also be used to reenter new option strings here
    # or a guess of the result
    try:
        line = input().strip()
    except EOFError:
        sys.exit()

    guessed_result = ""

    if len(line) != 0:
        if line == "?":
            try:
                for k, v in menu.items():
                    print( k, "\t", v["title"])
                line = input().strip()
            except NameError:
                print("\nThere are no menu items")
            continue
        elif line[0] == ":":
            try:
                try:
                    line = line[1:].strip()
                    command = menu[line]
                    args = shlex.split(command["args"])
                    print (args)
                    base_opts, opts = do_the_parser(args)
                except NameError:
                    print("\nThere are no menu items")
            except KeyError:
                print(f"\nError: No such menu item {line} found in {menu_filename}, ignoring")
            continue
        elif line[0] == ">":
            line=line[1:].strip()
            args = shlex.split(line)
            base_opts, opts = do_the_parser(args)
            continue
        else:
            try:
                # Ignore anything that comes before a period.
                # This lets you change your mind and try again
                # without erasing your previous attempt which might have some correct digits.
                ls = line.rsplit('.')
                if len(ls) > 1:
                    if ls[-1] == '':
                        line = ls[-2]
                    else:
                        line = ls[-1]

                # Read a number in reverse digit order if a comma is appended to it.
                # A backslash would be more intuitive, but not readily available on all language keyboard layouts.
                ls = line.rsplit(',')
                if len(ls) > 1:
                    if ls[-1] == '':
                        line = ls[-2][::-1]
                    else:
                        line = ls[-1]

                guessed_result = line.strip().lower()

                line = ""
            except ValueError:
                print("\nError: Not a valid number in the current base.")
                continue

    op = opts.op

    result = hex_no0x(functools.reduce(op, operands))
    if guessed_result != "" and result == guessed_result:
        pass
    else:
        if opts.show_work_multiplication and op == operator.mul and opts.num_operands == 2 and opts.length != 1 and min(len(hex_no0x(operand)) for operand in operands) != 1:           # "show work" for (most) multiplication
            print((2 + opts.length + opts.length - len(operand_str) - 0) * " ", " ", " ", opts.length * "\u2550", sep=" ")
            for i, d in enumerate(reversed(hex_no0x(operands[1]))):
                summand = hex_no0x(int(d, base_opts.base) * operands[0])
                print((6 + opts.length + opts.length - len(summand) - i) * " ", summand)
        print((7 - len(operator_string[op]) + opts.length + opts.length - len(result) - 0) * " ", len(result) * "\u2550", sep=" ")
        print((7 - len(operator_string[op]) + opts.length + opts.length - len(result) - 0) * " ", result, sep=" ")

        print("")
