'''
    GenMacro
    
    version 1.2
    2026 11 13

    
'''

import mouse, keyboard
import time, os, sys
import threading

from ctypes import windll
import tkinter as tk




class throw(Exception):
    '''
        Throws a custom error message 
            Used to debug messy file compilations
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
            0: log
            1: warn
            2: error
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



class Macro():
    '''
        Macro parent class
            Delay
            Abort 
    '''

    def __init__(self, name, keybind, mouseToggle, keyboardToggle):
        self.name=name
        
        self.instructions=[[],[]]
        self.keybindToggle=keybind
        self.mouseToggle=mouseToggle
        self.keyboardToggle=keyboardToggle

        self.stopFlag=threading.Event()



    def retName(self):
        return self.name


    def awaitAbort(self):
        '''
            Waits for stop keybind
            sets the stop flag when detected

        '''
        while(not self.stopFlag.is_set()):
            if(keyboard.is_pressed(self.keybindToggle)):
                self.stopFlag.set()
            time.sleep(0.05)
        log(0,f"Stopped macro {self.name}")








        
class Recorder(Macro):
    '''
        Records a macro
            Toggleable mouse and keyboard recording
            Round precision
        TODO:
            implement sc dim
    '''
    def __init__(self, name, keybind, mouseToggle, keyboardToggle, round_precision, sc_dim):
        super().__init__(name, keybind, mouseToggle, keyboardToggle)

        self.current_screen_x=sc_dim[0]
        self.current_screen_y=sc_dim[1]
        
        self.round_precision=round_precision


    def retInstruct(self):
        return self.instructions


    def record(self):#self.recording
        '''
            Records all input
        '''
        self.stopFlag.clear()
        
        log(0,f"Begin recording {self.name}")
        mcwT=threading.Thread(target=self.recordMouse, daemon=True)
        kT=threading.Thread(target=self.recordKey, daemon=True)

        mcwT.start()
        kT.start()

        mcwT.join()
        kT.join()

        self.stopFlag.clear()
        


    def recordMouse(self):#time,pos,lastPos -> _MouseC _end           [1][2]c PosX,PosY,dur (tMouseC)
        '''
            Thread 2
            Record Mouse function
            pushes instructions in real time
            has a check to ensure a macro cannot exit without releasing all pressed inputs
            
            0 LEFT='left'
            1 RIGHT='right'
            2 MIDDLE='middle'
            3 WHEEL='wheel'
            4 X='x'
            5 X2='x2'

        '''
        
        log(0,"Recording mouse")
        track=time.time()
        events=[]
        lost_keys=[0]*6#tracks keys that are not properly released by the end of the recording

        def c(event):
            if (not self.stopFlag.is_set()):
                events.append(event)

        if(self.mouseToggle):
            mouse.hook(c)
            self.awaitAbort()
            mouse.unhook(c)
        else:
            self.awaitAbort()

        log(0,"Stopped recording mouse function")

        if(not len(events)):#events are none
            return

        for event in events:
            if(isinstance(event,mouse.ButtonEvent)):
                if(event.button=='left'):
                    self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}c0,{(event.event_type == "down" or event.event_type=="double")+0}")#down=1 right =1-> cleft,down -> c0,1
                elif(event.button=='right'):
                    self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}c1,{(event.event_type == "down" or event.event_type=="double")+0}")
                elif(event.button=='middle'):
                    self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}c2,{(event.event_type == "down" or event.event_type=="double")+0}")
                elif(event.button=='x'):
                    self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}c3,{(event.event_type == "down" or event.event_type=="double")+0}")
                elif(event.button=='x2'):#none else
                    self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}c4,{(event.event_type == "down" or event.event_type=="double")+0}")
                track=event.time
                #lost keys dictionary here <<<<<<<<<<<<<<<<<
            elif(isinstance(event,mouse.MoveEvent)):
                self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}m{event.x},{event.y}")
                track=event.time
            else: #mousewheel
                self.instructions[0].append(f"s{round(event.time-track,self.round_precision)}w{abs(int(event.delta))},{(event.delta>0)+0}")#check <<<<<<<<<<<<<<<<<
                track=event.time

        # for i in range(len(lost_keys)):#close all pressed keys (very important)
        #     if(lost_keys[i]==1):
        #         self.instructions[1].append(f"c{i},0") 

        

    def recordKey(self):                            #   [3] c keyid 1/0 down/up (tKey)
        '''
            Thread 3
            Record Keyboard
            Pushes instructions after recording ends
            Resets all pressed keys 
            
        '''
        log(0,"Recording keyboard")

        

        lost_keys=[0]*100
        
        track=time.time()
        events=[]

        def c(event):
            if (not self.stopFlag.is_set()):
                events.append(event)

        if(self.keyboardToggle):
            keyboard.hook(c)
            self.awaitAbort()
            keyboard.unhook(c)
        else:
            self.awaitAbort()

        log(0,"Stopped recording keyboard")

        if(not len(events)):#events are none
            return
        
        for event in events:
            
            if event.event_type=='down': 
                self.instructions[1].append(f"s{round(event.time-track, self.round_precision)}k{event.scan_code},1") 
                track=event.time
                lost_keys[event.scan_code]=1
            elif event.event_type== 'up':
                self.instructions[1].append(f"s{round(event.time-track, self.round_precision)}k{event.scan_code},0") 
                track=event.time
                lost_keys[event.scan_code]=0
                
        for i in range(len(lost_keys)):#close all pressed keys (very important)
            if(lost_keys[i]==1):
                self.instructions[1].append(f"k{i},0") 






class Player(Macro):
    '''
        Plays a macro
            Toggleable mouse and keyboard playback
            Reverse playback
            Playback speed
        TODO:
            Factor sc dim
            implement relative movement
    '''
    def __init__(self, name, keybind, mouseToggle, keyboardToggle, sc_dim, speed, relToggle, reverseToggle):
        super().__init__(name, keybind,mouseToggle, keyboardToggle)

        self.recorded_screen_x=sc_dim[0]
        self.recorded_screen_y=sc_dim[1]
        self.playback_speed=(1/speed)
        self.relToggle=relToggle
        self.reverseToggle=reverseToggle

        self.mouseEndFlag=False
        self.keyEndFlag=False



    def setSpeed(self,speed):
        self.playback_speed=(1/speed)


    def delayOld(self, pausetime):
        '''
            Waits accurately
            Not in use

            Pass: 
                time to sleep
                
        '''
        start_ns=time.perf_counter_ns()
        target_ns=start_ns + int((pausetime*self.playback_speed) * 1_000_000_000)
    
        time.sleep((pausetime*self.playback_speed) * 0.98)

        while time.perf_counter_ns() < target_ns:
            pass
    

    def delay(self, pausetime):
        '''
            Waits less accurately but allows cancel

            Pass: 
                time to sleep
                
        '''
        target_ns=time.perf_counter_ns()+int(pausetime*self.playback_speed*1_000_000_000)

        while True:
            if self.stopFlag.is_set():
                return False
            r=((target_ns-time.perf_counter_ns())/1_000_000_000)

            if r<=0.05:
                break
            time.sleep(0.05)
        r=((target_ns-time.perf_counter_ns())/1_000_000_000)

        if r>0:
            time.sleep(r*0.98)

    
    def setInstruct(self,instructions):
        '''
            Sets instructions from compilation of a file
            Reverses if toggled
            instructions[0] corresponds to mouse 
            instructions[1] corresponds to keyboard
            Pass: 
                list instructions containing tuples representing actions and wait times
                if a tuple is found, the macro will push an action
                if not, a stall is indicated. instead will push a stall command that waits
                for example, [[][(c1,1),s0.5]] 
                located in row 2, macro will push the action 'push key code 1 down, then wait 0.5 seconds'
        '''
        self.instructions.clear()
        self.instructions=[[],[]]

        for r in range(len(instructions)):
            for c in range(len(instructions[r])):

                if not instructions[r][c]:
                    continue

                isT=(isinstance(instructions[r][c],tuple))
                if(isT):
                    if(r==0):      #mouse
                        self.instructions[r].append(lambda m_c=instructions[r][c]:self.mouseAction(*m_c))
                    elif(r==1):           #key
                        self.instructions[r].append(lambda k=instructions[r][c]:self.keyAction(*k))
                else:               #const stall
                    self.instructions[r].append(lambda s=instructions[r][c]:self.delay(s))

        if(self.reverseToggle):
            self.instructions[0].reverse()
            self.instructions[1].reverse()


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
    
        if not i:
            self.mouseEndFlag=True
        else:
            self.keyEndFlag=True

        if(self.mouseEndFlag and self.keyEndFlag):
            self.stopFlag.set()#<<<
            

    def play(self):#running
        '''
            Runs loaded instructions
            clears untoggled
        '''
        self.stopFlag.clear()

        if(not self.mouseToggle):
            self.instructions[0].clear()

        if(not self.keyboardToggle):
            self.instructions[1].clear()

        self.mouseEndFlag=False
        self.keyEndFlag=False

        log(0,f"Begin replay of {self.name}")
        m_cT=threading.Thread(target=lambda:self.useInstruct(0), daemon=True)
        kT=threading.Thread(target=lambda:self.useInstruct(1), daemon=True)
        w=threading.Thread(target=self.awaitAbort, daemon=True)#watches

        m_cT.start()
        kT.start()
        w.start()

        m_cT.join()
        kT.join()
        w.join()

        self.stopFlag.clear()

        log(0,f"Finished running {self.name}")
        

    def flush(self):
        '''
            Supposed to reset all downed keys or mouse actions from a replay

            TODO: make this
        '''
        pass
    

    def mouseAction(self, cmd, args_n, args_n1):#c1,1 (mp)
        '''
            Thread 2
            mouse click
            0 LEFT='left'
            1 RIGHT='right'
            2 MIDDLE='middle'
            3 WHEEL='wheel'
            4 X='x'
            5 X2='x2'
            Pass: 
                type (left or right click), action (up or down)
                ctype 1=left, 0=right
                action 1=down, 0=up
        '''
        if(cmd=='m'):                           #m move(x,y)
            mouse.move(args_n,args_n1,True)

        elif(cmd=='c'):                         #c click(button,type)
            if(args_n==0):          #1=left
                if((args_n1==1 and not self.reverseToggle) or (self.reverseToggle and args_n1==0)):         #1=down
                    mouse.press(mouse.LEFT)
                else:
                    mouse.release(mouse.LEFT)
            elif(args_n==1):        #right
                if((args_n1==1 and not self.reverseToggle) or (self.reverseToggle and args_n1==0)):
                    mouse.press(mouse.RIGHT)
                else:
                    mouse.release(mouse.RIGHT)
            elif(args_n==2):        #middle
                if((args_n1==1 and not self.reverseToggle) or (self.reverseToggle and args_n1==0)):
                    mouse.press(mouse.MIDDLE)
                else:
                    mouse.release(mouse.MIDDLE)
            elif(args_n==3):        #X (side button 1)
                if((args_n1==1 and not self.reverseToggle) or (self.reverseToggle and args_n1==0)):
                    mouse.press(mouse.X)
                else:
                    mouse.release(mouse.X)
            elif(args_n==4):        #X2 (side button 2)
                if((args_n1==1 and not self.reverseToggle) or (self.reverseToggle and args_n1==0)):
                    mouse.press(mouse.X2)
                else:
                    mouse.release(mouse.X2)

        elif(cmd=='w'):             #wheel
            if(args_n1==1):
                mouse.wheel(1)
            else:
                mouse.wheel(-1)     


    def keyAction(self,keyid,action):#c3,1 (key)
        '''
            Thread 3
            Keyboard
            Pass: 
                key code, action (up or down)
                action 1=down, 0=up
            
            TODO: find out why calling keyboard.is_pressed fixes ghost keys
        '''
        if((action==1 and not self.reverseToggle) or (self.reverseToggle  and action==0)):
            keyboard.send(keyid, True, False)
            keyboard.is_pressed(keyid)
        else:
            keyboard.send(keyid, False,True)
        








#Macro end
#
#
#
#
#checking functions







def settingsWriteHelper(fileSettings, settings):
    '''
        Writes data to settings
        Assumes fileSettings is right as declared in main()

        Pass: 
            the path to the file, the data to write
    '''
    
    
    with open(fileSettings,'w') as fileOUT:#replace
        fileOUT.write("record_key_1:")
        fileOUT.write(settings[0])
        fileOUT.write("\nrecord_key_2:")
        fileOUT.write(settings[1])
        fileOUT.write("\nplay_key_1:")
        fileOUT.write(settings[2])
        fileOUT.write("\nplay_key_2:")
        fileOUT.write(settings[3])
        fileOUT.write("\nround_precision:")
        fileOUT.write(str(settings[4]))
        fileOUT.write("\n")
    #oserror or excption


def settingsWrite(where, settings):
    '''
        TODO:
            Real errors
    '''
    settingsWriteHelper(where, settings)

    
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
    
            if("record_key_1" in line and preset_count==0):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("record_key_2" in line and preset_count==1):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("play_key_1" in line and preset_count==2):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1
            if("play_key_2" in line and preset_count==3):
                data_send_list.append(line[line_cont_val_start+1:len(line)-1])
                preset_count+=1   
            if("round_precision" in line and preset_count==4):
                data_send_list.append(int(line[line_cont_val_start+1:len(line)-1]))
                preset_count+=1
            if(preset_count==6):
                raise throw("Too many values listed in settings.txt")
    if(preset_count==0):
        raise Exception
    #value os excpt


def settingsComp(where, data_send_list, DEFAULT_SETTINGS):
    '''
        Attempts to restore defaults if bad value
        TODO:
            Real errors
    '''
    try:
        settingsCompHelper(where, data_send_list)
    except Exception as e:
        log(1,f"Rewriting settings: {e}")
        settingsWrite(where,DEFAULT_SETTINGS)
        log(0,f"Defaults restored")




#settings file end
#
#
#
#macro file start




def fileCompHelper(where, player):
    '''
        Compiles instructions for a macro object
        Pass: 
            directory, existing macro with a name
    '''
    m_dir=f"{where}/{player.retName()}"
    if os.path.isfile(m_dir):
        log(0,f"{player.retName()} located")
    else:
        raise throw(f"{player.retName()}: file does not exist")

    args_n=args_n1=0
    send_index=0
    line_instruction_count=0
    line_cont_end=0
    m_current_alloc=-1
    
    m_data_send_list=[[],[]]
        
    with open(m_dir,"r") as fileIN:
        for line_count, line in enumerate(fileIN, start=1):#for line

            #add screen size here
            
            if(line[1:3]==">>"):#define alloc in macrolist
                m_current_alloc=int(line[0:1])
                if(m_current_alloc>1):
                    raise throw(f"\"{m_current_alloc}>>\" is invalid")
                continue
            
            line_cont_end=line.find(';')
            
            if(line_cont_end or m_current_alloc>-1):#has data, defined alloc
                for i,ch in enumerate(line):#char in line
                    
                    if(ch.isalpha()):#m,c,k,s
                        send_index=i+1
                        while((not line[send_index].isalpha()) and (send_index!=line_cont_end)):send_index+=1
                        try:
                            args_n,args_n1=tuple(map(int, line[i+1:send_index].split(",")))
                            if(ch!='k'):
                                m_data_send_list[m_current_alloc].append((ch,args_n,args_n1))#mouse codes
                            else:
                                m_data_send_list[m_current_alloc].append((args_n,args_n1))#key has no codes

                        except ValueError:
                            m_data_send_list[m_current_alloc].append(float(line[i+1:send_index]))
                        line_instruction_count+=1
            else:
                raise throw(f"{player.retName()}: line {line_count}: Invalid action\n\t >>>{line}")
    #value index os expt
    
    player.setInstruct(m_data_send_list)
    log(0,f"{player.retName()} created with {line_instruction_count} instructions")


def fileComp(where,player):
    '''
        TODO:
            Real errors
    '''
    fileCompHelper(where,player)


def fileWriteHelper(where, recorder):
    '''
        Writes instructions from a macro object
        should be called after macro.recMacro 
        Pass: 
            directory containing macros, existing macro
        
        TODO: check directory
            +Move the file checking to another function
    '''

    m_dir=f"{where}/{recorder.retName()}"
    if os.path.isfile(m_dir):
        log(0,f"{recorder.retName()} located")
    else:
        raise throw(f"{recorder.retName()}: file does not exist")

    m_instr=recorder.retInstruct()
    
    with open(m_dir,'w') as fileOUT:#erase

        #fileOUT.write(f"sc>>{m.retScreenSize()[0]},{m.retScreenSize()[1]}\n")

        for r in range(len(m_instr)):
            if m_instr[r]: #skip if empty
                fileOUT.write(f"{r}>>\n")
                    
                for c in range(len(m_instr[r])):
                            
                    if(isinstance(m_instr[r][c],tuple)):

                        for i in range(len(m_instr[r][c])-1):
                            fileOUT.write(f"{m_instr[r][c][i]},")
                        fileOUT.write(f"{m_instr[r][c][len(m_instr[r][c])-1]}")
                    else:
                        fileOUT.write(m_instr[r][c])
                    
                    if(c==len(m_instr[r])-1):
                        fileOUT.write(';\n')
    
    #os excpt


def fileWrite(where,recorder):
    '''
        TODO:
            Real errors
    '''
    fileWriteHelper(where,recorder)
    log(0,f"Write successful: {recorder.retName()}")


def checkDirHelper(settingsDir,macrosDir,fileSettings,defaultSettings):
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
        settingsWrite(fileSettings,defaultSettings)


def checkDir(settingsDir,macrosDir,fileSettings,defaultSettings):
    try:
        checkDirHelper(settingsDir,macrosDir,fileSettings,defaultSettings)
        log(0,"All directories located")
    except Exception as e:
        log(2,"Directories could not be located")
        sys.exit(1)




#macro file end
#
#
#
#functions start

    
        
    
def createFile():
    '''
        Creates a file with a name the user defines
        currently unused (checkfile)
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
            filePath=os.path.join(dir, fileName)#???
            macroList.append(fileName)
    return macroList

        
