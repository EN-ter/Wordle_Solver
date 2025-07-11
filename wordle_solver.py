'''
get user input: word
    get user input: color of letters (green/yellow/grey)
import list 
calconnect to db 
select words with or excluding attributes of word entity
rate words based on letter frquency in list (if Letter in word appear(n)>1, divide Ln.val n)
sort list desc of "value" (L1val+...L5val)=word value
print to new possible answers
clear df and replace with fiktered list replace conn'''

import os
import pandas as pd
import sqlite3
from operator import concat

#word entry and letter evaluation
def word_entry():
    enter_word = concat(concat("Enter word(",  str(word_count+1)), "): ")
    word = ""
    confirmation = ""

    # prompts user for first word while word not 5 letters, or has numbers, or not as intended, or not word in list
    while (len(word) != 5 or word.isalpha() == False or confirmation != 'y' or word not in possible_answers_df['Possible_Words'].values): 
        valid_word = True
        word = str(input(enter_word))
        word = word.lower()
        
        if len(word) != 5:
            valid_word=False
            print("\nWORD MUST BE EXACTLY 5 CHARACTERS LONG\n")
        if word.isalpha() == False:
            valid_word=False
            print('WORD MAY ONLY CONTAIN LETTERS')
        if word not in possible_answers_df['Possible_Words'].values:
            valid_word=False
            print('WORD NOT IN LIST')
        if valid_word == True:
                confirmation = str(input("Confirm word y/n? "))

    word_df['letter'] = list(word)    
     
    #prompts user to evaluate and verify each letter in word (green, grey, or yellow)
    print("\n\nEvaluate each letter in ", word, "\n[G]reen,[Y]ellow, g[R]ey\n")
    word_df['eval'] = ""
    confirmation = 'n'
    while confirmation != 'y':    
        for i in range(5):    
            eval_cache = ""
            while eval_cache != "g" and eval_cache != "r" and eval_cache != "y":
                letter = word_df.loc[i,'letter'] + " = "
                eval_cache = str(input(letter))
                eval_cache = eval_cache.lower()
                if eval_cache == "g" or eval_cache == "r" or eval_cache == "y":
                    word_df.loc[i,'eval'] = eval_cache
                else:
                    print("Must use: [G]reen,[Y]ellow, g[R]ey g,y,r")
    
        print('\n')

        for i in range(5):  
            if word_df.loc[i, 'eval'] == "g":
                print(word_df.loc[i, 'letter']," = ", "GREEN")
            elif word_df.loc[i, 'eval'] == "y":
                print(word_df.loc[i, 'letter']," = ", "YELLOW")
            else:
                print(word_df.loc[i, 'letter']," = ", "GREY")
    
        confirmation = str(input("Correct y/n? ")).lower()
       
