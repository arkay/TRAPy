'''
Created on Mar 14, 2011

@author: Daniel Hwang
@version: 0.1
@file: cmdline.py
@description: command line interface for the trapy modules
'''
import argparse
import sys
from multiprocessing import Pool


# TODO:
# change so only 1 process is created
# change so the pyqt4 object is owned by the main function
# change to allow editing files
# add functionality for automatic download

# string constants
INIT_1 = 'initializing commandline interface for [T]okyoTosho[R]SS[A]synchronous[Py]thon command module...'
INIT_2 = 'trapymanager loaded successfully'
INIT_3 = 'trapyhook loaded successfully'
INIT_4 = 'all modules loaded successfully.\nstarting trapymanager...\n'
INIT_5 = 'process pool created successfully\n'
PROMPT = '\n(a)dd a trapyhook, (d)elete a trapyhook, (D)elete all trapyhooks,\nd(i)splay values from a trapyhook, d(I)splay values from all trapyhooks,\n(r)efresh all trapyhooks, e(x)it command line interface'
ADD_PROMPT_1 = 'URL to RSS feed (required, leave blank for default [TokyoToshokan]): '
ADD_PROMPT_2 = 'name (must be unique): '
ADD_PROMPT_3 = 'keyword(s) (separate values with a comma \',\'): '
ADD_PROMPT_4 = 'group (leave blank if you do not care): '
ADD_PROMPT_5 = 'format (leave blank if you do not care): '
BAD_VAL = 'invalid input'
DELETE_PROMPT_1 = 'which trapyhook do you want to delete? (leave blank to return)\n%s'
DELETE_PROMPT_2 = 'do you also want to delete the %s.conf file? (y/n): '
DELETE_NONE = 'no hooks to delete'
DELETE_ALL_PROMPT = 'are you sure you want to delete all hooks? (y/n): '
DISPLAY_PROMPT = 'which trapyhook do you want to display? (leave blank to return)\n%s'
DISPLAY_NONE = 'no hooks to display'
DISPLAY_ALL_PROMPT = ''
EXIT_PROMPT_1 = 'cleaning up objects...\n'
EXIT_PROMPT_2 = 'exiting commandline interface...\n'
REFRESH_PROMPT = ''

def poll (man, rate):
    ''' asynchronously calls man.refresh() every rate seconds '''
    try:
        import time
        import manager
        import hook
        
        import sys
        from PyQt4 import QtGui, QtCore
        
        class TRAPyQtSysTrayIcon (QtGui.QSystemTrayIcon):
            def __init__ (self, icon, parent = None):
                super(TRAPyQtSysTrayIcon, self).__init__(icon, parent)
                self.url = None
                self.connect(self, QtCore.SIGNAL('messageClicked()'), self.openBrowser)
            
            def getUrl (self):
                return self.url
                
            def setUrl (self, url):
                self.url = url
            
            def openBrowser (self):
                print 'kawashita yakusoku'
                if self.url != None:
                    import webbrowser
                    webbrowser.open(self.url, new = 2, autoraise = True)
        
        app = QtGui.QApplication([])
        qt = TRAPyQtSysTrayIcon(icon = QtGui.QIcon('inc/tomoyoicon.png'))
        qt.setToolTip('TRAPy Polling Process (%ds)'%(rate)) 
        qt.show()
        
        #qt.setUrl('http://google.com')
        #qt.showMessage('title', 'testingtesting', 0, 100000)
        
        #qt.emit(QtCore.SIGNAL('messageClicked()'))
        
        while (True):
            time.sleep(rate)
            res = man.refresh_poll()
            if res != None and len(res) > 0:
                for each in res:
                    # right now only shows one at a time, assumes it only finds one at a time. generally okay but not always
                    qt.setUrl(each['link'])
                    qt.showMessage('Torrent found: %s'%(each['title']), 'Link: %s'%(each['link']), 0, 60000)
                    print '\n%s\n\tlink: %s'%(each['title'], each['link'])
                print '\n' + PROMPT + '\n>> ',
    except Exception, e:
        print e
        sys.exit(1)

