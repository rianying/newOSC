import json

panel = 'env/startcodepanel.json'
smr = 'env/startcodesmr.json'

#reset every value in the panel to 0001
def resetpanel():
    with open(panel, 'r') as f:
        panel = json.load(f)
        for key in panel:
            panel[key] = '0001'

def resetsmr():
    with open(smr, 'r') as f:
        smr = json.load(f)
        for key in smr:
            smr[key] = '0001'

if __name__ == '__main__':
    # ask user which file to reset, panel, smr, or both
    print('Which file would you like to reset?')
    print('1. Panel')
    print('2. SMR')
    print('3. Both')
    choice = input('Choice: ')
    if choice == '1':
        resetpanel()
    elif choice == '2':
        resetsmr()
    elif choice == '3':
        resetpanel()
        resetsmr()
    else:
        print('Invalid choice')