def getDir():
    '''
        Gets the current running directory
        Returns: the running directory
    '''
    os.path.dirname(os.path.abspath(__file__))
    current=os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(current)
    return current
    #return os.path.dirname(os.path.abspath(sys.argv[0]))


def getVersion():
    ''' 
        Gets the current version
        Displayed on the ui
    '''
    return 1.2





#checks end
#
#
#
#UI begin






class RunData():
    '''
        Stores all running data for retrieval by ui
        for simplicity purposes
    '''
    def __init__(self,dir,settingsDir,macrosDir,fileSettings,macroList,settingsList, defSettingsList):
        self.macroList=[]
        self.dir=dir
        self.settingsDir=settingsDir
        self.macrosDir=macrosDir
        self.fileSettings=fileSettings
        self.macroList=macroList
        self.settingsList=settingsList
        self.tampered=False
        self.activeMacro=None

        self.screen_x=0
        self.screen_y=0

        self.defaultRecordKey1=defSettingsList[0]
        self.defaultRecordKey2=defSettingsList[1]
        self.defaultPlayKey1=defSettingsList[2]
        self.defaultPlayKey2=defSettingsList[3]
        self.defaultRoundPrecision=defSettingsList[4]

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


    def setScreenDim(self,x,y):
        self.screen_x=x
        self.screen_y=y

    def retScreenDim(self):
        return (self.screen_x,self.screen_y)

    #tampered status set reset get
    def setTampered(self):
        self.tampered=True
    
    def resetTampered(self):
        self.tampered=False

    def retTampered(self):
        return self.tampered

    def saveSettings(self, f_settingsList):
        self.settingsList=f_settingsList
        settingsWrite(self.fileSettings,f_settingsList)


    def setActiveMacro(self, active):
        self.activeMacro=active

    def retActiveMacro(self):
        return self.activeMacro




    
