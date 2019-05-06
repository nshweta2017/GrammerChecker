#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 17:39:19 2019

@author: snayak1
"""
#----------------------------------------------------------------------------------------------------------------------
#Import packages. Please install en model for spacy
#----------------------------------------------------------------------------------------------------------------------
import spacy
#from textblob import Word
from ccg_nlpy import remote_pipeline
import nltk
import pandas as pd
from pattern.en import lexeme
from textblob import TextBlob
import logging
import traceback
#Load en model for spacy (light version)




class tenseErrorDetector :
    
        #logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
        def __init__(self):
                 #list of possible subjects
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)
                logFormatter = '%(asctime)s -%(name)s - %(levelname)s - %(message)s'
                logging.basicConfig(filename='app.log', filemode='a', datefmt = '%Y-%m-%d %I:%M:%S %p', format=logFormatter)
                self.logger = logging.getLogger(__name__)
                self.logger.info('Importing articleErrorDector..') 
                self.SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]

        #----------------------------------------------------------------------------------------------------------------------
        #Sometimes spacy fails to detect the correct form of verb alternative way to detect it is using 
        #CogComp's light-weight Python NLP annotators 
        #For demo please refer  : http://macniece.seas.upenn.edu:4004/
        #Input : verb 
        #Output : Tag of verb when parsed with ccg_nlpy
        #----------------------------------------------------------------------------------------------------------------------
        
        def checkPosWithCogComp(self,word) :
            pipeline = remote_pipeline.RemotePipeline()
            doc = pipeline.doc(word) 
            pos_with_cc = list(doc.get_pos)
            return pos_with_cc[0]['label']
        
        #check if sentence is negated
        def isNegated(self,tok):
            negations = {"no", "not", "n't", "never", "none"}
            for dep in list(tok.lefts) + list(tok.rights):
                if dep.lower_ in negations:
                    return True
            return False
        
        #----------------------------------------------------------------------------------------------------------------------
        
        #Find subjects if sentence is complex or compound
        #Input : Subjects 
            
        #Output : Additional sentences from a compound sentence
            
        #----------------------------------------------------------------------------------------------------------------------
        
        def getSubsFromConjunctions(self,subs):
            moreSubs = []
            for sub in subs:
                # rights is a generator
                rights = list(sub.rights)
                rightDeps = {tok.lower_ for tok in rights}
                if "and" in rightDeps:
                    moreSubs.extend([tok for tok in rights if tok.dep_ in self.SUBJECTS or tok.pos_ == "NOUN"])
                    if len(moreSubs) > 0:
                        moreSubs.extend(self.getSubsFromConjunctions(moreSubs))
            return moreSubs
        
        #----------------------------------------------------------------------------------------------------------------------
        
        #Find subjects from nagative sentence
            
        #Input : verb 
            
        #Output : subjects
            
        #----------------------------------------------------------------------------------------------------------------------
        def findSubs(self,tok):
            head = tok.head
            while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
                head = head.head
            if head.pos_ == "VERB":
                subs = [tok for tok in head.lefts if tok.dep_ == "SUB" or tok.dep_ == "compound"]
                if len(subs) > 0:
                    verbNegated = self.isNegated(head)
                    subs.extend(self.getSubsFromConjunctions(subs))
                    return subs, verbNegated
                elif head.head != head:
                    return self.findSubs(head)
            elif head.pos_ == "NOUN" :
                return [head], self.isNegated(tok)
            return [], False
        
        #----------------------------------------------------------------------------------------------------------------------
        
        #This function finds all subjects from the sentence
            
        #Input : verb 
            
        #Output : subjects in the sentence
            
        #----------------------------------------------------------------------------------------------------------------------
            
        def getAllSubs(self,v):
            verbNegated = self.isNegated(v)
            subs = [tok for tok in v.lefts if tok.dep_ in self.SUBJECTS and tok.pos_ != "DET"]
            if len(subs) > 0:
                subs.extend(self.getSubsFromConjunctions(subs))
            else:
                foundSubs, verbNegated = self.findSubs(v)
                subs.extend(foundSubs)
            return subs, verbNegated
        #----------------------------------------------------------------------------------------------------------------------
        #For Sentences Like 'I am eat' spacy detects vesb as adjective(for which POS is JJ)
        #Below function will check if sentence parses such grammer 
            
        #Input : tokenized sentence 
            
        #Output : If sentence follows grammer retuns position of error in the sentence else returns -1
            
        #----------------------------------------------------------------------------------------------------------------------
            
        
        def checkIfVerbAsAdjective(self,tokens) :
            Digdug = nltk.RegexpParser(r""" CC: }<.*>+{
                                            {<VBP|VBZ|VBD>*<JJ> }    # Chink sequences of CC
                                        """)
             
            sentence = nltk.pos_tag(nltk.word_tokenize(tokens.text))
        
            result = Digdug.parse(sentence)
            subtree_count = 0 
            for subtree in result.subtrees(filter=lambda t: t.label() == 'CC'):
                    subtree_count = subtree_count+1
        
            if subtree_count >= 1 :
                
                AdverbAsVerb = [tok for tok in tokens if  tok.tag_ == "JJ" ]
                if (len(AdverbAsVerb) > 0 ):
                    if self.checkPosWithCogComp(AdverbAsVerb[0].text) == 'VB' :
                        position = tokens.text.find(AdverbAsVerb[0].text)
                        print('Possible error at :',AdverbAsVerb[0].text)
                        return False,position,position+len(AdverbAsVerb[0].text)+1
                    
                else:
                    return True,-1,-1
            else :
                    return True,-1,-1
                
        
        #----------------------------------------------------------------------------------------------------------------------
        # Check if sentence is follows rules of future tense correctly
                    
        # Input : Verbs ,auxillary verbs , tokanized sentence
                    
        # Output :If sentence follows any of the rule for future sentence function will return -1 else it will 
        #         return position of error in the sentence
                    
        #----------------------------------------------------------------------------------------------------------------------
        def checkFutureTense(self,verbs,aux,tokens) :
                if len(aux) == 1 : #if sentence has single aux verb  it is in simple future tense
                    if verbs[0].tag_ == 'VB' or  verbs[0].tag_ == 'VBP':
                        #w = Word(verbs[0].text)
                        lex = lexeme(verbs[0].text)
                        if verbs[0].text == 'be':
                            print(tokens[verbs[0].i+1].text)
                            position = tokens.text.find(verbs[0].text)
                            return position,position+len(verbs[0].text)
            #            elif WordNetLemmatizer().lemmatize(verbs[0].text,'v').lower() != verbs[0].text.lower() :
            #                print('Possible error at:',verbs[0].text)
            #                position = tokens.text.find(verbs[0].text)
            #                return position,position+len(verbs[0].text)
                            
                        elif lex[0] == verbs[0].text.lower() :
                                 return -1,-1
            
                        else :
                                 print('Possible error at:',verbs[0].text)
                                 position = tokens.text.find(verbs[0].text)
                                 return position,position+len(verbs[0].text)
                                 
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
                elif len(aux) == 2 : #if sentence has two aux verb  it is in continous future tense or future perfetct tense
                    if aux[1].text.lower() == 'have' : #check future perfetct tense
                        if verbs[0].tag_ == 'VBN' :
                            if verbs[0].text == 'been' : # I will have been ate
                                if verbs[1].tag_ != 'VBG' :
                                    print('Possible error at:',verbs[1])
                                    position = tokens.text.find(verbs[0].text)
                                    return position,position+len(verbs[0].text)
                                else :
                                    #pass
                                    return -1,-1
                            else :
                                #pass
                                return -1,-1
                        else :
                            print('Possible error at:',verbs[0].text)
                            position = tokens.text.find(verbs[0].text)
                            return position,position+len(verbs[0].text)
                        
                    elif aux[1].text.lower() == 'be' : #check continous future tense
                        if verbs[0].tag_ == 'VBG' :
                             #pass
                             return -1,-1
                        else :
                            
                            print('Possible error at:',verbs[0].text)
                            position = tokens.text.find(verbs[0].text)
                            return position,position+len(verbs[0].text)
                        
                elif len(aux) == 3 :  #if sentence has three aux verb sentence will be in future perfect continous tense
                    if aux[1].text.lower() == 'have' and aux[2].text.lower() == 'been':
                        if verbs[0].tag_ == 'VBG' :
                            #pass
                            return -1,-1
                        else :
                            print('Possible error at:',verbs[0].text)
                            position = tokens.text.find(verbs[0].text)
                            return position,position+len(verbs[0].text)
        
        #----------------------------------------------------------------------------------------------------------------------
        # Check if sentence is follows rules of present tense correctly
                    
        # Input : Verbs ,auxillary verbs , tokanized sentence
                    
        # Output :If sentence follows any of the rule for future sentence function will return -1 else it will 
        #         return position of error in the sentence
                    
        #----------------------------------------------------------------------------------------------------------------------
                        
        def checkPresentTense(self,verbs,aux,tokens) :
            if len(aux) == 1 :
                if aux[0].text != 'have'  or aux[0].text != 'has': #check present continous tense
                    if verbs[0].tag_ == "VBG":
                        #pass
                        return -1,-1
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
                else : #check present perfect tense
                    
                    if self.checkPosWithCogComp(verbs[0].text) == 'VBN' :
                        #pass
                        return -1,-1
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
            elif len(aux) == 2 :
                if aux[1].text.lower() == 'been':
                    if verbs[0].tag_ == "VBG" :
                        #pass
                        return -1,-1
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
                                     
        #        elif aux[0].tag_ == "VBZ" :
        #            if len(aux) == 1 :
        #                if aux[0].text != 'has'  :
        #                    if verbs[0].tag_ == "VBG":
        #                        #pass
        #                        return -1,-1
        #                    else :
        #                        logging.exception('Possible error at:',verbs[0].text)
        #                        position = tokens.text.find(verbs[0].text)
        #                        return position,position+len(verbs[0].text)
        #                else :
        #                    if checkPosWithCogComp(verbs[0].text) == 'VBN' :
        #                        #pass
        #                        return -1,-1
        #                    else :
        #                         logging.exception('Possible error at:',verbs[0].text)
        #                         position = tokens.text.find(verbs[0].text)
        #                         return position,position+len(verbs[0].text)
                         
        
        #----------------------------------------------------------------------------------------------------------------------
        # Check if sentence is follows rules of past tense correctly
                    
        # Input : Verbs ,auxillary verbs , tokanized sentence
                    
        # Output :If sentence follows any of the rule for future sentence function will return -1 else it will 
        #         return position of error in the sentence
                    
        #----------------------------------------------------------------------------------------------------------------------
                                 
        def checkPastTense(self,verbs,aux,tokens) :
            if len(aux) == 1 :
                if aux[0].text != 'had'  : #check past continous tense
                    if verbs[0].tag_ == "VBG":
                        #pass
                        return -1,-1
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
                else :                
                    if verbs[0].tag_ == "VBN": #check past perfect tense
                        #pass
                        return -1,-1
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
            elif len(aux) == 2 : #check past perfect continous tense
                if aux[1].text.lower() == 'been':
                    if verbs[0].tag_ == "VBG" :
                        #pass
                        return -1,-1
                     
                    else :
                        print('Possible error at:',verbs[0].text)
                        position = tokens.text.find(verbs[0].text)
                        return position,position+len(verbs[0].text)
        
        
        #----------------------------------------------------------------------------------------------------------------------
        # Check if sentence is follows rules of simple past tense or simple present tense correctly
                    
        # Input : Verbs  , tokanized sentence
                    
        # Output :If sentence follows any of the rule for future sentence function will return -1 else it will 
        #         return position of error in the sentence
                    
        #----------------------------------------------------------------------------------------------------------------------
                        
        def checkSimplePastPresentTense(self,verbs,tokens) :
            SingularPronoun = ['he','she','it','who','someone','everybody']
            
            subs, verbNegated = self.getAllSubs(verbs[0])
        #    logging.exception(subs)
        #    if checkPosWithCogComp(verbs[0].text) == 'VBN' :
        #        position = tokens.text.find(verbs[0].text)
        #        return position,position+len(verbs[0].text)
        #        #logging.exception('Possible error before :',verbs[0].text)
        #    
        #    elif verbs[0].tag_ == 'VBN' or verbs[0].tag_ == 'VBG'  :
        #        logging.exception('Possible error before :',verbs[0])
        #        position = tokens.text.find(verbs[0].text)
        #        return position,position+len(verbs[0].text)
            
            if  verbs[0].tag_ == 'VBZ' :
                if (subs[0].text.lower() in SingularPronoun or subs[0].tag_=='NN' or subs[0].tag_ == 'NNP') :
                    return -1,-1
                else :
                     print('Possible error before :',verbs[0])
                     position = tokens.text.find(verbs[0].text)
                     return position,position+len(verbs[0].text)
                        
            elif verbs[0].tag_ == 'VBP':
                if (subs[0].text.lower() in SingularPronoun or subs[0].tag_=='NN' or subs[0].tag_ == 'NNP') :
                    print('Possible error before :',verbs[0])
                    position = tokens.text.find(verbs[0].text)
                    return position,position+len(verbs[0].text)
                   
                else :
                    return -1,-1
                    
            else :
                return -1,-1
                        
        
        def tenseCheck(self,text,loc) :
            #print(text)
            self.logger.info('Checking tense error..')
            try :
                
                    nlp = spacy.load('en_core_web_md')
                    doc = nlp(text)
                    for idno, tokens in enumerate(doc.sents) :
                            
                            status, start,end = self.checkIfVerbAsAdjective(tokens)
                            if  status :
                                
                                    aux = []
                                    verbs= []
                                    # tok.dep_ == 'appos' is for "I Bit"
                                    verbs = [tok for tok in tokens if tok.pos_ == "VERB" and (tok.dep_ == "ROOT" or  tok.dep_ == 'dep' or  tok.dep_ == 'appos') and tok.dep_ != "aux"]
                                    if len(verbs) > 0 :
                #                        if verbs[0].dep_ == 'appos' :
                #                            start = tokens.text.find(verbs[0].text)
                #                            itermidiat_frame = pd.DataFrame([[idno,start,start+len(verbs[0].text)+1]],columns=['line','start','end'])
                #                            loc = loc.append(itermidiat_frame) 
                #                            print('Possible error at:',verbs[0].text)   
                #                            return loc
                                        
                                        aux = [tok for tok in verbs[0].lefts if  tok.dep_ == "aux" or tok.dep_ == "auxpass"]
                                        aux_r = [tok for tok in verbs[0].rights if  tok.dep_ == "aux"] # for sentences like 'I will be going to visit Mumbai'
                                                                                                       # auxillary verb(to) will be right subtree of root verb
                                        if (len(aux)>0) :
                                             if aux[0].tag_ == "MD" :
                                                 start,end =-1,-1 
                                                 start,end = self.checkFutureTense(verbs,aux,tokens)
                                                 itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                                 loc = loc.append(itermidiat_frame) 
                                             elif aux[0].tag_ == "VBP" or aux[0].tag_ == "VBZ" :
                                                 start,end =-1,-1
                                                 start,end = self.checkPresentTense(verbs,aux,tokens)
                                                 itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                                 loc = loc.append(itermidiat_frame) 
                                             elif aux[0].tag_ == "VBD" :
                                                 start,end =-1,-1
                                                 start,end = self.checkPastTense(verbs,aux,tokens)
                                                 itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                                 loc = loc.append(itermidiat_frame) 
                                        else : # if no auxillary verb sentence will be in simple past or simple present tense
                                            start,end =-1,-1
                                            start,end = self.checkSimplePastPresentTense(verbs,tokens)
                                            itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                            loc = loc.append(itermidiat_frame) 
                                        if (len(aux_r)>0) : # i will be going to check
                                            verbs_r = [tok for tok in verbs[0].rights if tok.pos_ == "VERB"  and tok.dep_ != "aux"]
                                            if verbs_r[0].tag_ == "VB" :
                                                pass
                                            else:
                                                print('Possible error at:',verbs[0].text)  
                                                start = tokens.text.find(verbs[0].text)
                                                itermidiat_frame = pd.DataFrame([[idno,start,start+len(verbs[0].text)+1]],columns=['line','start','end'])
                                                loc = loc.append(itermidiat_frame) 
                                    
                                    else :
                                        #Check erros for the sentences for twhich main verb is missing ex. I will catches
                                        aux = [tok for tok in tokens if  tok.dep_ == "aux" or tok.dep_ =="auxpass"]
                                        if len(aux) > 0:
                                            nouns = [tok for tok in tokens if   tok.dep_ =="ROOT"]
                                            if aux[0].tag_ == "MD" :
                                                blob = TextBlob(tokens.text)
                                                counts =[tag for word,tag in blob.tags if word.lower() == nouns[0].text.lower() ]
                                                if (counts[0] == 'VB') :
                                                    #print(tokens)
                                                    start = tokens.text.find(nouns[0].text)
                                                    itermidiat_frame = pd.DataFrame([[idno,start,start+len(nouns[0].text)+1]],columns=['line','start','end'])
                                                    loc = loc.append(itermidiat_frame) 
                                                                          
                                                    print('Possible error at:',nouns[0].text)
                                        else :
                                            #Check erros for the sentences main verb is miss-interpreted as noun Ex. I will chooses
                                            nouns = [tok for tok in tokens if   tok.dep_ =="ROOT"]
                                            blob = TextBlob(tokens.text)
                                            counts =[ tag for word,tag in blob.tags if word.lower() == nouns[0].text.lower() ]
                                            #NNS has been added for sentences liike I sangs
                                            if (counts[0] == 'VB' or counts[0] == 'VBP' or counts[0] == 'VBD' or counts[0] == 'VBZ' or counts[0] == 'VBG' or counts[0] == 'NNS') :
                                                start = tokens.text.find(nouns[0].text)
                                                itermidiat_frame = pd.DataFrame([[idno,start,start+len(nouns[0].text)+1]],columns=['line','start','end'])
                                                loc = loc.append(itermidiat_frame) 
                                                print('Possible error at:',nouns[0].text)        
                            else:
                                itermidiat_frame = pd.DataFrame([[idno,start,end]],columns=['line','start','end'])
                                loc = loc.append(itermidiat_frame) 
            
            except Exception as e:
                        self.logger.exception(traceback.format_exc())  
                        print(traceback.format_exc())    
    
            self.logger.info('Checking tense error has been completed..')
            return loc