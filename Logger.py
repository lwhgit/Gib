from colorama import init
from colorama import Fore, Back, Style

init()

class Log:

    @staticmethod
    def out(str, end="\n"):
        print(Fore.WHITE + str, end=end)

    @staticmethod
    def i(str, end="\n"):
        print(Fore.CYAN + str, end=end)
        
    @staticmethod
    def w(str, end="\n"):
        print(Fore.YELLOW + str, end=end)
        
    @staticmethod
    def e(str, end="\n"):
        print(Fore.RED + str, end=end)
        
    @staticmethod
    def line():
        print(Fore.WHITE + "-------------------------------------------")
    