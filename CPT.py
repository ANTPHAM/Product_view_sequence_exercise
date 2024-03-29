# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 12:19:59 2019

@author: Eric
"""

from PredictionTree import *
import pandas as pd
from tqdm import tqdm


class CPT():

    alphabet = None # A set of all unique items in the entire data file
    root = None # Root node of the Prediction Tree
    II = None #Inverted Index dictionary, where key : unique item, value : set of sequences containing this item
    LT = None # A Lookup table dictionary, where key : id of a sequence(row), value: leaf node of a Prediction Tree

    def __init__(self):
        self.alphabet = set()
        self.root = PredictionTree()
        self.II = {}
        self.LT = {}

    def load_files(self,train_file,test_file = None):

        """
        This function reads in the wide csv file of sequences separated by commas and returns a list of list of those
        sequences. The sequences are defined as below.
        seq1 = A,B,C,D
        seq2  B,C,E
        Returns: [[A,B,C,D],[B,C,E]]
        """
        
        data = [] # List of list containing the entire sequence data using which the model will be trained.
        target = [] # List of list containing the test sequences whose next n items are to be predicted
        
        if train_file is None:
            return train_file
        
        train = pd.read_csv(train_file)
    
        for index, row in train.iterrows():
            data.append(row.values)
            
        if test_file is not None:
            
            test = pd.read_csv(test_file)
            
            for index, row in test.iterrows():
                data.append(row.values)
                target.append(list(row.values))
                
            return data, target
        
        return data
        


    # In[3]:


    def train(self, data):

        """
        This functions populates the Prediction Tree, Inverted Index and LookUp Table for the algorithm.
        Input: The list of list training data
        Output : Boolean True
        """
        
        cursornode = self.root
        

        for seqid,row in enumerate(data):
            for element in row:

                # adding to the Prediction Tree

                if cursornode.hasChild(element)== False:
                    cursornode.addChild(element)
                    cursornode = cursornode.getChild(element)

                else:
                    cursornode = cursornode.getChild(element)

                # Adding to the Inverted Index

                if self.II.get(element) is None:
                    self.II[element] = set()

                self.II[element].add(seqid)
                
                self.alphabet.add(element)

            self.LT[seqid] = cursornode

            cursornode = self.root
            
        return True


    def score(self, counttable,key, length, target_size, number_of_similar_sequences, number_items_counttable):


        """
        This function is the main workhorse and calculates the score to be populated against an item. Items are predicted
        using this score.
        Output: Returns a counttable dictionary which stores the score against items. This counttable is specific for a 
        particular row or a sequence and therefore re-calculated at each prediction.
        """



        weight_level = 1/number_of_similar_sequences
        weight_distance = 1/number_items_counttable
        score = 1 + weight_level + weight_distance* 0.001
        
        if counttable.get(key) is None:
            counttable[key] = score
        else:
            counttable[key] = score * counttable.get(key)
            
        return counttable



    def predict(self,data,target,k, n=1): 
        """
        Here target is the test dataset in the form of list of list,
        k is the number of last elements that will be used to find similar sequences and,
        n is the number of predictions required.
        Input: training list of list, target list of list, k,n
        Output: max n predictions for each sequence
        """
        
        predictions = []
        
        for each_target in tqdm(target):
            each_target = each_target[-k:]
            
            intersection = set(range(0,len(data)))
            
            for element in each_target:
                if self.II.get(element) is None:
                    continue
                intersection = intersection & self.II.get(element)
            
            similar_sequences = []
            
            for element in intersection:
                currentnode = self.LT.get(element)
                tmp = []
                while currentnode.Item is not None:
                    tmp.append(currentnode.Item)
                    currentnode = currentnode.Parent
                similar_sequences.append(tmp)
                
            for sequence in similar_sequences:
                sequence.reverse()
                
            counttable = {}

            for  sequence in similar_sequences:
                try:
                    index = next(i for i,v in zip(range(len(sequence)-1, 0, -1), reversed(sequence)) if v == each_target[-1])
                except:
                    index = None
                if index is not None:
                    count = 1
                    for element in sequence[index+1:]:
                        if element in each_target:
                            continue
                            
                        counttable = self.score(counttable,element,len(each_target),len(each_target),len(similar_sequences),count)
                        count+=1


            pred = self.get_n_largest(counttable,n)
            predictions.append(pred)

        return predictions



    def get_n_largest(self,dictionary,n):


        """
        A small utility to obtain top n keys of a Dictionary based on their values.
        """
        largest = sorted(dictionary.items(), key = lambda t: t[1], reverse=True)[:n]
        return [key for key,_ in largest]