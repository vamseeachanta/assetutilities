# Third party imports
from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init()

print(f"This is {Fore.GREEN}color{Style.RESET_ALL}!")
print(f"Tests passed: {Fore.GREEN}{10}{Style.RESET_ALL}")
print(f"Tests Failed: {Fore.RED}{3}{Style.RESET_ALL}")
