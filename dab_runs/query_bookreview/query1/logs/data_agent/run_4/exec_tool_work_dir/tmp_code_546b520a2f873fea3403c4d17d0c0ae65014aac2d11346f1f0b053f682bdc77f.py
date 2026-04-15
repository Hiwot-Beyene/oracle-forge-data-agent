code = """import pandas as pd
import json
import re
import math

books_var = locals()['var_tool_query_db_46wd3IwDR8rynIszRsfE']
reviews_var = locals()['var_tool_query_db_6yGfHwuX6spaBIpwI9Vx']

if isinstance(books_var, str):
    with open(books_var, 'r') as f:
        books_data = json.load(f)
else:
    books_data = books_var

if isinstance(reviews_var, str):
    with open(reviews_var, 'r') as f:
        reviews_data = json.load(f)
else:
    reviews_data = reviews_var

books_df = pd.DataFrame(books_data)
reviews_df = pd.DataFrame(reviews_data)

def extract_year(details):
    if not isinstance(details, str):
        return None
    date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, (\d{4})', details)
    if date_match:
        return int(date_match.group(1))
    
    date_match2 = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})', details)
    if date_match2:
        return int(date_match2.group(1))
        
    all_years = re.findall(r'\b(19\d{2}|20\d{2}|18\d{2})\b', details)
    if all_years:
        for y in all_years:
            if 1800 <= int(y) <= 2024:
                return int(y)
    return None

books_df['year'] = books_df['details'].apply(extract_year)
books_df = books_df.dropna(subset=['year'])

def get_decade(year):
    return f"{math.floor(year / 10) * 10}s"

books_df['decade'] = books_df['year'].apply(get_decade)
books_df['id_num'] = books_df['book_id'].str.extract(r'(\d+)').astype(int)
reviews_df['id_num'] = reviews_df['purchase_id'].str.extract(r'(\d+)').astype(int)
reviews_df['rating'] = pd.to_numeric(reviews_df['rating'])

merged_df = pd.merge(reviews_df, books_df, on='id_num', how='inner')

# Calculate distinct books per decade
distinct_books_per_decade = merged_df.groupby('decade')['id_num'].nunique().reset_index()
distinct_books_per_decade.columns = ['decade', 'distinct_books']

# Usually average rating per decade is calculated by averaging all ratings in that decade
avg_review_rating = merged_df.groupby('decade')['rating'].mean().reset_index()
avg_review_rating.columns = ['decade', 'avg_review']

# Alternatively, average rating per decade is calculated by average of book averages
book_avgs = merged_df.groupby(['decade', 'id_num'])['rating'].mean().reset_index()
avg_book_rating = book_avgs.groupby('decade')['rating'].mean().reset_index()
avg_book_rating.columns = ['decade', 'avg_book']

res_df = pd.merge(distinct_books_per_decade, avg_review_rating, on='decade')
res_df = pd.merge(res_df, avg_book_rating, on='decade')

valid = res_df[res_df['distinct_books'] >= 10]

# Sort by avg review rating
valid = valid.sort_values(by='avg_review', ascending=False)
try:
    best_review = valid.iloc[0]['decade']
except:
    best_review = None

# Sort by avg book rating
valid_book = valid.sort_values(by='avg_book', ascending=False)
try:
    best_book = valid_book.iloc[0]['decade']
except:
    best_book = None
    
res = {
    'valid_decades': valid.to_dict(orient='records'),
    'best_review': best_review,
    'best_book': best_book
}
print("__RESULT__:")
print(json.dumps(res))"""

env_args = {'var_tool_query_db_xMvmHoVK4IVi7nYFaFWK': [{'details': 'Published by Chatto & Windus, the first edition of this book was released on January 1, 2004. It is written in English and comes in a hardcover format, comprising 196 pages. The book has an ISBN-10 of 0701169850 and an ISBN-13 of 978-0701169855. Weighing 10.1 ounces, its dimensions are 5.39 x 0.71 x 7.48 inches.'}, {'details': 'This book, published by Heinemann in its first edition on May 20, 1996, is written in English and is available in paperback format, consisting of 316 pages. It has an ISBN-10 of 0435088688 and an ISBN-13 of 978-0435088682. The item weighs 1.05 pounds and its dimensions are 6.03 x 0.67 x 8.95 inches.'}, {'details': 'This book, published by Little, Brown and Company in its first edition on May 8, 2012, is available in English and is bound as a hardcover with a total of 384 pages. It has an ISBN-10 of 9780316185363 and an ISBN-13 of 978-0316185363. The item weighs 1.4 pounds and its dimensions are 6.25 inches in width, 1.55 inches in depth, and 9.55 inches in height.'}, {'details': 'This book, published by Scholastic Paperbacks in a reprint edition on October 29, 2013, is written in English and consists of 64 pages. It has an ISBN-10 of 0545425573 and an ISBN-13 of 978-0545425575. The reading age is suitable for children between 7 and 10 years old, and it corresponds to a Lexile measure of 590L. The book is appropriate for students in grades 2 through 5. Weighing 1.92 ounces, its dimensions are 5.25 x 0.2 x 7.5 inches.'}, {'details': 'The book was published on May 18, 2014, and is available in English. It has a file size of 1542 KB and allows for unlimited simultaneous device usage. Text-to-speech functionality is enabled, and it supports screen readers, enhancing accessibility for readers. Enhanced typesetting is also enabled, while the X-Ray feature is not available. Word Wise is enabled to assist with comprehension, and sticky notes can be used on Kindle Scribe. The print length of the book is 233 pages.'}], 'var_tool_query_db_46wd3IwDR8rynIszRsfE': 'file_storage/tool_query_db_46wd3IwDR8rynIszRsfE.json', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx': 'file_storage/tool_query_db_6yGfHwuX6spaBIpwI9Vx.json', 'var_tool_execute_python_iMsGAbEfe6udau3ECtIV': ['var_tool_query_db_xMvmHoVK4IVi7nYFaFWK', 'var_tool_query_db_46wd3IwDR8rynIszRsfE', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx', '__builtins__', 'pd', 'json', 're', 'books_data'], 'var_tool_execute_python_lrt6X8sFGoXYyQB0J00E': [], 'var_tool_execute_python_HG8pNWewpWRj8TkFlgfi': {'books_rows': 200, 'reviews_rows': 1833}, 'var_tool_execute_python_Xu1vmtfvuImivWHcnBXU': {'total': 200, 'years': {'2012.0': 12, 'NaN': 11, '2016.0': 11, '2018.0': 11, '2019.0': 10, '2017.0': 10, '2020.0': 10, '2015.0': 9, '2006.0': 9, '2014.0': 8, '2004.0': 7, '2013.0': 7, '2010.0': 7, '2021.0': 6, '2005.0': 6, '2008.0': 5, '2001.0': 5, '1997.0': 4, '1987.0': 4, '2007.0': 4, '1996.0': 3, '2022.0': 3, '2000.0': 3, '2003.0': 3, '1995.0': 3, '1983.0': 3, '2011.0': 3, '2009.0': 3, '2023.0': 2, '1998.0': 2, '1990.0': 2, '1994.0': 1, '1993.0': 1, '1945.0': 1, '1939.0': 1, '1986.0': 1, '1979.0': 1, '1991.0': 1, '1985.0': 1, '1989.0': 1, '1885.0': 1, '1930.0': 1, '1975.0': 1, '2002.0': 1, '1982.0': 1}}}

exec(code, env_args)
