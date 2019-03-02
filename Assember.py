import re
import instfile


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []


# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))


def lookup(s):
    for i in range(0, symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1


def insert(s, t, a):
    symtable.append(Entry(s, t, a))
    return symtable.__len__() - 1


def init():
    for i in range(0, instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0, instfile.directives.__len__()):
        insert(instfile.directives[i],
               instfile.dirtoken[i], instfile.dircode[i])


file = open('input4.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True

Xbit4set = 0x800000  # ???
# Bbit4set = 0x400000
# Pbit4set = 0x200000
Ebit4set = 0x10000

Nbit4set = 0x200000
Ibit4set = 0x100000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000

Nbit3set = 0x20000
Ibit3set = 0x10000

# Our variable:
IdIndex = 0
startAddress = 0
totalSize = 0
inst = 0
hexOrStrIndex = 0
isLiteral = False
isExtd = False
base = None
PCrange = range(-2048, 2048)  # to 2048 not 2047 because range() is exclusive
disp = 0


def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False


def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '%':
            startLine = True
            while filecontent[bufferindex] != '\n':
                bufferindex = bufferindex + 1
            lineno += 1
            bufferindex = bufferindex + 1
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        # all number are considered as decimals
        tokenval = int(filecontent[bufferindex])
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return 'NUM'
    elif is_hex(filecontent[bufferindex]):
        # all number starting with 0x are considered as hex
        tokenval = int(filecontent[bufferindex][2:], 16)
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return 'NUM'
    elif filecontent[bufferindex] in ['+', '#', ',', '@', '=']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return c
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex + 1] == '\''):
            bytestring = ''
            bufferindex += 2
            # should we take into account the missing ' error?
            while filecontent[bufferindex] != '\'':
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = ('_' if isLiteral is False else '__') + bytestring
            p = lookup(bytestring)
            if p == -1:
                # should we deal with literals?
                p = insert(bytestring, 'STRING', (bytestringvalue if isLiteral is False else -1))
            tokenval = p
        # a string can start with C' or only with '
        elif filecontent[bufferindex] == '\'':
            bytestring = ''
            bufferindex += 1
            # should we take into account the missing ' error?
            while filecontent[bufferindex] != '\'':
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = ('_' if isLiteral is False else '__') + bytestring
            p = lookup(bytestring)
            if p == -1:
                # should we deal with literals?
                p = insert(bytestring, 'STRING', (bytestringvalue if isLiteral is False else -1))
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex + 1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue) % 2 == 1:
                bytestringvalue = '0' + bytestringvalue
            bytestring = ('_' if isLiteral is False else '__') + bytestring
            p = lookup(bytestring)
            if p == -1:
                # should we deal with literals?
                p = insert(bytestring, 'HEX', (bytestringvalue if isLiteral is False else -1))
            tokenval = p
        # elif (filecontent[bufferindex].upper() == 'END') and (filecontent[bufferindex].upper() == 'LTORG'):
        #     # assign address to literals
        #     if pass1or2 == 1:
        #         for search in symtable:
        #             if (search.string[:2] == '__') and (search.att == -1):
        #                 search.att = locctr
        #                 # update the locator
        #                 if search.token == "STRING":
        #                     locctr += (len(search.string) - 2)
        #                 elif search.token == "HEX":
        #                     locctr += (len(search.string) - 4) / 2
        #     elif pass1or2 == 2:
        #         # insert the data values of the literals in the object program
        #         pass
        else:
            p = lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    # should we deal with case-sensitive?
                    p = insert(filecontent[bufferindex].upper(), 'ID', locctr)
                else:
                    # forward reference
                    p = insert(filecontent[bufferindex].upper(), 'ID', -1)
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return symtable[p].token


def error(s):
    global lineno
    print('line ' + str(lineno) + ': ' + s)
    exit(1)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')


def checkindex():
    global bufferindex, symtable, tokenval
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index regsiter should be X')
        match('REG')
        return True
    return False


def parse():
    sic()


def sic():
    header()
    body()
    tail()


def header():
    global IdIndex, startAddress, locctr, totalSize, pass1or2
    IdIndex = tokenval
    match("ID")
    match("START")
    startAddress = locctr = symtable[IdIndex].att = tokenval
    match("NUM")
    if pass1or2 == 2:
        print("H ", symtable[IdIndex].string, format(startAddress, "06X"), format(totalSize, "06x"))


def body():
    global inst, pass1or2, startLine, lookahead

    if lookahead == "ID":
        if pass1or2 == 2:
            inst = 0
        match("ID")
        startLine = False
        rest1()
        body()

    elif lookahead == "f1" or lookahead == "f2" or lookahead == "f3" or lookahead == "+":
        if pass1or2 == 2:
            inst = 0
        stmt()
        body()

    elif lookahead == "WORD" or lookahead == "BYTE" or lookahead == "RESW" or lookahead == "RESB":
        if pass1or2 == 2:
            inst = 0
        stmt()
        body()


def tail():
    global totalSize, locctr, startAddress
    match("END")
    match("ID")
    totalSize = locctr - startAddress
    if pass1or2 == 2:
        print("E ", format(startAddress, '06x'))


def rest1():
    global locctr, inst, hexOrStrIndex, startLine

    if lookahead == "f1" or lookahead == "f2" or lookahead == "f3":
        stmt()

    elif lookahead == "WORD" or lookahead == "BYTE" or lookahead == "RESW" or lookahead == "RESB":
        data()

    else:
        error("Syntax error")


