import sqlite3 as lite
import sys
from urlparse import urlsplit
import base64

class RequestDB:
    def __init__(self,path):
        self.dbPath = path
        try:
            self.con = lite.connect(path)
            self.con.text_factory = str
            self.con.row_factory = lite.Row
        except lite.Error, e:
            print "Error initiating database %s" %(e.args[0])
            self.con = None
            return
        self.cache = []
        if self.checkTableExists('redirects') == False:
            statement = "CREATE TABLE redirects ("+"\n"+ \
                                    " id INTEGER PRIMARY KEY ASC,"+"\n"+ \
                                    " from_url TEXT,"+"\n"+ \
                                    " to_url TEXT, " +"\n"+ \
                                    " type_id INTEGER, " + "\n" + \
                                    " unique (from_url, to_url));";
            if self.executeStatement(statement) == None:
                return ;

    def find3XXRedirection(self):
        query_request = "SELECT id, url FROM http_requests WHERE " + \
                        "is_redirect = 1 AND " + \
                        "page_id != -1 " + \
                        ";"
        query_location = "SELECT value FROM http_request_headers WHERE " + \
                         "http_request_id = ? AND " + \
                         "name = 'location' ";

        cur = self.executeStatement(query_request)
        
        while True:
            row = cur.fetchone()
            if row == None:
                break
            statement = query_location.replace('?',str(row['id']))
            item_cur = self.executeStatement(statement)
           
            location = item_cur.fetchone()
            
            if location == None:
                #print query_location
                elem = row['url'], ""
            else:
                elem = row['url'], location['value']
            #typeid for 3xx is 1
            #print elem
            self.storeItem(elem,1)

    #this function has high false positive, no false negative
    def findJSRedirectionRoughly(self):
        query_request = "SELECT * FROM http_requests WHERE " + \
                        "is_redirect = 0 AND " + \
                        "page_id != -1 AND " + \
                        "content_type = 'text/html' AND " + \
                        "referrer != '' " + \
                        ";"
        query_referer = "SELECT * FROM http_requests WHERE " + \
                        "url = ? AND " + \
                        "page_id = ? " + \
                        ";"
        cur = self.con.cursor()
        try:
            cur.execute(query_request)
        except lite.Error, e:
            print "Error executing SQL: "+query_request+" "+str(e)
            return 

        count = 0;
        while True:
            row = cur.fetchone()
            if row == None:
                break
            item_cur = self.con.cursor()
            print row['url'],"  ",row['referrer']," ",row['content_type']
            
            try:
                referrer = str(row['referrer'])
                #print referrer
                item_cur.execute(query_referer, (referrer, str(row['page_id'])) )
            except lite.Error, e:
                print "Error executing SQL "+query_referer+" ["+ row['referrer'] +"] "+str(e)
                #return
            item = item_cur.fetchone()
            
            if(item != None):
                elem = item['url'],row['url']
                count = count + 1
            #else:
                #elem = "", row['url']
                print item['id']," ",row['id']
                self.storeItem(elem,4)
            
        print count

    def findRedirection(self):
        self.find3XXRedirection()
        self.findMETARedirection()
        self.findJSRedirection()
        self.con.close();
        print "finish extracking redirects, contents have been stored to table scripts"

    def findJSOrMETARedirection(self,table_name):
        query_request = "SELECT * FROM "+table_name+" ;";
        if table_name == "script_redirects":
            typeid = 2
        elif table_name == "meta_redirects":
            typeid = 3
        else:
            print "Error table name: "+table_name
            return;

        cur = self.executeStatement(query_request)
        
        while True:
            row = cur.fetchone()
            if row == None:
                break
            #item_cur = self.con.cursor()
            elem = row['from_url'],row['to_url']

            self.storeItem(elem,typeid)
            
    def findJSRedirection(self):
        self.findJSOrMETARedirection("script_redirects")

    def findMETARedirection(self):
        self.findJSOrMETARedirection("meta_redirects")

    def storeItem(self, elem,typeid):
        statement = "INSERT INTO redirects" + \
                    "(from_url, to_url, type_id) " + \
                    "VALUES ( \""+elem[0]+"\",\""+elem[1]+"\","+str(typeid) +");"
        self.executeStatement(statement)

        #print elem[0]," ==> ",elem[1]

    def findPotentialNoneLoadedURLs(self):
        query_test = "SELECT * FROM http_requests WHERE " + \
                 "is_redirect = 0 AND " + \
                 "page_id != -1 AND " + \
                 "content_type = 'null' AND " + \
                 "referrer = '' " + \
                 ";"
        
        cur = self.executeStatement(query_test)
        while True:
            row = cur.fetchone()
            if row == None:
                break
            print "Potential URL: ",row['url']

    def checkTableExists(self,table_name):
        statement = "SELECT name FROM sqlite_master WHERE " +\
                    "type='table' AND name='" + \
                    table_name + "';"
        cur = self.executeStatement(statement)
        row = cur.fetchone()
        if row == None:
        #    print "NO"
            return False
        #print "YES"
        return True

    def executeStatement(self, statement):
        #print statement
        cur = self.con.cursor()
        try:
            cur.execute(statement)
        except lite.Error, e:
            if str(e).startswith("UNIQUE constraint"):
                #print str(e),statement
                return 
                #sys.exit(1) 
            print "Error executing SQL: "+statement+" "+str(e)
            sys.exit(1)
        self.con.commit()
        return cur

#USAGE: python FindRedirection.py database_file_path
#   RequestDB.findRedirection() find all the redirections
#   RequestDB.findPotentialNoneLoadedURLs() find URLs that seem to fail loading

#Results are stored in table redirects, In table redirects, 
#  typeid refers to the type of redirection:
#  1: 3xx redirection
#  2: Javascript redirection, such as change the value of window.location
#  3: Meta redirection
def main():     
    #db = RequestDB("httpfox.sqlite")
    db = RequestDB(sys.argv[1])
    db.findRedirection()
  
if __name__ == '__main__':
    main()