class Base:
    '''
        Base class for the UI
        contains tk settings and the active macro
    '''

    def __init__(self, root, rd):
        self.root=root
        self.root.title(f"GenMacro {getVersion()}")
        self.root.geometry("600x340")
        self.root.configure(bg="#BDBDBD")
        self.active=None
        self.mainColor="#B9DAFF"
        self.rd=rd

        self.space=tk.Frame(self.root)#new
        self.space.pack(fill="both", expand=True)
        
        self.menuMain=MainInterface(self, self.space)
        self.menuMain.place(relwidth=1, relheight=1)
        
        self.menuSettings=SettingsMenu(self, self.space)
        self.menuSettings.place(relwidth=1, relheight=1)

        self.menuAction=ActionMenu(self, self.space)
        self.menuAction.place(relwidth=1,relheight=1)
        
        self.showMain()

        self.rd.setScreenDim(root.winfo_screenwidth(),root.winfo_screenheight())


    def showMain(self):
        self.menuMain.tkraise()
        
    def showSettings(self):
        self.menuSettings.tkraise()

    def showActions(self):
        self.menuAction.tkraise()
        self.menuAction.onShow()

    def updateLog(self,str):
        self.menuMain.log(str)









class MainInterface(tk.Frame):
    '''
        The main menu
        does main menu things
    '''

    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base=base

        frameMain=tk.Frame(self, bg=base.mainColor)
        frameMain.pack(fill="both",padx=20,pady=(10,0))


        #left (from LoadInterface)
        self.fileOptLeft=LoadInterface(base,frameMain,self.onDelete, self.onSelect)
        self.fileOptLeft.pack(side="left",fill="both",expand=True,padx=(0,10))

        #right (file)
        self.frameRight=tk.Frame(frameMain,bg=base.mainColor)
        self.frameRight.pack(side="left",fill="both", pady=(0,0))

        self.activeLabel=tk.Label(self.frameRight,text="Active file: None",bg=base.mainColor,font=("Arial", 14))
        self.activeLabel.pack(pady=(0,0))

        self.m_name=tk.Entry(self.frameRight)
        self.m_name.pack(fill="x",pady=0)

        frameRightOpt=tk.Frame(self.frameRight,bg=base.mainColor)
        frameRightOpt.pack(pady=2)

        tk.Button(frameRightOpt,text="Create",command=self.create).grid(row=0,column=0,padx=5)
        tk.Button(frameRightOpt,text="Ready",command=self.base.showActions).grid(row=0,column=1,padx=5)

        

        #lower
        frameLower=tk.Frame(self,bg=base.mainColor)
        frameLower.pack(fill="x",padx=20,pady=5)

        tk.Button(frameLower,text="Settings",command=self.base.showSettings).pack(side="left")
        tk.Button(frameLower,text="Quit",command=self.base.root.destroy).pack(side="right")

        #console
        frameBottom=tk.Frame(self.base.root)
        frameBottom.pack(padx=1,pady=1)

        self.console=tk.Text(frameBottom, height=6,bg="#FFFFFF")
        self.console.pack(side="bottom")
        self.log(self.base.rd.dir)


    def log(self, message):
        self.console.config(state="normal")
        self.console.insert(tk.END,time.strftime('%H:%M:%S',time.localtime(time.time()))+">"+message+"\n")
        self.console.config(state="disabled")
        self.console.see(tk.END)


    def create(self):
        m_name=self.m_name.get()

        if not m_name:
            self.base.updateLog("No name inputted. Start typing and try again.")
            return

        try:
            checkFile(self.base.rd.retMacrosDir(), m_name)
            self.fileOptLeft.displayMacros()
            self.base.updateLog(f"{m_name} created.")

        except Exception as e:
            self.base.updateLog(f"Cannot create file: {e}")


    def onSelect(self, selected):
        self.base.active=selected
        self.activeLabel.config(text=f"Active file: {selected}")
        #self.base.menuAction.activeLabel.config(text=f"Active file: {selected}")


    def onDelete(self, selected):
        if self.base.active == selected:
            self.base.active=None
            self.activeLabel.config(text="Active file: None")
            #self.base.menuAction.activeLabel.config(text="Active file: None")








