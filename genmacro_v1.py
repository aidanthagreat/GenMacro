'''
    GenMacro
    
    version 1
    2026 09 25

    
'''

#crutch
import mouse, keyboard

import time, os, sys
import threading

#ui
from ctypes import windll

import tkinter as tk
from tkinter import simpledialog, messagebox



class throw(Exception):
    '''
        Throws a custom error message
        Pass: 
            error message
    '''
    def __init__(self,str):
        self.str=str

    def __str__(self):
        return(f">>{self.str}")


def log(opt=0,msg="flag"):
    '''
        Universal log function 
        Pass: 
            output type and message to print
        Throw: 
            if the option is invalid, throws an error
    '''
    match opt:
        case 0:
            print("[\033[0;32mDBG\033[0m]",end=" ")
        case 1:
            print("[\033[0;35mWRN\033[0m]",end=" ")
        case 2:
            print("[\033[0;91mERR\033[0m]",end=" ")
        case _:
            raise throw(f"Invalid log type: {opt}")
    print(msg)



class macro():
    '''
        Macro class, backbone of the entire program
        Has built in recorders and runners using mouse, keyboard, and threading
        Pass: 
            name, round precision, step precision
            round precision determines the accuracy of timing in therecorder
            higher precision, better accuracy: 4-> 4.2736, 2-> 4.27
            lower to save space for longer macros
            step precision determines how many updates per second the recorder uses
            step precision is not the exact precision, its just a limit
            higher precision, better accuracy: 30-> limited to 30 updates a second
            lower to save resources and space
    
    '''

    def __init__(self,name, settings):
        self.name=name
        self.instructions=[[],[],[]]
        self.failsafeTrigger=False
        
        self.round_precision=None
        self.step_precision=None
        self.keybind_start=None
        self.keybind_stop=None

        self.mpEndFlag=False
        self.moveEndFlag=False
        self.keyEndFlag=False

        self.sset(settings)

        self.stopFlag=threading.Event()


    def retName(self):
        return self.name
    
    def retInstruct(self):
        return self.instructions

    def setKeybindStart(self,keyControl):
        self.keybind_start=keyControl

    def setKeybindStop(self,keyControl):
        self.keybind_stop=keyControl

    def sset(self, settings):
        self.keybind_start=f"{settings[0]}+{settings[1]}"
        self.keybind_stop=f"{settings[2]}+{settings[3]}"
        self.setRoundPrecision(int(settings[4]))#pre checked to meaningful extent
        self.setStepPrecision(int(settings[5]))

    def setRoundPrecision(self, round_precision):
        '''
            Sets the round precision
            Will log a warning if extreme precision is detected
            Pass: 
                precision amt
        '''
        self.round_precision=round_precision
        if(round_precision==0 or round_precision>8):
            log(1,f"Extreme round precision ({round_precision})")
            
    def setStepPrecision(self, step_precision):
        '''
            Sets the step precision
            Will log a warning if extreme precision is detected
            Pass: 
                precision amt
        '''
        self.step_precision=(round(1/step_precision,self.round_precision))
        if(self.step_precision==0 or self.step_precision>0.1):
            log(1,f"Extreme step precision ({step_precision})")


    def delay(self, pausetime):
        '''
            Waits 
            This function is here as a placeholder
            Pass: 
                time to sleep'
                
            TODO: experiment with perf_counter
        '''
        #test perf_counter
        time.sleep(pausetime)

    def flush(self):
        pass

    def awaitAbort(self):
        '''
            Waits for stop keybind
            sets the stop flag when detected

            TODO: look into interference caused by setting keybinds
        '''
        while(not self.stopFlag.is_set()):
            if(keyboard.is_pressed(self.keybind_stop)):
                self.stopFlag.set()
            time.sleep(0.05)

    def forceFlag(self):
        keyboard.send(self.keybind_stop, True, False)
        keyboard.is_pressed(self.keybind_stop)
        keyboard.send(self.keybind_stop, False,True)


    def setInstruct(self,instructions):
        '''
            Sets instructions from compilation of a file
            instructions[0] corresponds to mouse movemount
            instructions[1] corresponds to mouse control
            instructions[2] corresponds to keyboard
            Pass: 
                list instructions containing tuples representing actions and wait times
                if a tuple is found, the macro will push an action
                if not, a stall is indicated. instead will push a stall command that waits
                for example, [[][][(c1,1),s0.5]] 
                located in row 2, macro will push the action 'push key code 1 down, then wait 0.5 seconds'
        '''
        for r in range(len(instructions)):
            for c in range(len(instructions[r])):

                if not instructions[r][c]:
                    continue

                isT=(isinstance(instructions[r][c],tuple))

                if(isT):
                    if(r==0):      #mouse
                        self.instructions[r].append(lambda c=instructions[r][c]:self.move(*c))
                    elif(r==1):     #left
                        self.instructions[r].append(lambda c=instructions[r][c]:self.mp(*c))
                    elif(r==2):           #key
                        self.instructions[r].append(lambda c=instructions[r][c]:self.key(*c))
                else:               #const stall
                    self.instructions[r].append(lambda c=instructions[r][c]:self.delay(c))


    def useInstruct(self,i):#read
        '''
            Entry point for individual threads for runMacro
            each thread is assigned an individual row
            Pass: 
                index of row
            
        '''
        for callable in self.instructions[i]:
            if(not self.stopFlag.is_set()):
                callable()
    
        if(i==0):
            self.moveEndFlag=True
        elif(i==1):
            self.mpEndFlag=True
        else:
            self.keyEndFlag=True

        if(self.moveEndFlag and self.mpEndFlag and self.keyEndFlag):
            self.stopFlag.set()#<<<
            

    def rec(self):#self.recording
        '''
            Records all input
            must watch from another thread
        '''

        
        log(0,f"Begin recording {self.name}")

        mT=threading.Thread(target=self.tMouse)
        cT=threading.Thread(target=self.tMouseC)
        kT=threading.Thread(target=self.tKey)

        mT.daemon=True
        cT.daemon=True
        kT.daemon=True

        mT.start()
        cT.start()
        kT.start()

        mT.join()
        cT.join()
        kT.join()

        self.stopFlag.clear()
        return f"{self.name}: Recording stopped"





    def run(self):#running
        '''
            Runs loaded instructions
            
        '''
        self.mpEndFlag=False
        self.moveEndFlag=False
        self.keyEndFlag=False

        log(0,f"Begin replay of {self.name}")
        t=threading.Thread(target=lambda:self.useInstruct(0))
        t1=threading.Thread(target=lambda:self.useInstruct(1))
        t2=threading.Thread(target=lambda:self.useInstruct(2))
        t3=threading.Thread(target=self.awaitAbort)#watches

        t.daemon=True
        t1.daemon=True
        t2.daemon=True
        t3.daemon=True

        t.start()
        t1.start()
        t2.start()
        t3.start()

        t.join()
        t1.join()
        t2.join()
        t3.join()

        self.stopFlag.clear()

        log(0,f"Finished running {self.name}")
        #keyboard.restore_state(keyboard.stash_state()) this doesnt work
        #if the pgoram is force closed find out how to reset keys
        

    #
    #
    #
    #
    # Movement instructions


    def move(self,x,y):
        '''
            Thread 1
            moves the mouse
            
            TODO: look at the 'fix' feature in earlier versions, test on multiple screen sizes
        '''
        #x = int(x/self.div_x)
        #y = int(y/self.div_y)
        mouse.move(x,y,True)


    def mp(self, ctype, action):#c1,1
        '''
            Thread 2
            mouse click
            Pass: 
                type (left or right click), action (up or down)
                ctype 1=left, 0=right
                action 1=down, 0=up
        '''
        if(ctype==1):#1=left
            if(action==1):#1=down
                mouse.press(mouse.LEFT)
            else:
                mouse.release(mouse.LEFT)
        else:
            if(action==1):
                mouse.press(mouse.RIGHT)
            else:
                mouse.release(mouse.RIGHT)


    def key(self,keyid,action):#c3,1
        '''
            Thread 3
            Keyboard
            Pass: 
                key code, action (up or down)
                action 1=down, 0=up
            
            TODO: find out why calling keyboard.is_pressed fixes ghost keys
        '''
        if(action==1):
            keyboard.send(keyid, True, False)
            keyboard.is_pressed(keyid)
        else:
            keyboard.send(keyid, False,True)
        

        

    # movement instructions
    #
    #
    #
    # Recording functions


    def tMouse(self): #time,pos,lastPos -> _Mouse _end     [0] c PosX,PosY
        '''
            Thread 1
            Record Mouse movement
            Pushes instructions in real time
        '''
        log(0,"Recording mouse movement")
        instructions=[]
        track=time.time()
        lastPos=mouse.get_position()
        currentPos=lastPos
        
        while not self.stopFlag.is_set():
            
            currentPos=mouse.get_position()#-> (x,y)
            if(currentPos!=lastPos):
                moveTime=time.time()
                instructions.append(f"s{round(moveTime-track,self.round_precision)}")
                instructions.append(f"c{currentPos[0]},{currentPos[1]}")
                track=time.time()
            
            lastPos=mouse.get_position()#-> (x,y)
            self.delay(self.step_precision)
            
        log(0,"Stopped recording mouse movement")
        self.instructions[0]=instructions



    def tMouseC(self):#time,pos,lastPos -> _MouseC _end           [1][2]c PosX,PosY,dur
        '''
            Thread 2
            Record Mouse function
            pushes instructions in real time
            has a check to ensure a macro cannot exit without releasing all pressed inputs
            
            TODO: find out if this actually works, may need to invert not None
        '''
        log(0,"Recording mouse function")
        instructions=[]
        trackLeft=time.time()
        trackRight=time.time()
    
        pressingLeft=None
        pressingRight=None

        while not self.stopFlag.is_set():
            
            if mouse.is_pressed('left'):#left click
                if pressingLeft is None:
                    pressingLeft=time.time()
                    instructions.append(f"s{round(pressingLeft-trackLeft, self.round_precision)}c1,1")
            else:
                if pressingLeft is not None:  
                    duration = time.time() - pressingLeft
                    instructions.append(f"s{round(duration, self.round_precision)}c1,0")
                    pressingLeft=None  
                    trackLeft=time.time()
            if mouse.is_pressed('right'):#right click
                if pressingRight is None:  
                    pressingRight=time.time()
                    instructions.append(f"s{round(pressingRight-trackRight, self.round_precision)}c0,1")
            else:
                if pressingRight is not None: 
                    duration=time.time()-pressingRight
                    instructions.append(f"s{round(duration, self.round_precision)}c0,0")
                    pressingRight=None  
                    trackLeft=time.time()
                
            self.delay(self.step_precision)
        
        if pressingLeft is not None:  #reset left pressed
            duration = time.time() - pressingLeft
            instructions.append(f"s{round(duration, self.round_precision)}c1,0")
        if pressingRight is not None: #reset right pressed
            duration=time.time()-pressingRight
            instructions.append(f"s{round(duration, self.round_precision)}c0,0")

    
        log(0,"Stopped recording mouse function")
        self.instructions[1]=instructions

        

    def tKey(self):                            #   [3] c keyid 1/0 down/up
        '''
            Thread 3
            Record Keyboard
            Pushes instructions after recording ends
            Resets all pressed keys 
            
            TODO: find out how keyboard.record works
        '''
        log(0,"Recording keyboard")

        

        instructions=[]
        lost_keys=[0]*100
        
        track=time.time()
        events=[]

        def c(event):
            if (not self.stopFlag.is_set()):
                events.append(event)

        keyboard.hook(c)
        keyboard.start_recording(events)#<<
        self.awaitAbort()
        keyboard.unhook(c)

        if(not len(events)):#events are none
            return
        
        for i in range(len(events)):

            if events[i].event_type=='down': 
                instructions.append(f"s{round(events[i].time-track, self.round_precision)}c{events[i].scan_code},1") 
                track=events[i].time
                lost_keys[events[i].scan_code]=1
            elif events[i].event_type== 'up':
                instructions.append(f"s{round(events[i].time-track, self.round_precision)}c{events[i].scan_code},0") 
                track=events[i].time
                lost_keys[events[i].scan_code]=0
                
        for i in range(len(lost_keys)):#close all pressed keys (very important)
            if(lost_keys[i]==1):
                instructions.append(f"c{i},0") 

        
        log(0,"Stopped recording keyboard")
        self.instructions[2]=instructions