if __name__ == "__main__":
    ''' command line interface, allows for addition, deletion, refresh, and (display) '''
    rate = 600
    # command line argument parser
    try:
        parser = argparse.ArgumentParser(description = 'command line interface for the trapy module')
        parser.add_argument('-r', '--rate', type = int, help = 'the rate (in seconds) to poll the trapyhook objects')
        parsed = parser.parse_args()
        if parsed.rate:
            rate = parsed.rate
    except Exception, e:
        sys.exit(e)
    
    try:
        pool = man = None
        print INIT_1
        import manager
        print INIT_2
        import hook
        print INIT_3
        import time
        c = ['a', 'd', 'D', 'i', 'I', 'r', 'x']
        # any other module loads go here
        print INIT_4
        pool = Pool(1)
        print INIT_5
        time.sleep(1)
        # load manager object
        man = manager.trapymanager()
        # start polling
        result = pool.apply_async(poll, (man, rate))
        time.sleep(1)
        # for explicit calls to refresh, do not notify
        man.refresh()
        
        while True:
            print PROMPT
            val = raw_input(">> ")
            # bad input
            if val not in c:
                print BAD_VAL
                continue
            
            if val == 'x':
                print EXIT_PROMPT_1
                # any other bookkeeping goes here
                pool.terminate()
                del pool
                del man
                print EXIT_PROMPT_2
                break
            elif val == 'a':
                # remember to sanatize any incoming data~
                url = raw_input(ADD_PROMPT_1).strip()
                if len(url) == 0:
                    url = 'http://tokyotosho.info/rss.php?filter=1&zwnj=0'
                name = raw_input(ADD_PROMPT_2).strip()
                list = []
                kw = raw_input(ADD_PROMPT_3).strip().split(',')
                for v in kw:
                    list.append(('Keyword', v.strip()))
                gr = raw_input(ADD_PROMPT_4).strip()
                if len(gr) > 0:
                    list.append(('Group', gr))
                fm = raw_input(ADD_PROMPT_5).strip()
                if len(fm) > 0:
                    list.append(('Format', fm.lower()))
                man.add(url, name, list)
            elif val == 'd':
                # delete
                l = man.getlist()
                str = ""
                if len(l) == 0:
                    print DELETE_NONE
                    continue
                for each in l:
                    str += each.strip() + " "
                
                # loop guard
                a = 0
                while a == 0:
                    print DELETE_PROMPT_1%(str)
                    temp = raw_input(">> ").strip().lower()
                    if temp == '':
                        break
                    if temp in l:
                        temp_2 = raw_input(DELETE_PROMPT_2%(temp)).strip().lower()
                        print '\n'
                        if temp_2 == 'y':
                            man.delete(temp, rem = True)
                        else:
                            man.delete(temp, rem = False)
                        a = 1
                del l
            elif val == 'D':
                # delete all
                temp = raw_input(DELETE_ALL_PROMPT).strip().lower()
                if temp == 'y':
                    # delete config files also
                    man.deleteall(rem = True)
            elif val == 'i':
                # display
                l = man.getlist()
                str = ""
                if len(l) == 0:
                    print DISPLAY_NONE
                    continue
                for each in l:
                    str += each.strip() + " "
                
                # loop guard
                a = 0
                while a == 0:
                    print DISPLAY_PROMPT%(str)
                    temp = raw_input(">> ").strip().lower()
                    if temp == '':
                        break
                    if temp in l:
                        man.display(temp)
                        a = 1
            elif val == 'I':
                # display all
                print DISPLAY_ALL_PROMPT
                man.displayall()
            elif val == 'r':
                # refresh
                print REFRESH_PROMPT
                man.refresh()
    except Exception, e:
        if pool != None:
            pool.terminate()
            del pool
        if man != None:
            del man
        sys.exit(e)