#creates query to filter words
def word_filter():
    global query
    with sqlite3.connect(possible_answers_db_path) as conn:
        possible_answers_df.to_sql(table_name, conn, if_exists='replace', index=False)
    #check for duplicate letters where one is green and other is grey or one yellow and one green, then saves to list
    duplicates = word_df.sort_values(by='letter')
    duplicates = duplicates[duplicates.duplicated(subset=['letter'], keep=False)]
    r_g_exception_letters = ""
    y_g_exception_letters = ""
    if len(duplicates) >0 :
        #evaluates if there is one grey and and one green for one first set of duplicates
        r_g_exception = duplicates['eval'].iloc[0:2].str.count('r').sum() ==1 and duplicates['eval'].iloc[0:2].str.count('g').sum() ==1
        y_g_exception = duplicates['eval'].iloc[0:2].str.count('y').sum() ==1 and duplicates['eval'].iloc[0:2].str.count('g').sum() ==1
        #adds lett to list if true
        if r_g_exception==True: r_g_exception_letters = duplicates['letter'].iloc[0]
        if y_g_exception==True: y_g_exception_letters = duplicates['letter'].iloc[0]
        if len(duplicates) >2:
            #evaluates if there is one grey and and one green for one second set of duplicates (if theres a second set)
            r_g_exception = duplicates['eval'].iloc[2:5].str.count('r').sum() ==1 and duplicates['eval'].iloc[2:5].str.count('g').sum() ==1
            y_g_exception = duplicates['eval'].iloc[2:5].str.count('y').sum() ==1 and duplicates['eval'].iloc[2:5].str.count('g').sum() ==1
            if r_g_exception==True: r_g_exception_letters += duplicates['letter'].iloc[2]
            if y_g_exception==True: y_g_exception_letters += duplicates['letter'].iloc[2]
    
    for i in range(5):
        if i != 0:
            query += " AND "
                
        if word_df.loc[i, 'eval'] == 'g':
            query += f" SUBSTRING(Possible_Words, {i+1}, 1) == '{word_df.loc[i, 'letter']}'"
        elif word_df.loc[i, 'eval'] == 'r':
            #excludes grey letter completely for single instance and when duplicate set both grey
            if word_df.loc[i, 'letter'] not in r_g_exception_letters: query += f" Possible_Words NOT LIKE '%{word_df.loc[i, 'letter']}%'"    
            #excludes grey letter from location, but does not remove from possible wordsto ensure green letter
            else:
                grey_letter = i*'_' + word_df.loc[i, 'letter'] +(4-i)*'_'
                query += f" Possible_Words NOT LIKE '{grey_letter}'"
 
        elif word_df.loc[i, 'eval'] == 'y':
            #has letter but not in position i+1 if no y_g exception
            query += f" Possible_Words LIKE '%{word_df.loc[i, 'letter']}%' AND SUBSTRING(Possible_Words, {i+1}, 1) != '{word_df.loc[i, 'letter']}'"
            #adds mmust have at least 2 occurences of letter (green location +1 )
            if word_df.loc[i, 'letter'] in y_g_exception_letters:
                query += f" AND LENGTH(REPLACE(Possible_Words, '{word_df.loc[i, 'letter']}', '')) < 4 "