#Macro end
#
#
#
#
#checking functions





def settingsWrite(where, settings):
    settingsWriteHelper(where, settings)


def settingsWriteHelper(where, settings):
    '''
        Writes data to settings
        Pass: 
            the path to the file, the data to write
    '''
    if(not os.path.exists(where)):
        raise throw(f"{where} does not exist")
    
    with open(where,'w') as fileOUT:#replace
        fileOUT.write("keybind_start_1:")
        fileOUT.write(settings[0])
        fileOUT.write("\nkeybind_start_2:")
        fileOUT.write(settings[1])
        fileOUT.write("\nkeybind_stop_1:")
        fileOUT.write(settings[2])
        fileOUT.write("\nkeybind_stop_2:")
        fileOUT.write(settings[3])
        fileOUT.write("\nround_precision:")
        fileOUT.write(str(settings[4]))
        fileOUT.write("\nstep_precision:")
        fileOUT.write(str(settings[5]))
        fileOUT.write("\n")
    #oserror or excption


def settingsComp(where, data_send_list, DEFAULT_SETTINGS):
    try:
        settingsCompHelper(where, data_send_list)
    except ValueError as e:
        log(2,f"Bad value: {e}")
    except OSError as e:
        log(2,f"File error: {e}")
    except Exception as e:
        log(1,f"Rewriting settings: {e}")
        settingsWrite(where,DEFAULT_SETTINGS)
        log(0,f"Defaults restored")
    
