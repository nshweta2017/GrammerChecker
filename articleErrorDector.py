# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 20 16:33:44 2019

@author: snayak1
"""
import traceback
from textblob import TextBlob
import re
import spacy
import pandas as pd
#import tenseErrorDetector
import logging


#check for exceptions


class articleErrorDector :
    
        logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
        
        def __init__(self):
            logging.info('Importing articleErrorDector..')
            
            
        def checkWordExists(self,word,file):
            with open(file, 'r') as file:
                if re.search('^{0}$'.format(re.escape(word)), file.read(), flags=re.M):
                    return True
                else:
                    return False
                
        
        def checkIfStartsWithVowel(self,word) :
            if not ( word.lower().startswith('a') |word.lower().startswith('e') | word.lower().startswith('i') 
                   | word.lower().startswith('o') |word.lower().startswith('u')) :
                return True
            else:
                return False
            
        def getSentenceWithTag(self,tokens,nextWord,article) :
            nextloc = tokens.text.find(nextWord)
            return nextloc-(1+len(article)),nextloc-1
            #return tokens[0:nextloc-(1+len(article))] + ' <span class="highlight0"> '+tokens[nextloc-2]+' </span> '+tokens[nextloc:]
        
        def articleCheck(self,text,loc) :
            nlp = spacy.load('en')
            doc = nlp(text)
            try :
                logging.info('Checking article error..')
                for idno, tokens in enumerate(doc.sents):
                    articleList = []
                    articleList = [tok for tok in tokens if tok.dep_ =='det']
                    entitiesList = []
                    entitiesList = [ent.text for ent in tokens.ents if ent.label_ == 'NORP']
                    
                    for article in articleList :
                        equalsA =  None
                        equalsAn =  None
                        equalsThe = None
                        determiner_rule = 'NO_RULE'
                        if article.text.lower() == 'a' :
                             equalsA = True
                        elif article.text.lower() == 'an' : 
                             equalsAn = True
                        elif article.text.lower() == 'the' :
                             equalsThe = True
                        if (tokens[article.i+1].text in entitiesList) and (tokens[article.i+1].pos_ !=' ADJ') :
                            
                                    determiner_rule = 'NORP.determiner'
                                    
                        blob = TextBlob(tokens[article.i+1].text)
                        
                        if blob.words.pop().pluralize() == tokens[article.i+1].text :
                            
                            determiner_rule='UCN.determiner'
                            
                        if self.checkWordExists(tokens[article.i+1].text,'./det_a.txt'):
                            determiner_rule='A.determiner'
                            
                        elif self.checkWordExists(tokens[article.i+1].text,'./det_an.txt'):
                            determiner_rule='AN.determiner'   
                            
                        if determiner_rule == 'NO_RULE' :
                                #print(tokens[t.i+1].dep_,tokens[t.i+1].text)
                                if tokens[article.i+1].tag_ == 'NNS' :
                                    print(tokens[article.i+1].pos_)
                                    determiner_rule = 'The.determiner'
                                    print(determiner_rule)
                                    
                                elif tokens[article.i+1].pos_ == 'ADJ' and tokens[article.i+2].tag_ == 'NN' :
                                   determiner_rule = 'The.determiner'  
                                elif tokens[article.i+1].pos_ == 'ADJ' and tokens[article.i+2].pos_ == 'NOUN' :   
                                    determiner_rule = 'The.determiner'
                                elif self.checkIfStartsWithVowel(tokens[article.i+1].text) :
                                        determiner_rule='A.determiner'
                                else :
                                       determiner_rule='AN.determiner'
                        #print(determiner_rule)               
                        if determiner_rule != 'UCN.determiner'  and determiner_rule != 'NORP.determiner' :
                        
                            if determiner_rule != 'The.determiner' :
                                
                               if (equalsA == True) and (determiner_rule != 'A.determiner') :
                                   
                                   start,end = self.getSentenceWithTag(tokens,tokens[article.i+1].text,article.text)
                                   itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                   loc = loc.append(itermidiat_frame) 
                                    
                               elif (equalsAn == True) and (determiner_rule != 'AN.determiner') :
                                   
                                   start,end = self.getSentenceWithTag(tokens,tokens[article.i+1].text,article.text)
                                   itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                   loc = loc.append(itermidiat_frame) 
                                   
                               elif (equalsThe != True) :
                                   
                                   start,end = self.getSentenceWithTag(tokens,tokens[article.i+1].text,article.text)
                                   itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                   loc = loc.append(itermidiat_frame)  
                                  
                        elif (equalsA == True or equalsAn == True or equalsThe == True) :
                            
                           if (determiner_rule == 'UCN.determiner'):
                                 
                                   start,end = self.getSentenceWithTag(tokens,tokens[article.i+1].text,article.text)
                                   itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                   loc = loc.append(itermidiat_frame) 
                                 
                           else :
                               
                                   start,end = self.getSentenceWithTag(tokens,tokens[article.i+1].text,article.text)
                                   itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                   loc = loc.append(itermidiat_frame) 
                                   
                    logging.info('Checking article error check has been completed..')  
                    
            except Exception as e:
                        logging.exception(traceback.format_exc())  
                        print(traceback.format_exc()) 
            print(loc)   
            return loc
         
#loc = pd.DataFrame(columns=['line','start','end'])
#text1 =  input()
#loc = articleCheck(text1,loc)
#loc = langtool.checkWithLanguageTool(text1,loc)
#loc = tenseErrorDetector.tenseCheck(text1,loc)