class SettingsMenu(tk.Frame):
    '''
        Responsible for handling the users settings:
            Keybind for record
            Keybind for start
            Default round precision
        
    '''
    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base=base
        self.popupActive=False
        tk.Label(self, text="Settings", bg=self.base.mainColor, font=("Arial", 14)).pack(pady=10)#first access

        frameMain=tk.Frame(self,bg=self.base.mainColor)
        frameMain.pack(pady=5)

        tk.Label(frameMain, font=("Arial",10),text="Record toggle 1", bg=self.base.mainColor).grid(row=0,column=0,padx=10,pady=2)
        tk.Label(frameMain, font=("Arial",10),text="Record toggle 2", bg=self.base.mainColor).grid(row=1,column=0,padx=10,pady=2)

        tk.Label(frameMain, font=("Arial",10),text="Play toggle 1", bg=self.base.mainColor).grid(row=0,column=3,padx=10,pady=2)
        tk.Label(frameMain, font=("Arial",10),text="Play toggle 2", bg=self.base.mainColor).grid(row=1,column=3,padx=10,pady=2)
        
        tk.Button(frameMain, font=("Arial",10),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(0)).grid(row=0,column=1,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",10),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(1)).grid(row=1,column=1,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",10),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(2)).grid(row=0,column=4,padx=10,pady=2)
        tk.Button(frameMain, font=("Arial",10),text="Set", bg=self.base.mainColor, command=lambda: self.setKeybind(3)).grid(row=1,column=4,padx=10,pady=2)

        self.recordKey1=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[0]}",font=("Arial", 12), bg=self.base.mainColor)
        self.recordKey1.grid(row=0,column=2,padx=10,pady=0,sticky="nsew")#<<<<<<<<<<
        self.recordKey2=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[1]}",font=("Arial", 12), bg=self.base.mainColor)
        self.recordKey2.grid(row=1,column=2,padx=10,pady=0,sticky="nsew")

        self.playKey1=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[2]}",font=("Arial", 12), bg=self.base.mainColor)
        self.playKey1.grid(row=0,column=5,padx=10,pady=0,sticky="nsew")
        self.playKey2=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[3]}",font=("Arial", 12), bg=self.base.mainColor)
        self.playKey2.grid(row=1,column=5,padx=10,pady=0,sticky="nsew")

        frameLower=tk.Frame(self,bg=base.mainColor)
        frameLower.pack(fill="x",padx=20,pady=5)

        self.roundLabel=tk.Label(frameLower,bg=base.mainColor,font=("Arial", 8))
        self.roundLabel.pack(pady=(0, 0))
        
        self.roundSlider=tk.Scale(frameLower,from_=1,to=12,resolution=1,orient=tk.HORIZONTAL,showvalue=False,
                                    command=self.update,bg=base.mainColor,highlightthickness=0,width=11,length=300,sliderlength=20)
        self.roundSlider.set(self.base.rd.retSettingsList()[4])
        self.roundSlider.pack(pady=(0,0))

        tk.Button(frameLower, text="Reset defaults", command=self.resetDefaults).pack(side="right")
        tk.Button(frameLower,text="Back", command=lambda: self.back()).pack(side="left")
        



    def resetDefaults(self):
        if(not self.popupActive):
            self.base.rd.setTampered()
            self.recordKey1.config(text=self.base.rd.defaultRecordKey1)
            self.recordKey2.config(text=self.base.rd.defaultRecordKey2)
            self.base.menuAction.recordToggleDisplay.config(text=f"{self.base.rd.defaultRecordKey1}+{self.base.rd.defaultRecordKey2}")
            self.playKey1.config(text=self.base.rd.defaultPlayKey1)
            self.playKey2.config(text=self.base.rd.defaultPlayKey2)
            self.roundSlider.set(self.base.rd.defaultRoundPrecision)
            self.base.menuAction.recordToggleDisplay.config(text=f"{self.base.rd.defaultPlayKey1}+{self.base.rd.defaultPlayKey2}")
            


    def update(self, value):
        self.base.rd.setTampered()
        self.roundLabel.config(text=f"Default Round Precision: ({value}) digits")
        


    def set(self):#assume tampered status
        self.base.rd.saveSettings([self.recordKey1["text"],self.recordKey2["text"],
                                    self.playKey1["text"],self.playKey2["text"],self.roundSlider.get()])
        self.base.rd.resetTampered()
        self.base.updateLog("Changes saved")


    def back(self):
        if(not self.popupActive):
            if(self.base.rd.retTampered()):#send, assume checked
                self.set()
            self.base.showMain()


    def setKeybind(self,n):
        #can otherwise mess with .config(state=...)
        if(not self.popupActive):
            self.base.rd.setTampered()
            self.promptKey(n)
            
    
    def promptKey(self,n):
        #first out
        self.popupActive=True
        popup=tk.Toplevel(self.base.root)
        popup.attributes("-topmost", True)
        popup.title("genmacro")
        popup.geometry("300x100")
        
        label=tk.Label(popup, text="Enter a key...", font=("Arial", 14))
        label.pack(pady=20)

        popup.bind("<<KeyPressReceived>>", lambda a: popup.destroy())

        t=threading.Thread(target=self.setAKey, args=(popup,n), daemon=True)
        t.start()
        

    def setAKey(self,popup,n):
        '''
            Thread 1
            Get key
            Will not allow duplicate keybinds
            
        '''

        key=str(keyboard.read_key())#<<<
        
        recTempList=[]
        playTempList=[]

        duplicateToggle=False
        duplicateSelf=False

        if(n<2):
            playTempList=sorted([self.playKey1["text"],self.playKey2["text"]])

            if(n==0):
                recTempList=sorted([key,self.recordKey2["text"]])
                if(key!=self.recordKey2["text"]):
                    if(recTempList!=playTempList):
                        self.recordKey1.config(text=key.lower())
                        self.base.menuAction.recordToggleDisplay.config(text=f"{key}+{self.recordKey2["text"]}")
                    else:
                        duplicateToggle=True
                else:
                    duplicateSelf=True
            elif(n==1):
                recTempList=sorted([key,self.recordKey1["text"]])
                if(key!=self.recordKey1["text"]):
                    if(recTempList!=playTempList):
                        self.recordKey2.config(text=key.lower())
                        self.base.menuAction.recordToggleDisplay.config(text=f"{self.recordKey1["text"]}+{key}")
                    else:
                        duplicateToggle=True
                else:
                    duplicateSelf=True
        else:
            recTempList=sorted([self.recordKey1["text"],self.recordKey2["text"]])

            if(n==2):
                playTempList=sorted([key,self.playKey2["text"]])
                if(key!=self.playKey2["text"]):
                    if(recTempList!=playTempList):
                        self.playKey1.config(text=key.lower())
                        self.base.menuAction.playToggleDisplay.config(text=f"{key}+{self.playKey2["text"]}")
                    else:
                        duplicateToggle=True
                else:
                    duplicateSelf=True
            elif(n==3):
                playTempList=sorted([key,self.playKey1["text"]])
                if(key!=self.playKey1["text"]):
                    if(recTempList!=playTempList):
                        self.playKey2.config(text=key.lower())
                        self.base.menuAction.playToggleDisplay.config(text=f"{self.playKey1["text"]}+{key}")
                    else:
                        duplicateToggle=True
                else:
                    duplicateSelf=True


        if(duplicateToggle):
            self.base.updateLog(f"Cannot have duplicate toggle keybinds: {recTempList} and {playTempList}")
        elif(duplicateSelf):
            self.base.updateLog(f"Cannot have duplicate keys: {key}")

        popup.event_generate("<<KeyPressReceived>>", when="tail")
        self.popupActive=False






