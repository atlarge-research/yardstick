
import sys
import os
import socket

def main(args):
    hostnames = sorted(os.environ['PRUN_PE_HOSTS'].split())
    thismachine = socket.gethostname()
    thisindex = hostnames.index(thismachine)

    thisrole = "UNKNOWN"
    with open('roles', 'r') as fin:
        total = 0
        for line in fin:
            num, role = line.split()
            num = int(num)
            num += total
            if thisindex < num:
               thisrole = role 
               break
    print thisrole

if __name__ == "__main__":
    main(sys.argv[1:])
