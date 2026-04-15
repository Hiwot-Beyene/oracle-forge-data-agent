code = """import pandas as pd
import json
import re
import math

# Load results
# The keys are: var_tool_query_db_xMvmHoVK4IVi7nYFaFWK (limit 5 details)
# var_tool_query_db_46wd3IwDR8rynIszRsfE (all details)
# var_tool_query_db_6yGfHwuX6spaBIpwI9Vx (reviews)

# Let's inspect the types
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

# Extract year from details using a refined regex pattern
def extract_year(details):
    if not isinstance(details, str):
        return None
    # Looking for a 4-digit number that starts with 18, 19, or 20
    match = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', details)
    if match:
        year = int(match.group(1))
        if 1800 <= year <= 2024:
            return year
    return None

books_df['year'] = books_df['details'].apply(extract_year)
books_df = books_df.dropna(subset=['year'])

# Map year to decade
def get_decade(year):
    return f"{math.floor(year / 10) * 10}s"

books_df['decade'] = books_df['year'].apply(get_decade)

# Extract numeric ID for join
books_df['id_num'] = books_df['book_id'].str.extract(r'(\d+)').astype(int)
reviews_df['id_num'] = reviews_df['purchase_id'].str.extract(r'(\d+)').astype(int)

# Ensure 'rating' is numeric
reviews_df['rating'] = pd.to_numeric(reviews_df['rating'])

# Merge dataframes
merged_df = pd.merge(reviews_df, books_df, on='id_num', how='inner')

# Calculate distinct books per decade
distinct_books_per_decade = merged_df.groupby('decade')['id_num'].nunique().reset_index()
distinct_books_per_decade.columns = ['decade', 'distinct_books']

# In multiple-review-per-book scenarios, "average rating among decades" could mean:
# Approach A: The average of all review ratings in that decade.
avg_review_rating_per_decade = merged_df.groupby('decade')['rating'].mean().reset_index()
avg_review_rating_per_decade.columns = ['decade', 'avg_review_rating']

# Approach B: The average of the average rating of each book in that decade.
book_avgs = merged_df.groupby(['decade', 'id_num'])['rating'].mean().reset_index()
avg_book_rating_per_decade = book_avgs.groupby('decade')['rating'].mean().reset_index()
avg_book_rating_per_decade.columns = ['decade', 'avg_book_rating']

# Combine both approaches
result_df = pd.merge(distinct_books_per_decade, avg_review_rating_per_decade, on='decade')
result_df = pd.merge(result_df, avg_book_rating_per_decade, on='decade')

# Filter for decades with at least 10 distinct books rated
valid_decades = result_df[result_df['distinct_books'] >= 10]

res_out = valid_decades.to_dict(orient='records')

print("__RESULT__:")
print(json.dumps(res_out))"""

env_args = {'var_tool_query_db_xMvmHoVK4IVi7nYFaFWK': [{'details': 'Published by Chatto & Windus, the first edition of this book was released on January 1, 2004. It is written in English and comes in a hardcover format, comprising 196 pages. The book has an ISBN-10 of 0701169850 and an ISBN-13 of 978-0701169855. Weighing 10.1 ounces, its dimensions are 5.39 x 0.71 x 7.48 inches.'}, {'details': 'This book, published by Heinemann in its first edition on May 20, 1996, is written in English and is available in paperback format, consisting of 316 pages. It has an ISBN-10 of 0435088688 and an ISBN-13 of 978-0435088682. The item weighs 1.05 pounds and its dimensions are 6.03 x 0.67 x 8.95 inches.'}, {'details': 'This book, published by Little, Brown and Company in its first edition on May 8, 2012, is available in English and is bound as a hardcover with a total of 384 pages. It has an ISBN-10 of 9780316185363 and an ISBN-13 of 978-0316185363. The item weighs 1.4 pounds and its dimensions are 6.25 inches in width, 1.55 inches in depth, and 9.55 inches in height.'}, {'details': 'This book, published by Scholastic Paperbacks in a reprint edition on October 29, 2013, is written in English and consists of 64 pages. It has an ISBN-10 of 0545425573 and an ISBN-13 of 978-0545425575. The reading age is suitable for children between 7 and 10 years old, and it corresponds to a Lexile measure of 590L. The book is appropriate for students in grades 2 through 5. Weighing 1.92 ounces, its dimensions are 5.25 x 0.2 x 7.5 inches.'}, {'details': 'The book was published on May 18, 2014, and is available in English. It has a file size of 1542 KB and allows for unlimited simultaneous device usage. Text-to-speech functionality is enabled, and it supports screen readers, enhancing accessibility for readers. Enhanced typesetting is also enabled, while the X-Ray feature is not available. Word Wise is enabled to assist with comprehension, and sticky notes can be used on Kindle Scribe. The print length of the book is 233 pages.'}], 'var_tool_query_db_46wd3IwDR8rynIszRsfE': 'file_storage/tool_query_db_46wd3IwDR8rynIszRsfE.json', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx': 'file_storage/tool_query_db_6yGfHwuX6spaBIpwI9Vx.json', 'var_tool_execute_python_iMsGAbEfe6udau3ECtIV': ['var_tool_query_db_xMvmHoVK4IVi7nYFaFWK', 'var_tool_query_db_46wd3IwDR8rynIszRsfE', 'var_tool_query_db_6yGfHwuX6spaBIpwI9Vx', '__builtins__', 'pd', 'json', 're', 'books_data']}

exec(code, env_args)
