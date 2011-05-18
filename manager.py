''' taken from http://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python
and modified to fit my needs more. less useful, more specific '''

from tempfile import mkstemp
from shutil import move
from os import remove, close

def replace(file, str):
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(file)
    for line in old_file:
        if line.strip() == str:
            continue
        else:
            new_file.write(line)
    #close temp file
    new_file.close()
    close(fh)
    old_file.close()
    #Remove original file
    remove(file)
    #Move new file
    move(abs_path, file)
    return abs_path
	
'''
Created on Mar 11, 2011

@author: Daniel Hwang
@version: 0.1
@file: manager.py
@description: manages (creates and refreshes) trapyhook objects
'''

import os
import sys
import hook
import re

CONF_FILE = 'inc/trapy.conf'

class trapymanager(object):
    ''' rss trapyhook management object '''
    
    def __init__ (self):
        ''' init should be called once and only once '''
        self.cwd = os.getcwd()
        self.list = []
        self.map = {'Group': 'title', 'Keyword': 'title', 'Format': 'format'}
        self.entry_re = re.compile('#([0-9]+)#(.+)$')
		
        if os.path.exists(CONF_FILE):
            # load up trapy.conf file, grab contents from it
            try:
                print 'opening %s file...\n'%(CONF_FILE)
                self.file = open(CONF_FILE, 'r+')
                for line in self.file.readlines():
                    # read in all .conf files and load them up, preparing for polling
                    self.list.append(line.strip())
            except Exception, e:
                sys.exit(e)
        else:
            try:
                # TODO: should add something to create the inc folder if necessary? Naw.
                print 'creating %s file...\n'%(CONF_FILE)
                # otherwise, create one
                self.file = open(CONF_FILE, 'w+')
            except Exception, e:
                sys.exit(e)
            
    def __del__ (self):
        ''' called before the trapymanager object is deleted '''
        if self.file:
            self.file.close()
    
    def add (self, url, name, keywords):
        ''' passes through data after a bit of sanitization
        this should be synchronous'''
        print 'adding %s to feedlist...\n'%(name)
        kw = []
        for k,v in keywords:
            if k == 'Group':
                v = '[' + v + ']'
            kw.append((self.map[k], v))
        # 'Title': 'Madoka' would be generated by Keyword => 'Madoka'
        # 'Title': '[Nutbladder]' would be generated by Sub Group => 'Nutbladder'
        # 'Format': 'mkv' would be generated by Format => 'mkv'
        
        h = hook.trapyhook(url.strip(), name.strip(), kw)
        if h != -1:
            self.file.write(name.lower().strip() + '\n')
            self.list.append(name.lower().strip())
            return 1
        return -1

    def delete (self, name, rem = False):
        ''' deletes a specified trapyhook object, if rem is True, also remove the .conf file 
        this should not be asynchronous... should be mutex with refresh and add '''
        name = name.lower().strip()
        print 'deleting %s from the feedlist...\n'%(name)
        self.file.close()
        replace(CONF_FILE, name)
        self.file = open(CONF_FILE, 'r+')
        self.list = []
        for line in self.file.readlines():
            # read in all .conf files and load them up, preparing for polling
            self.list.append(line.strip())
    
        if rem:
            print 'deleting %s.conf...\n'%(name)
            if os.path.exists(name + '.conf'):
                os.remove(name + '.conf')
        return 1
        
    def deleteall (self, rem = False):
        ''' should be synchronous, deletes the base config file and all associated trapyhook conf files '''
        self.file.close()
        if os.path.exists(CONF_FILE):
            print 'deleting %s...\n'%(CONF_FILE)
            os.remove(CONF_FILE)
        
        if rem:
            for each in self.list:
                if os.path.exists(each + '.conf'):
                    print 'deleting %s.conf...\n'%(each)
                    os.remove(each + '.conf')
        try:
            print 'creating %s file...\n'%(CONF_FILE)
            # otherwise, create one
            self.file = open(CONF_FILE, 'w+')
            self.list = []
        except Exception, e:
            sys.exit(e)
        return 1
        
    def display (self, name):
        ''' displays all values found for a specified trapyhook
        this should not be asynchronous '''
        if os.path.exists(name + '.conf'):
            file = open(name + '.conf')
        
        try:
            print '\ndisplaying all entries for %s.conf'%(name)
            c = 0
            for line in file:
                match = self.entry_re.match(line.strip())
                if match:
                    data = eval(match.group(2))
                    c += 1
                    print '%d) %s\n\tlink: %s'%(c, data['title'], data['link'])
            print '%d entries found'%(c)
        except Exception, e:
            sys.exit(e)
        return 1
        
    def displayall (self):
        ''' displays all values found for all trapyhooks this should not be asynchronous '''
        print 'displaying all entries for all trapyhooks'
        for each in self.list:
            self.display(each)
        return 1
        
    def edit (self, name):
        ''' allows the user to edit various fields in the specified configuration file '''
        return 0
        
    def getlist (self):
        ''' used to display to the user all trapyhooks currently loaded '''
        return self.list
        
    def refresh (self):
        ''' refreshes all queued conf files. calls to trapyhook.py should be asynchronous
        or should this function call be asynchronous... actually, all function calls by the manager
        should be asynchronous
        see: http://stackoverflow.com/questions/1239035/asynchronous-method-call-in-python
        and: http://docs.python.org/library/multiprocessing.html#module-multiprocessing '''
        print 'refreshing %d feed(s)...\n'%(len(self.list))
        return hook.trapyhook.refresh(self.list)
 
    @staticmethod
    def refresh_poll ():
        ''' does a full refresh, rereads the trapy.conf file and grabs the lines '''
        list = []
        if os.path.exists(CONF_FILE):
            # load up trapy.conf file, grab contents from it
            try:
                #print 'opening trapy.conf file...\n'
                file = open(CONF_FILE, 'r')
                for line in file.readlines():
                    # read in all .conf files and load them up, preparing for polling
                    list.append(line.strip())
                #print 'refreshing %d feed(s)...\n'%(len(list))
                return hook.trapyhook.refresh(list, verbose = False)
            except Exception, e:
                sys.exit(e)
        return (None, 0)
        
if __name__ == '__main__':
    list = []
    list.append(('Keyword', 'Madoka'))
    list.append(('Group', 'Nutbladder'))
    list.append(('Format', 'mkv'))
    m = trapymanager()
    #m.delete('Madoka', rem = True)
    #m.add('http://tokyotosho.info/rss.php?filter=1&zwnj=0', 'madokanutbladder', list)