class LoadInterface(tk.Frame):
    '''
        The moveable interface to replace LoadMenu
        
    '''
    def __init__(self, base, parent, onDelete, onSelect):
        super().__init__(parent, bg=base.mainColor)
        self.base=base
        self.selected=None
        self.onSelect=onSelect
        self.onDelete=onDelete

        #tk.Label(self,text="Select an existing macro",bg=base.mainColor,font=("Arial", 14)).pack(anchor="center")
        tk.Label(self,text="Select an existing macro",bg=base.mainColor,font=("Arial", 14)).pack(anchor="center", pady=(0, 0))

        self.listbox=tk.Listbox(self, height=8)
        self.listbox.pack(fill="x", pady=0)

        frameButton=tk.Frame(self, bg=base.mainColor)
        frameButton.pack(pady=2)

        tk.Button(frameButton,text="Select",command=self.select).grid(row=0,column=0,padx=5)
        tk.Button(frameButton,text="Delete",command=self.delete).grid(row=0,column=1,padx=5)

        self.displayMacros()

        
    def select(self):
        opt=self.listbox.curselection()

        if not opt:
            self.base.updateLog('Nothing to select. Click on an existing file and try again.')
            return

        self.selected=self.listbox.get(opt[0])
        self.onSelect(self.selected)


    def delete(self):
        opt=self.listbox.curselection()

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




