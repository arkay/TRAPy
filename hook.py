'''
Created on Mar 9, 2011

@author: Daniel Hwang
@version: 0.1
@file: hook.py
@description: 
'''

import os
import re
import sys
import urllib2
from datetime import datetime, timedelta
from xml.etree import ElementTree as etree

class trapyhook(object):
    '''rss feed xml parser object'''

    def __init__ (self, url, name, list):
        ''' init method for a trapyhook object, sets up initial configuration object '''
        if url == None or name == None:
            sys.exit('url or name not specified, exiting application')
        # should do some checking for a valid rss url here
            
        name = name.lower().replace(' ','')
        try:
            if os.path.exists(name + '.conf'):
                raise Exception('file \'%s.conf\' already exists'%(name))
            print 'creating \'%s\'...'%(name) 
            conf = open(name + '.conf', 'w')
        except Exception, e:
            sys.exit(e)
                
        self.conf = conf
            
        # lower everything in the keyword dictionary
        # do some data sanitation
        keywords = [(k.lower(), v.lower()) for (k,v) in list]
            
        try:
            print 'opening \'%s\'...'%(url)
            req = urllib2.Request(url)
            file = urllib2.urlopen(req)
            (ret, count) = self.parser(file, keywords)
            if ret != None:
                print '%d matches found.'%(count)
                self.ret = ret
                self.name = name
                self.url = url
                self.keywords = keywords
                try:
                    print 'writing configuration file...'
                    # write confs to the log file
                    self.conf.write('###NAME###%s\n'%(self.name))
                    '''
                    self.conf.write('###LASTACCESS###%s\n'%(datetime.strftime(datetime.today(),'%Y-%m-%d %H:%M:%S')))
                    '''
                    self.conf.write('###URL###%s\n'%(self.url))
                    self.conf.write('###KEYWORDS###%s\n'%(self.keywords))
                    c = 0
                    # write any return values
                    for i in ret:
                        self.conf.write('#%d#%s\n'%(c,i))
                        c += 1
                    conf.close()   
                    print 'writing complete, %s.conf created successfully.\n'%(self.name)
                except Exception, e:
                    raise e
            else:
                raise Exception('failed parsing, exiting application')
        except Exception, e:
            conf.close()
            sys.exit(e)

    @staticmethod
    def parser(file, keywords, last = None, verbose = True):
        ''' parses a specified rss file descriptor for keywords, initial configuration passes in file and keywords
        subsequent refreshes pass in the file, keyword, and last access time '''
        try:
            doc = etree.parse(file)
        except Exception, e:
            #sys.exit(e)
            if verbose:
                print e
            return -1
        
        if doc.getroot().tag != 'rss':
            return (None, -1)
        
        if verbose:
            print 'begin parsing'
        months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        pubdate_re = re.compile('(?:[a-zA-Z]*) (?P<date>[0-9]*) (?P<month>[a-zA-Z]*) (?P<year>[0-9]*) (?P<hour>[0-9]*):(?P<minute>[0-9]*):(?P<second>[0-9]*) GMT')
        items = []
        try:
            for item in doc.iter('item'):
                # parser through sub nodes: category, title, link, description, guid, pubDate
                if last:
                    pubdate = item.find('pubDate').text
                    # seems like we have to use a fucking regex for this shit...
                    match = pubdate_re.search(pubdate)
                    pubd_dt = datetime(int(match.group('year')), months[match.group('month')], int(match.group('date')), int(match.group('hour')), int(match.group('minute')), int(match.group('second')))
                    
                    if pubd_dt <= last + timedelta(hours = 8):
                        # if published earlier than the last access time stop processing
                        break
                        
                ins = True
                for (k,v) in keywords:
                    # reverse logic, all key => value pairs MUST be matched, otherwise ignore item
                    if k == 'format':
                        text = item.find('title').text
                        # treat formats specially
                        if not text.endswith(v):
                            ins = False
                            break
                        else:
                            continue
                    
                    # treat all others normally
                    text = item.find(k).text
                    if text.lower().find(v) == -1:
                        ins = False
                        break
                
                if ins:
                    # if ins is True, grab the title, link, description (will later be parsed to grab size/comment
                    it = {}
                    it['title'] = item.find('title').text
                    it['link'] = item.find('link').text
                    it['description'] = item.find('description').text
                    items.append(it)
        except Exception, e:
            #sys.exit(e)
            if verbose:
                print e
            return -1
            
        return (items, len(items))
        
    @staticmethod
    def refresh(names, verbose = True):
        ''' static function to check the rss hook again for a particular .conf file,
        should be called periodically to check for updates '''
        if len(names) == 0:
            #sys.exit('no files specified')
            return None
            
        url_o = ''
        file = None
        
        found = []
        for name in names:
            name = name.lower().replace(' ','') + '.conf'
            try:
                if not os.path.exists(name):
                    raise Exception('file \'%s\' does not exist'%(name))
                if verbose:
                    print 'opening \'%s\'...'%(name) 
                conf = open(name, 'r+')
            except Exception, e:
                #sys.exit(e)
                if verbose:
                    print e
                return None
                
            try:
                last_t = os.stat(name).st_mtime
                last = datetime.fromtimestamp(last_t)
                # grab url, keyword, and last access time from the specified conf file
                line_re = re.compile('#([0-9#]*)#([A-Z]+)*(?:###)*(.+)$')
                c = 0
                for line in conf:
                    match = line_re.match(line)
                    
                    # handle individual entries
                    if match.group(1) != '#':
                        # grabs the last line number
                        c = int(match.group(1))
                    else:
                        if match.group(2) == 'NAME':
                            # strip the last 5 characters from the name '.conf'
                            if name[:-5] != match.group(3):
                                raise Exception('improper file found: title')
                        elif match.group(2) == 'URL':
                            url = match.group(3)
                        elif match.group(2) == 'KEYWORDS':
                            if verbose:
                                print 'parsing keywords from file...'
                            keywords = None
                            keywords = eval(match.group(3))
                            if not keywords:
                                raise Exception('improper file found: keywords')
                            if verbose:
                                print 'keywords parsed'
                        '''
                        elif match.group(2) == 'LASTACCESS':
                            last = datetime.strptime(match.group(3), '%Y-%m-%d %H:%M:%S')
                            if not last:
                                raise Exception('improper file found: lastaccess')
                            print '\nlast access at %s'%(last)
                        '''
                # close the file and reopen if needed
                conf.close()
                
                if not url:
                    raise Exception('improper file found: url')

                if url and keywords and last:
                    if verbose:
                        print 'opening \'%s\'...'%(url)
                    if True:
                    # this doesnt work atm
                    #if url != url_o or file == None:
                        # if not the same file, request again
                        req = urllib2.Request(url)
                        file = urllib2.urlopen(req)
                    (ret, count) = trapyhook.parser(file, keywords, last, verbose)
                    
                    url_o = url
                    
                    if ret != None and count != 0:
                        # if file is needed
                        conf = open(name, 'r+')
                        # append found values to the end of the file, update last access time
                        if verbose:
                            print '%d matches found.\n'%(count)
                        conf.seek(0, 2) # seek to end of file just in case
                        for i in ret:
                            conf.write('#%d#%s\n'%(c,i))
                            found.append(i)
                            c = c + 1
                        conf.close()
                    else:
                        if verbose:
                            print 'No new matches found.\n'
                    
            except Exception, e:
                conf.close()
                #sys.exit(e)
                if verbose:
                    print e
                return None
        # should return a list of objects so manager can pass it back up to cmdline to create the notification
        return found

if __name__ == '__main__':
    list = []
    list.append(('Title', 'Madoka'))
    list.append(('Title', '[Nutbladder]'))
    list.append(('Format', 'mkv'))
    # 'Title': 'Madoka' would be generated by Keyword => 'Madoka'
    # 'Title': '[Nutbladder]' would be generated by Sub Group => 'Nutbladder'
    # 'Format': 'mkv' would be generated by Format => 'mkv'
    
    # initializes a new trapyhook object
    trapyhook('http://tokyotosho.info/rss.php?filter=1&zwnj=0', 'MadokaNut', list)
    
    # refreshes the trapyhook object
    trapyhook.refresh(['Madokanut'])
    
    ### Should we create a new hook for every query? I don't really know... I think this way is actually better... but no shared memory for static functions