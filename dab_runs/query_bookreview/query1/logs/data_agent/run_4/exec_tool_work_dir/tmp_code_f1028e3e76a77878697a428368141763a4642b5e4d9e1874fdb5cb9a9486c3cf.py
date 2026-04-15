code = """import pandas as pd
import json
import re
import math

books_var = locals()['var_tool_query_db_46wd3IwDR8rynIszRsfE']
if isinstance(books_var, str):
    with open(books_var, 'r') as f:
        books_data = json.load(f)
else:
    books_data = books_var

books_df = pd.DataFrame(books_data)

def extract_year(details):
    if not isinstance(details, str):
        return None
    # Let's find dates like "January 1, 2004" or "May 18, 2014" or "in 2004"
    # Find all 4 digit numbers
    all_years = re.findall(r'\b(19\d{2}|20\d{2})\b', details)
    
    # We want the year of publication. Often it's preceded by a month and day, or "released on", "published ... on".
    # Let's extract them and return the last valid year mentioned, or maybe just look for typical date patterns first.
    
    # Pattern 1: Month DD, YYYY
    date_match = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, (\d{4})', details)
    if date_match:
        return int(date_match.group(1))
    
    # Pattern 2: Month YYYY
    date_match2 = re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})', details)
    if date_match2:
        return int(date_match2.group(1))
        
    if all_years:
        # Just return the first one found that could be a year
        for y in all_years:
            if 1800 <= int(y) <= 2024:
                return int(y)
    return None

books_df['year'] = books_df['details'].apply(extract_year)
years = books_df['year'].value_counts(dropna=False).to_dict()

res = {
    'total': len(books_df),
    'years': years
}
print("__RESULT__:")
print(json.dumps(res))"""

env_args = {'var_tool_query_db_xMvmHoVK4IVi7nYFaFWK': [{'details': 'Published by Chatto & Windus, the first edition of this book was released on January 1, 2004. It is written in English and comes in a hardcover format, comprising 196 pages. The book has an ISBN-10 of 0701169850 and an ISBN-13 of 978-0701169855. Weighing 10.1 ounces, its dimensions are 5.39 x 0.71 x 7.48 inches.'}, {'details': 'This book, published by Heinemann in its first edition on May 20, 1996, is written in English and is available in paperback format, consisting of 316 pages. It has an ISBN-10 of 0435088688 and an ISBN-13 of 978-0435088682. The item weighs 1.05 pounds and its dimensions are 6.03 x 0.67 x 8.95 inches.'}, {'details': 'This book, published by Little, Brown and Company in its first edition on May 8, 2012, is available in English and is bound as a hardcover with a total of 384 pages. It has an ISBN-10 of 9780316185363 and an ISBN-13 of 978-0316185363. The item weighs 1.4 pounds and its dimensions are 6.25 inches in width, 1.55 inches in depth, and 9.55 inches in height.'}, {'details': 'This book, published by Scholastic Paperbacks in a reprint edition on October 29, 2013, is written in English and consists of 64 pages. It has an ISBN-10 of 0545425573 and an ISBN-13 of 978-0545425575. The reading age is suitable for children between 7 and 10 years old, and it corresponds to a Lexile measure of 590L. The book is appropriate for students in grades 2 through 5. Weighing 1.92 ounces, its dimensions are 5.25 x 0.2 x 7.5 inches.'}, {'details': 'The book was published on May 18, 2014, and is available in English. It has a file size of 1542 KB and allows for unlimited simultaneous device usage. Text-to-speech functionality is enabled, and it supports screen readers, enhancing accessibility for readers. Enhanced typesetting is also enabled, while the X-Ray feature is not available. Word Wise is enabled to assist with comprehension, and sticky notes can be used on Kindle Scribe. The print length of the book is 233 pages.'}], 'var_tool_query_db_46wd3IwDR8rynIszRsfE': 'file_storage/tool_query_db_46wd3IwDR8rynIszRsfE.json', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx': 'file_storage/tool_query_db_6yGfHwuX6spaBIpwI9Vx.json', 'var_tool_execute_python_iMsGAbEfe6udau3ECtIV': ['var_tool_query_db_xMvmHoVK4IVi7nYFaFWK', 'var_tool_query_db_46wd3IwDR8rynIszRsfE', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx', '__builtins__', 'pd', 'json', 're', 'books_data'], 'var_tool_execute_python_lrt6X8sFGoXYyQB0J00E': [], 'var_tool_execute_python_HG8pNWewpWRj8TkFlgfi': {'books_rows': 200, 'reviews_rows': 1833}}

exec(code, env_args)