def settingsCompHelper(where, data_send_list):
    '''
        Compiles all settings presets
        Pass: 
            settings file location, a list
            list will be cleared to ensure no duplication
    '''
    # if(not os.path.exists(where)):
    #     raise throw(f"{where} does not exist")
    
    #data_send_list.clear()#if called twice will not stack and throw err
    preset_count=0
    line_cont_val_start=0

    with open(where,'r+') as fileIN:
        for i,line in enumerate(fileIN, start=1):#for line
            line_cont_val_start=line.find(':')
    
            #unused settings switcher: incredibly niche and complicated
            #preset init to -1
            #if(line.strip().endswith(">>")):#define alloc  line[-3:len(line)-1]==">>"
            #    preset_count+=1
            #    data_send_list.append([line[:-3],"ctrl+shift",4,30])#defaults just incase 
            #if(preset_count>-1):#valid preset
    
            if("keybind_start_1" in line and preset_count==0):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("keybind_start_2" in line and preset_count==1):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("keybind_stop_1" in line and preset_count==2):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("keybind_stop_2" in line and preset_count==3):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("round_precision" in line and preset_count==4):
                data_send_list.append(int(line[line_cont_val_start+1:len(line)-1]))
                preset_count+=1
            if("step_precision" in line and preset_count==5):
                data_send_list.append(int(line[line_cont_val_start+1:len(line)-1]))
                preset_count+=1
            if(preset_count==7):
                raise throw("Too many values listed in settings.txt")
    if(preset_count==0):
        raise Exception
    #value os excpt



#settings file end
#
#
#
#macro file start




def fileCompHelper(where,m):
    '''
        Compiles instructions for a macro object
        Pass: 
            directory, existing macro with a name
    '''
    m_dir=f"{where}/{m.retName()}"
    if os.path.isfile(m_dir):
        log(0,f"{m.retName()} located")
    else:
        raise throw(f"{m.retName()}: file does not exist")

    n=n1=0
    send_index=0
    line_instruction_count=0
    line_cont_end=0
    m_current_alloc=-1
    
    m_data_send_list=[[],[],[]]
        
    with open(m_dir,"r") as fileIN:
        for line_count, line in enumerate(fileIN, start=1):#for line
            
            if(line[1:3]==">>"):#define alloc in macrolist
                m_current_alloc=int(line[0:1])
                continue
            
            line_cont_end=line.find(';')
            
            if(line_cont_end or m_current_alloc>-1):#has data, defined alloc
                for i,ch in enumerate(line):#char in line
                    
                    if(ch.isalpha()):#c,s
                        send_index=i+1
                        while((not line[send_index].isalpha()) and (send_index!=line_cont_end)):send_index+=1
                        try:
                            n,n1=tuple(map(int, line[i+1:send_index].split(",")))
                            m_data_send_list[m_current_alloc].append((n,n1))
                        except ValueError:
                            m_data_send_list[m_current_alloc].append(float(line[i+1:send_index]))
                        line_instruction_count+=1
            else:
                raise throw(f"{m.retName()}: line {line_count}: Invalid action\n\t >>>{line}")
    #value index os expt
    
    m.setInstruct(m_data_send_list)
    log(0,f"{m.retName()} created with {line_instruction_count} instructions")


