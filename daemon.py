#!/bin/python

import signal
import os
import sys

#Use this variable for your loop
daemon_quit = False

PIPE_FILE = "/tmp/cald_pipe"
DB_LOC_LINK = "/tmp/calendar_link"
ERR_LOG = "/tmp/cald_err.log"

#Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True

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

def add_cmd(command,read,errors):
    date = command[1]
    event_name = command[2] + ","
    
    event_desc = ''
    if len(command) == 4:
        event_desc = command[3]

    for event in read:
        event = event.split(',')
        if event[0] == date and (event[1] + ",") == event_name:
            errors.append("Duplicate event\n")
            return read,errors
    
    read.append(date+','+event_name+event_desc.strip("\n"))
    return read,errors

def del_cmd(command,read,errors):
    date = command[1]
    event_name = command[2]
    
    event_desc = ''
    if len(command) == 4:
        event_desc = command[3]

    for event in read:
        eventls = event.split(',')
        if date == eventls[0] and event_name == eventls[1]:
            read.pop(read.index(event))
            return read,errors

    errors.append("Event not found\n")
    return read,errors

def upd_cmd(command,read,errors):
    date = command[1]
    event_name = command[2]
    event_name_new = command[3] + ","
    event_desc_new = ""
    if len(command) == 5:
        event_desc_new = command[4]
    for event in read:
        eventls = event.split(',')
        if date == eventls[0] and event_name == eventls[1]:

            read[read.index(event)] = date+','+event_name_new+event_desc_new
            return read,errors

    errors.append("Unable to update, event does not exist\n")
    return read,errors

def run():
    #Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    CSV_FILE = "/home/cald_db.csv"

    # Create pipe
    if not os.path.exists(PIPE_FILE):
        os.mkfifo(PIPE_FILE)

    #Create csv database
    if len(sys.argv) > 1:
        CSV_FILE = sys.argv[1]

    if not os.path.exists(CSV_FILE):
        db_csv = open(CSV_FILE,'x')
        db_csv.close()

    #Write csv db location
    db_loc = open(DB_LOC_LINK, 'w')
    db_loc.write(CSV_FILE)
    db_loc.close()

    #Open error log
    
    errors = []
    while not daemon_quit:
        db = open(CSV_FILE, 'r')
        init_read = db.readlines()
        db.close()

        errors_file = open(ERR_LOG, 'w')
        errors_file.writelines(errors)
        errors_file.close()

        read = []
        for x in init_read:
            read.append(x.strip("\n"))

        pipe = open(PIPE_FILE, "r")
        command_read = pipe.readline()
        if "," in command_read:
            command = command_read.split(",")
        else:
            command_read = command_read.split(" ")
            command = []
            str_build = ''
            for elem in command_read:
                elem = elem.strip("\n")
                if '"' in elem:
                    if elem.startswith('"') and elem.endswith('"'):
                        command.append(elem[1:-1])
                        str_build = ''
                    elif elem.startswith('"'):
                        str_build = elem[1:]
                    elif elem.endswith('"'):
                        str_build += " " + elem[:-1]
                        command.append(str_build)
                        str_build = ''

                else:
                    if str_build == '':
                        command.append(elem)
                    else:
                        str_build += " " + elem
            
        for i,x in enumerate(command):
            if "\n" in x:
                command[i] = x.strip("\n")
                    
        

        if len(command) > 1:
            if command[0] == "ADD":
                new_cal,errors = add_cmd(command,read,errors)
                
                db_csv = open(CSV_FILE, 'w')
                if len(new_cal) > 1:
                    for event in new_cal[:-1]:
                        db_csv.write(event + "\n")
                    db_csv.write(new_cal[-1]+ "\n")
                elif len(new_cal) == 1:
                    db_csv.write(new_cal[0]+ "\n")
                else:
                    db_csv.write("")
                db_csv.close()
                read = new_cal
                

            elif command[0] == "DEL":
                new_cal,errors = del_cmd(command,read,errors)
                db_csv = open(CSV_FILE, 'w')
                if len(new_cal) > 1:
                    for event in new_cal[:-1]:
                        db_csv.write(event + "\n")
                    db_csv.write(new_cal[-1]+ "\n")
                elif len(new_cal) == 1:
                    db_csv.write(new_cal[0]+ "\n")
                else:
                    db_csv.write("")
                db_csv.close()
                read = new_cal
                

            elif command[0] == "UPD":
                new_cal,errors = upd_cmd(command,read,errors)
                db_csv = open(CSV_FILE, 'w')
                if len(new_cal) > 1:
                    for event in new_cal[:-1]:
                        db_csv.write(event + "\n")
                    db_csv.write(new_cal[-1]+ "\n")
                elif len(new_cal) == 1:
                    db_csv.write(new_cal[0]+ "\n")
                else:
                    db_csv.write("")
                db_csv.close()
                read = new_cal
                

            errors_file = open(ERR_LOG, 'w')
            errors_file.writelines(errors)
            errors_file.close()
    errors_file.close()        
    pipe.close()
if __name__ == '__main__':
    run()