def answer_ranking():
    global possible_answers_temp
    letter_value_df = pd.DataFrame()
    letter_value_df['word'] = possible_answers_temp['Possible_Words']
    #dictionary initializization for letter value in word list (ie word contains at least one instance)
    letter_value_dict = {
        'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0, 'g': 0,
        'h': 0, 'i': 0, 'j': 0, 'k': 0, 'l': 0, 'm': 0, 'n': 0,
        'o': 0, 'p': 0, 'q': 0, 'r': 0, 's': 0, 't': 0, 'u': 0,
        'v': 0, 'w': 0, 'x': 0, 'y': 0, 'z': 0}
    
    #1st letter of word =L1, 2nd letter of word = L2...
    print(possible_answers_temp[['Possible_Words']])

    possible_answers_temp[['L1', 'L2', 'L3', 'L4', 'L5']] = possible_answers_temp['Possible_Words'].apply(lambda x: pd.Series(list(x)))

    #initializes count columns (number of times letter appears in word to be used to weight letter values ie 2x: value/2)
    possible_answers_temp = possible_answers_temp.assign(**{f'L{i}count_in_word': 0 for i in range(1, 6)})

    #initailizes letter value columns
    possible_answers_temp = possible_answers_temp.assign(**{f'L{i}val': 0 for i in range(1, 6)})

    #counts if letter in word then assigns instances (excluding duplicates to value in dictionary)
    for letter, value in letter_value_dict.items():
        letter_value_df['word_replace'] =  letter_value_df['word'].str.replace(letter, '')
        letter_value_df['word_replace'] = letter_value_df['word_replace'].str.len()   
        letter_value_dict[letter] = (letter_value_df['word_replace'] < 5).sum()
    
    #assigns letter value to correspodning vlaue columns
    possible_answers_temp['L1val'] = possible_answers_temp['L1'].map(letter_value_dict)
    possible_answers_temp['L2val'] = possible_answers_temp['L2'].map(letter_value_dict)
    possible_answers_temp['L3val'] = possible_answers_temp['L3'].map(letter_value_dict)
    possible_answers_temp['L4val'] = possible_answers_temp['L4'].map(letter_value_dict)
    possible_answers_temp['L5val'] = possible_answers_temp['L5'].map(letter_value_dict)

    #propmted MS copilot: count for how many times a character in column a1 appears in string in column word
    #counts occurences of letter within word ex belle b=1, e=2, l=2
    possible_answers_temp['L1count_in_word'] = possible_answers_temp.apply(lambda row: row['Possible_Words'].count(row['L1']), axis=1)
    possible_answers_temp['L2count_in_word'] = possible_answers_temp.apply(lambda row: row['Possible_Words'].count(row['L2']), axis=1)
    possible_answers_temp['L3count_in_word'] = possible_answers_temp.apply(lambda row: row['Possible_Words'].count(row['L3']), axis=1)
    possible_answers_temp['L4count_in_word'] = possible_answers_temp.apply(lambda row: row['Possible_Words'].count(row['L4']), axis=1)
    possible_answers_temp['L5count_in_word'] = possible_answers_temp.apply(lambda row: row['Possible_Words'].count(row['L5']), axis=1)

    #divides value by occurences then sums values and sorts in descending order
    possible_answers_temp['L1val'] /= possible_answers_temp['L1count_in_word']
    possible_answers_temp['L2val'] /= possible_answers_temp['L2count_in_word']
    possible_answers_temp['L3val'] /= possible_answers_temp['L3count_in_word']
    possible_answers_temp['L4val'] /= possible_answers_temp['L4count_in_word']
    possible_answers_temp['L5val'] /= possible_answers_temp['L5count_in_word']
    possible_answers_temp['word_value']= possible_answers_temp.iloc[:, 11:16].sum(axis=1)
    possible_answers_temp.sort_values(by='word_value', ascending=False, inplace=True) 
    return(possible_answers_temp['Possible_Words'].tolist())

#loads complete word list to possible answers df and saves to SQlite db
table_name = 'Possible_answers'
#word list from https://gist.github.com/shmookey/b28e342e1b1756c4700f42f17102c2ff


folder_path = os.path.dirname(os.path.abspath(__file__))
complete_word_list = os.path.join(folder_path, r'wordlist1.csv')
possible_answers_db_path = os.path.join(folder_path, r'possible_answers.db')

possible_answers_df = pd.read_csv(complete_word_list, names = ['Possible_Words'])
possible_answers_df[['L1', 'L2', 'L3', 'L4', 'L5', 'Score']] = None
with sqlite3.connect(possible_answers_db_path) as conn: possible_answers_df.to_sql(table_name, conn, if_exists='replace', index=False)

word_count = 0
solved = ''

#word df for word entry
word_df = pd.DataFrame()
print("Recommendations for first word: \n arose \n earls \n reals \n raise \n arise")

while solved != 'y' and word_count < 6:
    
    word_entry()
    print('\n\n\n\n\n')
        
    query = f"SELECT Possible_Words FROM {table_name} WHERE"
    word_filter()

    #answer list based on query
    possible_answers_temp = pd.read_sql(query, conn)
    

    if possible_answers_temp.empty: 
        print("0 answers in list") 
        break

    ranked_answers = answer_ranking()
    # "updates" df to filtered words 
    possible_answers_df = possible_answers_df.iloc[0:0]
    possible_answers_df['Possible_Words'] = possible_answers_temp[['Possible_Words']].copy()
   
    #for i in range(len(possible_answers_temp['Possible_Words'])): print(ranked_answers[i])
    print("\n".join(ranked_answers))

    print(len(possible_answers_temp['Possible_Words']), ' possible answers in list')
    if len(possible_answers_temp['Possible_Words']) == 0: break
   
    word_count+=1
  
    while solved != 'y' and solved != 'n': solved = str(input("was it solved y/n?  "))