def fileComp(where,m):
    try:
        fileCompHelper(where,m)
    except ValueError as e:
        log(2,f"Invalid instruction: {e}")
    except IndexError as e:
        log(2,f"Read error: {e}")
    except OSError as e:
        log(2,f"File error: {e}")
    except Exception as e:
        log(2,f"Error: {e}")




def fileWriteHelper(where,m):
    '''
        Writes instructions from a macro object
        should be called after macro.recMacro 
        Pass: 
            directory containing macros, existing macro
        
        TODO: check directory
    '''

    m_dir=f"{where}/{m.retName()}"
    if os.path.isfile(m_dir):
        log(0,f"{m.retName()} located")
    else:
        raise throw(f"{m.retName()}: file does not exist")

    MAX_INSTR=20
    max_instr_line=MAX_INSTR
    m_ref_instr=m.retInstruct()
    
    with open(m_dir,'+r') as fileOUT:
        
        for r in range(len(m_ref_instr)):
            if m_ref_instr[r]: #skip if empty
                fileOUT.write(f"{r}>>\n")
                max_instr_line=MAX_INSTR
                    
                for c in range(len(m_ref_instr[r])):
                            
                    if(isinstance(m_ref_instr[r][c],tuple)):
                        fileOUT.write("c")
                        for i in range(len(m_ref_instr[r][c])-1):
                            fileOUT.write(f"{m_ref_instr[r][c][i]},")
                        fileOUT.write(f"{m_ref_instr[r][c][len(m_ref_instr[r][c])-1]}")
                    else:
                        fileOUT.write(m_ref_instr[r][c])
                    max_instr_line-=1
                    
                    if(max_instr_line==0):
                        fileOUT.write(';\n')
                        max_instr_line=MAX_INSTR
                    elif(c==len(m_ref_instr[r])-1):
                        fileOUT.write(';\n')
                        max_instr_line=MAX_INSTR
    
    #os excpt


def fileWrite(where,m):
    try:
        fileWriteHelper(where,m)
        log(0,f"Write successful: {m.retName()}")
    except OSError as e:
        log(2,f"File error: {e}")
    except Exception as e:
        log(2,f"Error: {e}")




def checkDirHelper(settingsDir,macrosDir,fileSettings):
    '''
        Runs checks to validate directory and validity
        if directories are not found, will try to create
        if settings is empty, new defaults are written
        
        Pass:
            directory of settings, macros, and settings file
    '''
    
    if(not os.path.exists(settingsDir)):
        os.makedirs(settingsDir)
    if(not os.path.exists(macrosDir)):
        os.makedirs(macrosDir)
    if (not os.path.exists(fileSettings)):
        if(not checkFile(settingsDir,fileSettings)):
            raise Exception("")#???
        settingsWrite(fileSettings,[['ctrl+shift','ctrl+alt',4,30]])



def checkDir(settingsDir,macrosDir,fileSettings):
    try:
        checkDirHelper(settingsDir,macrosDir,fileSettings)
        log(0,"All directories located")
    except Exception as e:
        log(2,"Directories could not be located")
        sys.exit(1)




#macro file end
#
#
#
#functions start



def getInt(prompt):
    '''
        Gets an int
        Pass: 
            the prompt
    '''
    while True:
        try:
            a = int(input(prompt))
            return a
        except ValueError:
            log(2,"Invalid input")
    

def validateInt(val):
    try:
        int(val)
        return 1
    except ValueError:
        return 0
    
        
    
def createFile():
    '''
        Creates a file with a name the user defines
        currently unused (checkfile)
        TODO: check directory
    '''
    try:
        while 1:
            fileName=input("Enter macro name: ").strip()
            if(fileName[0].isalpha()):
                if(not fileName.endswith(".txt")):
                    fileName+=".txt"
                if(not os.path.exists(fileName)):
                    fileOUT=open(fileName,'x')
                    fileOUT.close()
                    break
                else:
                    print("File already exists")
            else:
                print("File name must begin with alphabetical characters")
    except OSError as e:
        log(2,f"File error: {e}")
        return ""
    return fileName


def delFile(where, fileName):
    '''
        Creates a file with the given file name
        assumes the file exists
        Pass: 
            the filename
        
    '''
    os.remove(f"{where}\\{fileName}")
        
    #oserr throw


def checkFile(where, fileName):
    '''
        Creates a file with the given file name
        Pass: 
            the filename
    '''
    if(fileName[0].isalpha()):
        if(not fileName.endswith(".txt")):
            fileName+=".txt"
        if(not os.path.exists(f"{where}\\{fileName}")):
            #open the full path not filename
            fileOUT=open(f"{where}\\{fileName}",'x')
            fileOUT.close()
        else:#exists
            raise throw(f"{fileName} already exists")
    else:#invalid name
        raise throw(f"{fileName} is not valid")
    #oserr


def listMacros(dir):
    '''
        Gets all macros from the given directory
        Pass: 
            directory
        Returns: 
            the list of macros in the directory
    '''
    macroList=[]
    for fileName in filter(lambda p: p.endswith('.txt'), os.listdir(dir)):
            filePath = os.path.join(dir, fileName)#???
            macroList.append(fileName)
    return macroList

        