class ActionMenu(tk.Frame):
    '''
        Responsible for event handling
            Listens for keybinds
            Records and runs macros

    '''
    def __init__(self, base, parent):
        super().__init__(parent, bg=base.mainColor)
        self.base=base

        #toggle variables
        self.mouseVar=tk.BooleanVar(value=True)
        self.keyboardVar=tk.BooleanVar(value=True)
        self.relVar=tk.BooleanVar(value=False)
        self.reverseVar=tk.BooleanVar(value=False)

        self.mouseCB=True
        self.keyboardCB=True
        self.relCB=False
        self.reverseCB=False

        #running variables
        self.recHotkey=None
        self.playHotkey=None

        self.active=None
        self.m_name=None
        self.writeFlag=True

        self.recCheck=False
        self.runCheck=False

        self.playbackSpeed=1.0
        self.rp=6

        self.tR=None
        self.tP=None

        #top
        self.activeLabel=tk.Label(self, text="Active file: None", bg=self.base.mainColor, font=("Arial", 14))
        self.activeLabel.pack(pady=(10,0))#first access

        frameMain=tk.Frame(self,bg=self.base.mainColor)
        frameMain.pack(pady=(0,0))

        tk.Label(frameMain, text="Record", bg=self.base.mainColor, font=("Arial", 14)).grid(row=0,column=0,padx=80,pady=(0,0))
        tk.Label(frameMain, text="Replay", bg=self.base.mainColor, font=("Arial", 14)).grid(row=0,column=1,padx=80,pady=(0,0))

        self.recordToggleDisplay=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}", bg=self.base.mainColor,font=("Arial", 14))
        self.recordToggleDisplay.grid(row=1,column=0,padx=80)
        self.playToggleDisplay=tk.Label(frameMain, text=f"{self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}", bg=self.base.mainColor,font=("Arial", 14))
        self.playToggleDisplay.grid(row=1,column=1,padx=80)


        #quick settings
        frameLower=tk.Frame(self,bg=base.mainColor)
        frameLower.pack(fill="x",padx=20,pady=5)

        self.frameLeft=tk.Frame(frameLower,bg=base.mainColor)
        self.frameLeft.pack(side="left",padx=(0, 10))

        self.frameRight=tk.Frame(frameLower,bg=base.mainColor)
        self.frameRight.pack(side="left", padx=(20,0),pady=(0,0))


        #checkbox (right)
        tk.Checkbutton(self.frameRight,text="Mouse",variable=self.mouseVar,command=self.toggleMouse,bg=base.mainColor).pack(anchor="w",pady=(0,0))
        tk.Checkbutton(self.frameRight,text="Keyboard",variable=self.keyboardVar,command=self.toggleKeyboard,bg=base.mainColor).pack(anchor="w", pady=(0,0))
        tk.Checkbutton(self.frameRight,text="Relative movement",variable=self.relVar,command=self.toggleRel,bg=base.mainColor).pack(anchor="w", pady=(0,0))
        tk.Checkbutton(self.frameRight,text="Reverse playback",variable=self.reverseVar,command=self.toggleReverse,bg=base.mainColor).pack(anchor="w", pady=(0,0))

                
        #slider (right)
        frameSpeed=tk.Frame(self.frameLeft,bg=base.mainColor)
        frameSpeed.pack(side="left",padx=(40,20), pady=(0,0))

        #slider speed
        self.speedLabel=tk.Label(frameSpeed,bg=base.mainColor,font=("Arial", 8))
        self.speedLabel.pack(pady=(0, 0))

        self.speedSlider=tk.Scale(frameSpeed,from_=0.2,to=10.0,resolution=0.2,orient=tk.HORIZONTAL,showvalue=False,
                                    command=self.updateSpeed,bg=base.mainColor,highlightthickness=0,width=11,length=233,sliderlength=20)
        self.speedSlider.set(1.0)
        self.speedSlider.pack(fill="x", pady=(0,0))

        #slider rp
        self.rpLabel=tk.Label(frameSpeed,bg=base.mainColor,font=("Arial", 8))
        self.rpLabel.pack(pady=(0, 0))

        self.rpSlider=tk.Scale(frameSpeed,from_=1,to=12,resolution=1,orient=tk.HORIZONTAL,showvalue=False,
                                    command=self.updateRp,bg=base.mainColor,highlightthickness=0,width=11,length=233,sliderlength=20)
        self.rpSlider.set(self.base.rd.retSettingsList()[4])
        self.rpSlider.pack(fill="x", pady=(0,0))

        #button
        frameBottom=tk.Frame(self,bg=base.mainColor)
        frameBottom.pack(fill="x",padx=20,pady=5)

        tk.Button(frameBottom, text="Back", command=lambda: self.back()).pack(side="left")


    def toggleMouse(self):
        self.mouseCB=self.mouseVar.get()
        self.writeFlag=True


    def toggleKeyboard(self):
        self.keyboardCB=self.keyboardVar.get()
        self.writeFlag=True


    def toggleRel(self):
        self.relCB=self.relVar.get()
        self.writeFlag=True


    def toggleReverse(self):
        self.reverseCB=self.reverseVar.get()
        self.writeFlag=True


    def updateSpeed(self, value):
        if(float(value)>5):
            self.speedLabel.config(text=f"Playback Speed: {value}x (Unstable)")
        else:
            self.speedLabel.config(text=f"Playback Speed: {value}x")
        self.playbackSpeed=float(value)
        self.writeFlag=True


    def updateRp(self, value):
        self.rpLabel.config(text=f"Round Precision: ({value}) digits")
        self.rp=int(value)
        self.writeFlag=True


    def linkHotkeys(self):
        self.tR=threading.Thread(target=self.recordingStart,daemon=True)
        self.tP=threading.Thread(target=self.runningStart,daemon=True)
        self.recHotkey=keyboard.add_hotkey(f"{self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}",self.tR.start)
        self.playHotkey=keyboard.add_hotkey(f"{self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}",self.tP.start)
                
        
    def unlinkHotkeys(self):
        if(self.recHotkey is not None and self.playHotkey is not None):
            keyboard.remove_hotkey(self.recHotkey)
            keyboard.remove_hotkey(self.playHotkey)
            self.recHotkey=None
            self.playHotkey=None


    def waitForRelease(self, keybind):
        while any(keyboard.is_pressed(key) for key in keybind.split("+")):
            time.sleep(0.05)


    def onShow(self):
        '''
            Called in base after shown
        '''
        self.writeFlag=True
        self.m_name=self.base.active#for the purposes of tk freaking tf out
        self.activeLabel.config(text=f"Active file: {self.m_name}")
        
        if(self.m_name is not None):
            self.linkHotkeys()
        else:
            self.base.updateLog("Create or choose a file to run actions")


    def recordingStart(self):#create Recorder
        '''
            Thread 1
            Records and writes
        '''
        self.recCheck=True
        self.unlinkHotkeys()
        self.waitForRelease(f"{self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}")
        self.active=Recorder(self.m_name,f"{self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}",self.mouseCB,self.keyboardCB,self.rp,(self.base.rd.retScreenDim()))#<<<
        self.active.record()
        
        self.waitForRelease(f"{self.base.rd.retSettingsList()[0]}+{self.base.rd.retSettingsList()[1]}")
        self.writeFlag=True
        fileWrite(self.base.rd.retMacrosDir(),self.active)#<<<
        self.linkHotkeys()
        


    def runningStart(self):#run Player
        '''
            Thread 1
            Compiles and plays
        '''
        self.runCheck=True
        self.unlinkHotkeys()
        self.waitForRelease(f"{self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}")

        if(self.writeFlag or not isinstance(self.active, Player)):
            self.active=Player(self.m_name,f"{self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}",self.mouseCB,self.keyboardCB,(self.base.rd.retScreenDim())
                               ,self.playbackSpeed,self.relCB,self.reverseCB)#<<<
            fileComp(self.base.rd.retMacrosDir(),self.active)
            self.writeFlag=False
        self.active.play()

        self.waitForRelease(f"{self.base.rd.retSettingsList()[2]}+{self.base.rd.retSettingsList()[3]}")
        self.linkHotkeys()
        

    def back(self):
        self.unlinkHotkeys()
        
        if(self.active is not None):
            self.active.stopFlag.set()
            self.writeFlag=True

        self.recCheck=False
        self.runCheck=False
        self.base.showMain()