def stmt():
    global locctr, inst, pass1or2, startLine, isExtd
    ind = tokenval
    startLine = False

    # --------------- Format 1 ------------------------------
    if lookahead == "f1":
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        match("f1")
        locctr += 1
        if pass1or2 == 2:
            print("T ", format(locctr - 1, '06x'), " 01 ", format(inst, '02x'))
    # --------------- Format 1 ------------------------------

    # --------------- Format 2 ------------------------------
    elif lookahead == "f2":
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8
        match("f2")
        if pass1or2 == 2:
            inst += (symtable[tokenval].att << 4)
        match("REG")
        locctr += 2
        # rest3:
        if lookahead == ",":
            match(",")
            inst += symtable[tokenval].att
            match("REG")
        if pass1or2 == 2:
            print("T ", format(locctr - 2, '06x'), " 02 ", format(inst, '04x'))

    # --------------- Format 2 ------------------------------

    # --------------- Format 3 ------------------------------
    elif lookahead == "f3":
        # --------------- for RSUB --------------------------
        if symtable[ind].string == 'RSUB':
            match("f3")
            locctr += 3
        # --------------- for RSUB --------------------------
        else:
            if pass1or2 == 2:
                inst = symtable[tokenval].att << 16
            match("f3")
            locctr += 3
            rest4()
            if pass1or2 == 2:
                print("T ", format(locctr - 3, '06x'), " 03 ", format(inst, '06x'))
    # --------------- Format 3 ------------------------------

    # --------------- Format 4 ------------------------------
    elif lookahead == "+":
        isExtd = True
        match("+")
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 20
            inst += Ebit4set
        match("f3")
        if pass1or2 == 2:
            inst += symtable[tokenval].att
        locctr += 4
        rest4()
        isExtd = False
        if pass1or2 == 2:
            print("T ", format(locctr - 4, '06x'), " 04 ", format(inst, '08x'))
    # --------------- Format 4 ------------------------------


def data():
    global locctr, inst, hexOrStrIndex, startLine
    if lookahead == "WORD":
        match("WORD")
        locctr += 3
        if pass1or2 == 2:
            inst = tokenval
            print("T ", format(locctr - 3, '06x'), " 03 ", format(inst, '06x'))
        startLine = False
        match("NUM")
        startLine = True

    elif lookahead == "RESW":
        match("RESW")
        startLine = False
        locctr += tokenval * 3
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        match("NUM")
        startLine = True

    elif lookahead == "RESB":
        match("RESB")
        startLine = False
        locctr += tokenval
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        match("NUM")
        startLine = True

    elif lookahead == "BYTE":
        hexOrStrIndex = tokenval
        match("BYTE")
        startLine = False
        rest2()


def rest4():
    global inst, disp, PCrange
    addressMode()
    if lookahead == "ID":
        if pass1or2 == 2 and not isExtd:
            TA = symtable[tokenval].att
            PC = locctr
            disp = TA - PC
            if disp in PCrange:
                inst += disp
                inst += Pbit3set
            elif base is not None and not isExtd:
                disp = TA - base
                inst += disp
                inst += Bbit3set
            else:
                error("PC and base is not applicable")

        match("ID")

    elif lookahead == "NUM":
        if pass1or2 == 2:
            inst += tokenval
        match("NUM")

    index()


def addressMode():
    global inst, isLiteral
    if lookahead == "@":
        inst += Nbit3set if isExtd is False else Nbit4set
        match("@")

    elif lookahead == "#":
        inst += Ibit3set if isExtd is False else Ibit4set
        match("#")
    elif lookahead == "=":
        isLiteral = True
        match("=")
        inst += Nbit3set if isExtd is False else Nbit4set
        inst += Ibit3set if isExtd is False else Ibit4set
        # rest2()
        isLiteral = False
    else:
        inst += Nbit3set if isExtd is False else Nbit4set
        inst += Ibit3set if isExtd is False else Ibit4set


def index():
    global inst, pass1or2, Xbit3set, startLine
    if lookahead == ",":
        match(",")
        match("REG")
        if pass1or2 == 2:
            inst += Xbit3set
    startLine = True


def rest2():
    global locctr, inst, pass1or2, hexOrStrIndex, startLine
    if lookahead == "HEX":

        locctr += (len(symtable[tokenval].string) - 1) / 2
        # inst += address of literal
        if pass1or2 == 2 and not isLiteral:
            inst = symtable[hexOrStrIndex].att
            print("T ", format(locctr - 3, '06x'), " 03 ", format(inst, '06x'))
        match("HEX")
        startLine = True

    elif lookahead == "STRING":

        locctr += len(symtable[tokenval].string) - 1
        # inst += address of literal
        if pass1or2 == 2 and not isLiteral:
            inst = symtable[hexOrStrIndex].att
            print("T ", format(locctr - 3, '06x'), " 03 ", format(inst, '06x'))
        match("STRING")
        startLine = True


def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    filecontent = re.split("([\\W])", w)
    i = 0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    # to be sure that the content ends with new line
    if filecontent[len(filecontent) - 1] != '\n':
        filecontent.append('\n')
    for pass1or2 in range(1, 3):
        global lookahead
        lookahead = lexan()
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()


main()