def getDir():
    '''
        Gets the current running directory
        Returns: the running directory
    '''
    os.path.dirname(os.path.abspath(__file__))
    current = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(current)
    return current
    #return os.path.dirname(os.path.abspath(sys.argv[0]))


def getVersion():
    ''' 
        Gets the current version
        Displayed on the ui
    '''
    return 1





#checks end
#
#
#
#UI begin





class RunData():
    #assume existence

    def __init__(self,settingsDir,macrosDir,fileSettings,macroList,settingsList, defSettingsList):
        self.macroList=[]
        self.settingsList=[]
        self.settingsDir=settingsDir
        self.macrosDir=macrosDir
        self.fileSettings=fileSettings
        self.macroList=macroList
        self.settingsList=settingsList
        self.tampered=False

        self.defaultStartKey1=defSettingsList[0]
        self.defaultStartKey2=defSettingsList[1]
        self.defaultStopKey1=defSettingsList[2]
        self.defaultStopKey2=defSettingsList[3]
        self.defaultRoundPrecision=defSettingsList[4]
        self.defaultStepPrecision=defSettingsList[5]

        #why cannot init macroList=listMacros
        self.resetMacroList()

        
    def retMacroList(self):
        return self.macroList

    def retMacrosDir(self):
        return self.macrosDir

    def resetMacroList(self):
        self.macroList=listMacros(self.macrosDir)
    
    def retSettingsList(self):
        return self.settingsList
    
    def retSettingsDir(self):
        return self.settingsDir

    #tampered status set reset get
    def setTampered(self):
        self.tampered=True
    
    def resetTampered(self):
        self.tampered=False

    def getTampered(self):
        return self.tampered

    def saveSettings(self, f_settingsList):
        self.settingsList=f_settingsList
        settingsWrite(self.fileSettings,f_settingsList)




class Base:
    '''
        Base class for the UI
        contains tk settings and the active macro
    '''

    def __init__(self, root, rd):
        self.root = root
        self.root.title("GenMacro")
        self.root.geometry("600x400")
        self.root.configure(bg="#BDBDBD")
        self.active=None
        self.mainColor="#B9DAFF"
        self.rd=rd
        
        self.space = tk.Frame(self.root)#new
        self.space.pack(fill="both", expand=True)
        
        self.menuMain=MainMenu(self, self.space)
        self.menuMain.place(relwidth=1, relheight=1)
        
        self.menuSettings=SettingsMenu(self, self.space)
        self.menuSettings.place(relwidth=1, relheight=1)
        
        self.menuCreate=CreateMenu(self, self.space,"Create new macro","Record")
        self.menuCreate.place(relwidth=1, relheight=1)

        self.menuRun=RunMenu(self, self.space,"Run macro","Replay")
        self.menuRun.place(relwidth=1, relheight=1)
        self.showMain()

    def showMain(self):
        self.menuMain.tkraise()
        
    def showSettings(self):
        self.menuSettings.tkraise()

    def showCreate(self):
        self.menuCreate.fileOptLeft.displayMacros()
        self.menuCreate.tkraise()

    def showRun(self):
        self.menuRun.fileOptLeft.displayMacros()
        self.menuRun.tkraise()

    def restore(self):
        '''
            Not ready yet

            TODO: Make this 
        '''
        return
        m=macro("---",self.rd.retSettingsList())
        m.flush()

    def updateLog(self,str):
        self.menuMain.log(str)

    
        

class MainMenu(tk.Frame):
    '''
        The main menu
        
        Access:
        showLoad            related
        showSettings        related
        runMacro            out
        showActive          in
    
    '''
    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base = base
        tk.Label(self, text=f"version {getVersion()}", fg="gray", bg=self.base.mainColor, font=("Arial", 8)).pack(anchor="nw",padx=20)#first access
        tk.Label(self, text="GenMacro", bg=self.base.mainColor, font=("Arial", 30)).pack(pady=0)

        frame=tk.Frame(self,bg=self.base.mainColor)
        frame.pack(pady=40)

        tk.Button(frame, text="Create new", font=("Arial", 16), width=20, command=lambda: base.showCreate()).grid(row=0,column=0,padx=10,pady=10)
        tk.Button(frame, text="Replay", font=("Arial", 16), width=20, command=lambda: self.base.showRun()).grid(row=0,column=1,padx=10,pady=10)
        tk.Button(frame, text="Settings", font=("Arial", 16), width=20, command=lambda: base.showSettings()).grid(row=1,column=0,padx=10,pady=10)
        tk.Button(frame, text="Restore", font=("Arial", 16), width=20, command=lambda: base.restore()).grid(row=1,column=1,padx=10,pady=10)

        #runMacro(self.base.active)
        self.bottom=tk.Frame(self.base.root)
        self.bottom.pack(padx=1,pady=1)
        
        self.console = tk.Text(self.bottom, height=6, bg="#FFFFFF")
        self.console.pack(side="bottom")
        self.log(f"Hover and scroll to see any overflowing messages.")
        
    def log(self, message):
        self.console.config(state="normal")
        self.console.insert(tk.END, ">"+message + "\n")
        self.console.config(state="disabled")
        self.console.see(tk.END)
        



