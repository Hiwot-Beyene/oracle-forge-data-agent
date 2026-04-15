code = """import pandas as pd
import re

books_info_df = pd.DataFrame(locals()['var_tool_query_db_e5l18T9N0P21lG4a4cWX'])
review_df = pd.DataFrame(locals()['var_tool_query_db_vI0qfS2nL5aRjJjsb2iX'])

def extract_year(details):
    if not isinstance(details, str):
        return None
    match = re.search(r'\b(19[8-9]\d|20\d{2})\b', details)
    if match:
        return int(match.group(1))
    return None

books_info_df['publication_year'] = books_info_df['details'].apply(extract_year)
# Minor data cleaning for purchase_id in review_df
review_df['purchase_id'] = review_df['purchase_id'].str.replace("purchaseid_", "bookid_")
merged_df = pd.merge(books_info_df, review_df, left_on='book_id', right_on='purchase_id')
merged_df['rating'] = pd.to_numeric(merged_df['rating'])
merged_df = merged_df.dropna(subset=['publication_year'])
merged_df['decade'] = (merged_df['publication_year'] // 10) * 10
decade_stats = merged_df.groupby('decade').agg(avg_rating=('rating', 'mean'), distinct_books=('book_id', 'nunique')).reset_index()
decades_with_10_books = decade_stats[decade_stats['distinct_books'] >= 10]
highest_rated_decade = decades_with_10_books.loc[decades_with_10_books['avg_rating'].idxmax()]

result = str(int(highest_rated_decade["decade"])) + "s"
print("__RESULT__:")
print(f'"{result}"')"""

env_args = {'var_tool_list_db_XmbKsCH3iQyTlIOtsVPc': ['books_info'], 'var_tool_query_db_Jxrp6rHzULh8jX04lkb7': [{'details': 'Published by Chatto & Windus, the first edition of this book was released on January 1, 2004. It is written in English and comes in a hardcover format, comprising 196 pages. The book has an ISBN-10 of 0701169850 and an ISBN-13 of 978-0701169855. Weighing 10.1 ounces, its dimensions are 5.39 x 0.71 x 7.48 inches.'}, {'details': 'This book, published by Heinemann in its first edition on May 20, 1996, is written in English and is available in paperback format, consisting of 316 pages. It has an ISBN-10 of 0435088688 and an ISBN-13 of 978-0435088682. The item weighs 1.05 pounds and its dimensions are 6.03 x 0.67 x 8.95 inches.'}, {'details': 'This book, published by Little, Brown and Company in its first edition on May 8, 2012, is available in English and is bound as a hardcover with a total of 384 pages. It has an ISBN-10 of 9780316185363 and an ISBN-13 of 978-0316185363. The item weighs 1.4 pounds and its dimensions are 6.25 inches in width, 1.55 inches in depth, and 9.55 inches in height.'}, {'details': 'This book, published by Scholastic Paperbacks in a reprint edition on October 29, 2013, is written in English and consists of 64 pages. It has an ISBN-10 of 0545425573 and an ISBN-13 of 978-0545425575. The reading age is suitable for children between 7 and 10 years old, and it corresponds to a Lexile measure of 590L. The book is appropriate for students in grades 2 through 5. Weighing 1.92 ounces, its dimensions are 5.25 x 0.2 x 7.5 inches.'}, {'details': 'The book was published on May 18, 2014, and is available in English. It has a file size of 1542 KB and allows for unlimited simultaneous device usage. Text-to-speech functionality is enabled, and it supports screen readers, enhancing accessibility for readers. Enhanced typesetting is also enabled, while the X-Ray feature is not available. Word Wise is enabled to assist with comprehension, and sticky notes can be used on Kindle Scribe. The print length of the book is 233 pages.'}], 'var_tool_query_db_2iyD1Nu49cwTMJuTw3T8': 'file_storage/tool_query_db_2iyD1Nu49cwTMJuTw3T8.json', 'var_tool_query_db_0fpdVdqBPwLPx1oe9oui': 'file_storage/tool_query_db_0fpdVdqBPwLPx1oe9oui.json'}

exec(code, env_args)