#UI end
#
#
#
#main begin




def main():
    #os.path.dirname(os.path.abspath(__file__))
    #current=os.path.dirname(os.path.abspath(sys.argv[0]))
    #os.chdir(current)
    # log(0,f"Running Directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    #directories and files
    DEF_RECORD_TOGGLE_1='ctrl'
    DEF_RECORD_TOGGLE_2='shift'
    DEF_PLAY_TOGGLE_1='ctrl'
    DEF_PLAY_TOGGLE_2='alt'
    DEF_ROUND_PRECISION=6
    DEF_SETTINGS_LIST=[DEF_RECORD_TOGGLE_1,DEF_RECORD_TOGGLE_2,
                        DEF_PLAY_TOGGLE_1,DEF_PLAY_TOGGLE_2, DEF_ROUND_PRECISION]
    
    current=getDir()
    settingsDir=f"{current}\\settings"
    macrosDir =f"{current}\\macros"
    fileSettings =f"{settingsDir}\\settings.txt"
    macroList=[]
    settingsList=[]

    #init
    checkDir(settingsDir,macrosDir,fileSettings,DEF_SETTINGS_LIST)
    settingsComp(fileSettings,settingsList, DEF_SETTINGS_LIST)#<<<
    log(0,"All file checks passed")
    rd=RunData(current,settingsDir,macrosDir,fileSettings,macroList,settingsList,DEF_SETTINGS_LIST)

    #ui
    root=tk.Tk()
    windll.shcore.SetProcessDpiAwareness(1)#for blurry text in widget 
    Base(root, rd)

    log(0,"Starting UI")
    root.mainloop()#<<<

        
if __name__=='__main__':
    main()
    log(0,"End")



'''



'''