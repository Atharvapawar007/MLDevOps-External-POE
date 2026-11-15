#!/usr/bin/env python3
"""
addition.py - Core addition logic and standalone CLI interface.

Accepts two numbers, computes their addition, and displays the result.
"""

import sys
import argparse
from typing import Union


def add_numbers(num1: Union[int, float], num2: Union[int, float]) -> Union[int, float]:
    """
    Adds two numbers and returns their sum.

    Args:
        num1: The first number (int or float).
        num2: The second number (int or float).

    Returns:
        The arithmetic sum of num1 and num2.

    Raises:
        TypeError: If either input is not a number.
    """
    if not isinstance(num1, (int, float)) or not isinstance(num2, (int, float)):
        raise TypeError(f"Both inputs must be numeric types (int or float). Received: {type(num1).__name__}, {type(num2).__name__}")
    
    # Check for NaN or infinity if desired, but standard addition handles floats
    return num1 + num2


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments if provided."""
    parser = argparse.ArgumentParser(
        description="Accept two numbers and display their addition."
    )
    parser.add_argument(
        "--num1",
        type=float,
        default=None,
        help="First number for addition"
    )
    parser.add_argument(
        "--num2",
        type=float,
        default=None,
        help="Second number for addition"
    )
    return parser.parse_args()


def interactive_input() -> tuple[float, float]:
    """Prompt the user interactively to accept two numbers."""
    print("=" * 45)
    print("       Python Addition Calculator")
    print("=" * 45)
    
    while True:
        try:
            val1 = input("Enter the first number: ").strip()
            num1 = float(val1)
            break
        except ValueError:
            print("Invalid input! Please enter a valid numerical value.")
    
    while True:
        try:
            val2 = input("Enter the second number: ").strip()
            num2 = float(val2)
            break
        except ValueError:
            print("Invalid input! Please enter a valid numerical value.")
            
    return num1, num2


def main():
    """Main execution entry point."""
    args = parse_arguments()

    if args.num1 is not None and args.num2 is not None:
        num1, num2 = args.num1, args.num2
    else:
        num1, num2 = interactive_input()

    result = add_numbers(num1, num2)

    # Format output nicely: display integer if the result has no fractional part
    formatted_num1 = int(num1) if num1.is_integer() else num1
    formatted_num2 = int(num2) if num2.is_integer() else num2
    formatted_result = int(result) if isinstance(result, float) and result.is_integer() else result

    print("-" * 45)
    print(f"First Number  : {formatted_num1}")
    print(f"Second Number : {formatted_num2}")
    print(f"Addition (+)  : {formatted_result}")
    print("-" * 45)
    print(f"Formula: {formatted_num1} + {formatted_num2} = {formatted_result}")
    print("=" * 45)


if __name__ == "__main__":
    main()
