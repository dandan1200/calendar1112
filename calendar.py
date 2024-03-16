import os
import sys


PIPE_FILE = "/tmp/cald_pipe"
DB_LOC_LINK = "/tmp/calendar_link"

def valid_date(dateIn):
    #Check length
    if len(dateIn) != 10:
        return False
    if dateIn[2] != "-" or dateIn[5] != "-":
        return False
    year = int(dateIn[6]+dateIn[7]+dateIn[8]+dateIn[9])
    month = int(dateIn[3]+dateIn[4])
    day = int(dateIn[0]+dateIn[1])

    if year > 2021 or year < 0 or month > 12 or  month < 1 or day > 31 or day < 0:
        return False
    
    if month in [4,6,9,11]:
        if day > 30:
            return False

    if month == 2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            if day > 29:
                return False
        elif day > 28:
            return False
    
    return True

def get_cmd(command,db):
    if len(command) < 3:
        sys.stderr.write("Error: not enough arguments\n")
        return ""
    events = []
    if db.readable() == False:
        sys.stderr.write("File not readable")
        return ""

    init_read = db.readlines()
    db.close()
    read = []
    for x in init_read:
        read.append(x.strip("\n"))

        
            

    #GET DATE command
    if command[1] == "DATE":
        if len(command) == 2:
            sys.stderr.write("Please specify an argument\n")
            return ""
        dates = command[2:]
        
        for date in dates:
            if valid_date(date) == False:
                sys.stderr.write("Unable to parse date\n")
                return ""
        else:
            for date in dates:
                for row in read:
                    row = row.split(",")
                    if row[0] == date:
                        events.append(row)
    #GET INTERVAL command
    elif command[1] == "INTERVAL":
        if len(command) != 4:
            sys.stderr.write("Error: wrong number of arguments\n")
            return ""
        
        sdate = command[2]
        edate = command[3]

        if valid_date(sdate) and valid_date(edate):
            #check order
            if date_order(sdate,edate) == False:
                sys.stderr.write("Unable to Process, Start date is after End date\n")
                return ""
            for event in read:
                event = event.split(",")
                if date_order(sdate,event[0]) and date_order(event[0],edate):
                    events.append(event)
    #GET NAME command
    elif command[1] == "NAME":
        if len(command) < 3:
            sys.stderr.write("Error: not enough arguments\n")
            return ""
        
        names = [x for x in command[2:]]
                

        for name in names:
            for event in read:
                event = event.split(",")
                if event[1].startswith(name):
                    events.append(event)

    output = ''
    for event in events:
        if len(event) == 3:
            output += (event[0] + " : " + event[1] + " : " + event[2] + "\n")
        else:
            output += (event[0] + " : " + event[1] + " :\n")
    return output
    
def date_order(sdate,edate):
    if int(sdate[6] + sdate[7] + sdate[8] + sdate[9]) > int(edate[6] + edate[7] + edate[8] + edate[9]):
        return False
    elif int(sdate[6] + sdate[7] + sdate[8] + sdate[9]) == int(edate[6] + edate[7] + edate[8] + edate[9]):
        if int(sdate[3]+sdate[4]) == int(edate[3]+edate[4]):
            if int(sdate[0]+sdate[1]) > int(edate[0]+edate[1]):
                return False
        elif int(sdate[3]+sdate[4]) > int(edate[3]+edate[4]):
            return False
    
    return True

def add_cmd(command,pipe):
    if len(command) < 2:
        sys.stderr.write("Unable to parse date\n")
        return ""
    if len(command) < 3:
        sys.stderr.write("Missing event name\n")
        return ""
    date = command[1]
    if valid_date(date) == False:
        sys.stderr.write("Multiple errors occur\n")
        return ""
    if len(command) > 5:
        sys.stderr.write("Multiple errors occur\n")
        return ""
    
    
    pipe.write(",".join(command))

    return ""

def del_cmd(command,pipe):
    if len(command) == 2:
        sys.stderr.write("Missing event name\n")
        return ""
    if len(command) == 1:
        sys.stderr.write("Unable to parse date\n")
        return ""
    if len(command) > 3:

        sys.stderr.write("Too many arguments\n")
        return ""
    else:
        if valid_date(command[1]) == False:
            sys.stderr.write("Unable to parse date\n")
            return ""
        
        pipe.write(",".join(command))
        return ""

def upd_cmd(command,pipe,db):
    init_read = db.readlines()
    db.close()
    read = []
    for x in init_read:
        read.append(x.strip("\n"))

    if len(command) < 3:
        sys.stderr.write("Not enough arguments given\n")
        return ""
    if valid_date(command[1]) == False:
        sys.stderr.write("Unable to parse date\n")
        return ""

    found = False
    for x in read:
        if x.split(",")[0] == command[1] and x.split(",")[1] == command[2]:
            found = True
    if found == False:
        sys.stderr.write("Unable to update, event does not exist\n")
        return ""
    

    pipe.write(",".join(command))
    return ""


def run():
    if os.path.exists(PIPE_FILE):
        pipe = open(PIPE_FILE, "w")
    else:
        sys.stderr.write("Error: Pipe doesn't exist, run daemon.")
        return ""
    
    if os.path.exists(DB_LOC_LINK):
        db_path_file = open(DB_LOC_LINK,'r')
        db_path = db_path_file.read()
        if os.path.exists(db_path):
            cald_db = open(db_path,'r')
        else:
            sys.stderr.write("Unable to process calendar database")
            return
    else:
        sys.stderr.write("Unable to process calendar database")
        return

    if len(sys.argv) < 2:
        sys.stderr.write("Error: not enough arguments")
        return
    
    command = sys.argv[1:]

    if command[0] == "GET":
        print(get_cmd(command,cald_db),end='')

    if command[0] == "ADD":
        print(add_cmd(command,pipe),end='')
    if command[0] == "DEL":
        print(del_cmd(command,pipe),end='')
    if command[0] == "UPD":
        print(upd_cmd(command,pipe,cald_db),end='')



    pipe.close()
    cald_db.close()


if __name__ == '__main__':
    run()