class SettingsMenu2(tk.Frame):
    '''
    '''
    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base = base
        self.saveRP=self.base.rd.retSettingsList()[4]
        self.saveSP=self.base.rd.retSettingsList()[5]

        tk.Label(self, text="Settings", bg=self.base.mainColor, font=("Arial", 18)).pack(pady=10)#first access

        frame=tk.Frame(self,bg=self.base.mainColor)
        frame.pack(pady=20)

        tk.Label(frame, font=("Arial",12),text="Round Precision", bg=self.base.mainColor).grid(row=0,column=1,padx=10,pady=10)
        self.rpE = tk.Entry(frame, font=("Arial",8))
        self.rpE.grid(row=1,column=1,padx=10,pady=10)
        
        tk.Label(frame, font=("Arial",12),text="Step Precision", bg=self.base.mainColor).grid(row=0,column=2,padx=10,pady=10)
        self.spE = tk.Entry(frame, font=("Arial",8))
        self.spE.grid(row=1,column=2,padx=10,pady=10)
        
        tk.Button(self, text="Back", command=lambda: self.back()).pack(pady=2)#last access


    def back(self):
        '''
            TODO: remake this function
        '''
        #get from entry, from tkinter 
        tempRP=self.rpE.get()
        tempSP=self.spE.get()

        if(tempSP=="" and self.saveSP==self.base.rd.defaultStepPrecision):
            tempSP=self.base.rd.defaultStepPrecision
            self.base.updateLog(f"Invalid step precision. Set to default ({tempSP})")
        if(tempRP=="" and self.base.rd.defaultRoundPrecision==self.base.rd.defaultRoundPrecision):
            tempRP=self.base.rd.defaultRoundPrecision
            self.base.updateLog(f"Invalid round precision. Set to default ({tempRP})")
        
        if(validateInt(tempRP) and validateInt(tempSP)):#an int
            if(tempRP!=self.saveRP or tempSP!=self.saveSP):#updated
                #set new 
                self.saveRP=tempRP
                self.saveSP=tempSP
                self.base.rd.setTampered()
                print(self.saveSP)
                print(self.saveRP)
            else:#no updates
                pass
        else:#not int
            pass
        self.base.showSettings()



class SettingsMenu(tk.Frame):
    '''
    '''
    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base = base
        self.popupActive=False
        tk.Label(self, text="Settings", bg=self.base.mainColor, font=("Arial", 18)).pack(pady=10)#first access

        self.Settings2=SettingsMenu2(self.base, self.base.space)
        self.Settings2.place(relwidth=1, relheight=1)

        frameMain=tk.Frame(self,bg=self.base.mainColor)
        frameMain.pack(pady=5)

        tk.Label(frameMain, font=("Arial",12),text="START macro keybind 1", bg=self.base.mainColor).grid(row=0,column=0,padx=10,pady=2)
        tk.Label(frameMain, font=("Arial",12),text="START macro keybind 2", bg=self.base.mainColor).grid(row=1,column=0,padx=10,pady=2)

        tk.Label(frameMain, font=("Arial",12),text="STOP macro keybind 1", bg=self.base.mainColor).grid(row=2,column=0,padx=10,pady=2)
        tk.Label(frameMain, font=("Arial",12),text="STOP macro keybind 2", bg=self.base.mainColor).grid(row=3,column=0,padx=10,pady=2)
        
        tk.Button(frameMain, font=("Arial",12),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(0)).grid(row=0,column=1,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",12),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(1)).grid(row=1,column=1,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",12),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(2)).grid(row=2,column=1,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",12),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(3)).grid(row=3,column=1,padx=10,pady=2)

        self.startKey1 = tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[0]}",font=("Arial", 12), bg=self.base.mainColor)
        self.startKey1.grid(row=0,column=2,padx=10,pady=0,sticky="nsew")#<<<<<<<<<<
        self.startKey2 = tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[1]}",font=("Arial", 12), bg=self.base.mainColor)
        self.startKey2.grid(row=1,column=2,padx=10,pady=0,sticky="nsew")

        self.stopKey1 = tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[2]}",font=("Arial", 12), bg=self.base.mainColor)
        self.stopKey1.grid(row=2,column=2,padx=10,pady=0,sticky="nsew")
        self.stopKey2 = tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[3]}",font=("Arial", 12), bg=self.base.mainColor)
        self.stopKey2.grid(row=3,column=2,padx=10,pady=0,sticky="nsew")

        frameButton=tk.Frame(self,bg=self.base.mainColor)
        frameButton.pack(pady=5)
        
        tk.Button(frameButton, text="Reset defaults", command=lambda: self.resetDefaults()).grid(row=0,column=0,padx=10)
        #tk.Button(frameButton, text="Back", command=lambda: self.back()).grid(row=0,column=1,padx=10)
        tk.Button(frameButton, text="Next", command=lambda: self.nextPage()).grid(row=0,column=2,padx=10)

        tk.Button(self,text="Back", command=lambda: self.back()).pack(pady=2)
        

    def nextPage(self):
        if(not self.popupActive):
            self.Settings2.tkraise()


    def resetDefaults(self):
        if(not self.popupActive):
            self.startKey1.config(text=self.base.rd.defaultStartKey1)
            self.startKey2.config(text=self.base.rd.defaultStartKey2)
            self.stopKey1.config(text=self.base.rd.defaultStopKey1)
            self.stopKey2.config(text=self.base.rd.defaultStopKey2)
            self.Settings2.saveRP=self.base.rd.defaultRoundPrecision
            self.Settings2.saveSP=self.base.rd.defaultStepPrecision
            self.base.rd.setTampered()
           

    def back(self):
        if(not self.popupActive):
            if(self.base.rd.getTampered()):#send, assume checked
                self.base.rd.saveSettings([self.startKey1["text"],self.startKey2["text"],
                                       self.stopKey1["text"],self.stopKey2["text"],
                                       self.Settings2.saveRP,self.Settings2.saveSP])
                self.base.rd.resetTampered()
                self.base.updateLog("Changes saved")
            self.base.showMain()


    def setKeybind(self,n):
        #can otherwise mess with .config(state=...)
        if(not self.popupActive):
            self.base.rd.setTampered()
            self.promptKey(n)
            
    
    def promptKey(self,n):
        #first out
        self.popupActive=True
        popup = tk.Toplevel(self.base.root)
        popup.attributes("-topmost", True)
        popup.title("genmacro")
        popup.geometry("300x100")
        
        label = tk.Label(popup, text="Enter a key...", font=("Arial", 14))
        label.pack(pady=20)

        popup.bind("<<KeyPressReceived>>", lambda a: popup.destroy())

        t = threading.Thread(target=self.setAKey, args=(popup,n), daemon=True)
        t.start()
        

    def setAKey(self,popup,n):
        #from thread

        key=keyboard.read_key()#<<<
        
        if(n==0):#start1
            if(self.startKey2["text"]!=key):
                self.startKey1.config(text=key.lower())
            else:
                self.base.updateLog(f"Cannot have duplicate keys: {self.startKey2["text"]}")
        elif(n==1):#start2
            if(self.startKey1["text"]!=key):
                self.startKey2.config(text=key.lower())
            else:
                self.base.updateLog(f"Cannot have duplicate keys: {self.startKey1["text"]}")


        elif(n==2):#stop1
            if(self.stopKey2["text"]!=key):
                self.stopKey1.config(text=key.lower())
            else:
                self.base.updateLog(f"Cannot have duplicate keys: {self.stopKey2["text"]}")
        else:#3 stop2
            if(self.stopKey1["text"]!=key):
                self.stopKey2.config(text=key.lower())
            else:
                self.base.updateLog(f"Cannot have duplicate keys: {self.stopKey1["text"]}")
            
        popup.event_generate("<<KeyPressReceived>>", when="tail")
        self.popupActive=False




