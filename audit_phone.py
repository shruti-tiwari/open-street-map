'''Auditing Phone numbers
check
'''
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

phone_number_re=re.compile(r'^\+1\s\([0-9]{3}\)\s[0-9]{3}\-[0-9]{4}$')
 #
def audit_pn_type(number):
    if(isinstance(number,unicode)):
        number = number.encode('ascii', 'ignore').decode('ascii')

    m = phone_number_re.search(number)
    if m:        
        return True
    else:
        return False
    
    
def get_numeric(s):
    return str(filter(str.isdigit,s))

def check_ext(number):
    return len(number)>10

def update_number(wrong_number):
    numeric=get_numeric(wrong_number)
    
    if numeric.startswith('1'):
        numeric=numeric[1:]
        
    if check_ext(numeric):
        newnumber='+1 ({}) {}-{} ext. {}'.format(numeric[0:3], numeric[3:6], numeric[6:10],numeric[10:])
        return newnumber
    
    elif len(numeric)==10:
        newnumber='+1 ({}) {}-{}'.format(numeric[0:3], numeric[3:6], numeric[6:])
        return newnumber
    
    else: 
        newnumber="No Phone Number"
        return newnumber
    return
    #print (wrong_number +" -> " +newnumber)
   

           
def process_phone_map(filename):
    phones=set()
    count=0
    for _, element in ET.iterparse(filename):
        if element.tag=="tag":
            #for child in element:
            #if child.tag=="tag":
            if element.attrib["k"]=="phone":
                if audit_pn_type(element.attrib["v"]):
                    value=element.attrib["v"] 
                else:
                    value=update_number(element.attrib["v"])
                
                phones.add(value.encode('ascii','ignore'))
    return phones
if __name__ == '__main__':
    print(process_phone_map('sample3.osm'))
