#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 17:38:32 2019

@author: snayak1
"""

from GrammerChecker import *
import pandas as pd


loc = pd.DataFrame(columns=['line','start','end'])
aff = articleErrorDector()
loc =  aff.articleCheck('It is a orange',loc)
loc