class LoadInterface(tk.Frame):
    '''
        The moveable interface to replace LoadMenu
        
    '''
    def __init__(self, base, parent, onDelete, onSelect):
        super().__init__(parent, bg=base.mainColor)
        self.base = base
        self.selected=None
        self.onSelect=onSelect
        self.onDelete=onDelete

        tk.Label(self,text="Select an existing macro",bg=base.mainColor,font=("Arial", 14)).pack(anchor="center")

        self.listbox = tk.Listbox(self, height=8)
        self.listbox.pack(fill="x", pady=0)

        frameButton = tk.Frame(self, bg=base.mainColor)
        frameButton.pack(pady=2)

        tk.Button(frameButton,text="Select",command=self.select).grid(row=0,column=0,padx=5)
        tk.Button(frameButton,text="Delete",command=self.delete).grid(row=0,column=1,padx=5)

        self.displayMacros()

        
    def select(self):
        opt = self.listbox.curselection()

        if not opt:
            self.base.updateLog('Nothing to select. Click on an existing file and try again.')
            return

        self.selected=self.listbox.get(opt[0])
        self.onSelect(self.selected)


    def delete(self):
        opt = self.listbox.curselection()

        if not opt:
            self.base.updateLog('Nothing to delete. Click on an existing file and try again.')
            return

        selected=self.listbox.get(opt[0])#make sure selected cant be deleted
        if (self.selected==selected):
            self.selected=None

        try:
            delFile(self.base.rd.retMacrosDir(),selected)
            self.base.updateLog(f"Removed {selected}")
        except Exception as e:
            self.base.updateLog(f"Could not remove {selected}: {e}")

        self.displayMacros()
        self.onDelete(selected)


    def displayMacros(self):
        self.listbox.delete(0, tk.END)
        self.base.rd.resetMacroList()

        for item in self.base.rd.retMacroList():
            self.listbox.insert(tk.END,item)



class FileBaseParent(tk.Frame):
    '''
        Implements LoadInterface

        A base class for CreateMenu and RunMenu
        shares frames and active labels
    
    '''
    def __init__(self,base,parent,menuDesc,actionLabel):
        super().__init__(parent,bg=base.mainColor)
        self.base=base
        self.actionLabel=actionLabel

        tk.Label(self, text=menuDesc, bg=self.base.mainColor, font=("Arial", 18)).pack(pady=(10,0))#first access

        frameMain = tk.Frame(self, bg=base.mainColor)
        frameMain.pack(fill="both", expand=True, padx=20, pady=(10,0))

        #left
        self.fileOptLeft = LoadInterface(base, frameMain, self.onDelete, self.onSelect)
        self.fileOptLeft.pack(side="left",fill="both",expand=True,padx=(0, 10))

        #right
        self.frameRight = tk.Frame(frameMain, bg=base.mainColor)
        self.frameRight.pack(side="left",expand=True,pady=0)

        tk.Label(self.frameRight,text="New file",bg=base.mainColor,font=("Arial", 14)).pack(anchor="center",pady=0)

        self.m_name = tk.Entry(self.frameRight)
        self.m_name.pack(fill="x", pady=5)

        tk.Button(self.frameRight,text="Create",command=self.create).pack(pady=0)

        self.activeLabel=tk.Label(self.frameRight,bg=base.mainColor,font=("Arial", 14))
        self.activeLabel.pack(anchor="center",pady=(20,0))

        self.recordButton=tk.Button(self.frameRight,text=self.actionLabel,command=self.customAction)
        self.recordButton.pack(pady=0)
            
        tk.Button(self,text="Back",command=self.base.showMain).pack(pady=2)#last access
        
            
    def create(self):
        m_name = self.m_name.get()

        if not m_name:
            self.base.updateLog('No name inputted. Start typing and try again.')
            return

        try:
            checkFile(self.base.rd.retMacrosDir(), m_name)
            self.fileOptLeft.displayMacros()
            self.base.updateLog(f"{m_name} created.")
            #could add auto select here but list is sorted alphabetically for some reason
            #or duplicate checkFile to return only the final result and do nothing else
        except Exception as e:
            self.base.updateLog(f"Cannot create file: {e}")


    #apprently these methods arent shared cause tkinter is a bum
    #just count on updates called before base.showCreate/showRun to show the correct active file

    def onDelete(self,selected):
        if (self.base.active==selected):
            self.base.active=None
            self.activeLabel.config(text=f"{self.actionLabel} file: None")


    def onSelect(self,selected):
        self.base.active=selected
        self.activeLabel.config(text=f"{self.actionLabel} file: {self.base.active}")


    def customAction(self):
        '''
            Placeholder 
        '''
        pass



        
