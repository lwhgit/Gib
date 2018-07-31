import Gib

def main():
    print("봇을 선택하세요.")
    for i in range(0, len(Gib.TOKEN)):
        print("    " + str(i + 1) + " : ", end="")
        print(Gib.TOKEN[i]["name"])
    
    index = input()
    
    Gib.login(int(index) - 1)
    
main()