class CreateMenu(FileBaseParent):
    '''
        Child class of FileBaseParent
        
    '''
    def __init__(self,base,parent,menuDesc,actionLabel):
        super().__init__(base,parent,menuDesc,actionLabel)
        

    def customAction(self):

        if (self.base.active is None):#has active
            self.base.updateLog("No file selected")
            return
            
        m=macro(self.base.active,self.base.rd.retSettingsList())#<<<

        def restore():
            popup.destroy()
            self.base.root.deiconify()
            m.stopFlag.set()


        popup = tk.Toplevel(self.base.root)
        popup.attributes("-topmost", True)
        popup.title(f"GenMacro {self.actionLabel}: {self.base.active}")
        popup.geometry("300x100")
        popup.protocol("WM_DELETE_WINDOW", restore)#manual close failsafe
            
        tk.Label(popup, text=f"{self.actionLabel} Start: {self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}", font=("Arial", 14)).pack(pady=0)
        tk.Label(popup, text=f"{self.actionLabel} Stop: {self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}", font=("Arial", 14)).pack(pady=0)
        tk.Button(popup,text="Back",command=restore).pack(pady=2)#last access

        self.base.root.iconify()
        self.base.root.update()

        t = threading.Thread(target=self.recordingStart,args=(popup,m), daemon=True)
        t.start()#<<<

        
            
    def recordingStart(self, popup,m):
        '''
            Thread 1
        '''
        #wait here
        keyboard.wait(m.keybind_start)
        #start the macro, configure attributes, and record until cancel conditions
        m.rec()#<<<
        fileWrite(self.base.rd.retMacrosDir(),m)
        self.base.updateLog(f"Write successful: {m.retName()}")
        #update macro file here refresh
        



class RunMenu(FileBaseParent):
    '''
        Access:
        
    '''
    def __init__(self,base,parent,menuDesc,actionLabel):
        super().__init__(base,parent,menuDesc,actionLabel)


    def customAction(self):
        if (self.base.active is None):#has active
            self.base.updateLog("No file selected")
            return
        
        m=macro(self.base.active,self.base.rd.retSettingsList())#<<<

        def restore():
            popup.destroy()
            self.base.root.deiconify()
            m.stopFlag.set()


        popup = tk.Toplevel(self.base.root)
        popup.attributes("-topmost", True)
        popup.title(f"GenMacro {self.actionLabel}: {self.base.active}")
        popup.geometry("300x100")
        popup.protocol("WM_DELETE_WINDOW", restore)#manual close failsafe
            
        tk.Label(popup, text=f"{self.actionLabel} Start: {self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}", font=("Arial", 14)).pack(pady=0)
        tk.Label(popup, text=f"{self.actionLabel} Stop: {self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}", font=("Arial", 14)).pack(pady=0)
        tk.Button(popup,text="Back",command=restore).pack(pady=2)#last access

        self.base.root.iconify()
        self.base.root.update()

        t = threading.Thread(target=self.runningStart,args=(popup,m), daemon=True)
        t.start()#<<<


    def runningStart(self,popup,m):
        #wait here
        keyboard.wait(m.keybind_start)
        #start the macro, configure attributes, and run until cancel conditions
        fileComp(self.base.rd.retMacrosDir(),m)
        m.run()#<<<
        self.base.updateLog(f"Replay successful: {m.retName()}")        




#UI end
#
#
#
#main begin




def main():
    #os.path.dirname(os.path.abspath(__file__))
    #current = os.path.dirname(os.path.abspath(sys.argv[0]))
    #os.chdir(current)
    # log(0,f"Running Directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    #directories and files
    DEF_KEYSTART1='ctrl'
    DEF_KEYSTART2='shift'
    DEF_KEYSTOP1='ctrl'
    DEF_KEYSTOP2='alt'
    DEF_RP=4
    DEF_SP=60
    
    current=getDir()
    settingsDir=f"{current}\\settings"
    macrosDir =f"{current}\\macros"
    fileSettings =f"{settingsDir}\\settings.txt"
    macroList=[]
    settingsList=[]

    #init
    checkDir(settingsDir,macrosDir,fileSettings)
    settingsComp(fileSettings,settingsList, [DEF_KEYSTART1,DEF_KEYSTART2,DEF_KEYSTOP1,DEF_KEYSTOP2,DEF_RP,DEF_SP])#<<<
    log(0,"All file checks passed")
    #data for ui
    rd=RunData(settingsDir,macrosDir,fileSettings,macroList,settingsList,[DEF_KEYSTART1,DEF_KEYSTART2,DEF_KEYSTOP1,DEF_KEYSTOP2,DEF_RP,DEF_SP])

    #ui setup
    root = tk.Tk()
    windll.shcore.SetProcessDpiAwareness(1)#for blurry text in widget 
    Base(root, rd)

    log(0,"Starting UI")
    root.mainloop()#<<<

        
if __name__=='__main__':
    main()
    log(0,"End")



'''



'''