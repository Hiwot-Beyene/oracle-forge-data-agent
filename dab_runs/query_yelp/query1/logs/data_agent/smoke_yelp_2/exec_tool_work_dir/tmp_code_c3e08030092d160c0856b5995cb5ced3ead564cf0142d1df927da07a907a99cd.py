code = """import json

# The query result is a list with a single dictionary
result = var_toolu_bdrk_01GaK5eQq5RWz1fGUSN9Pj4f[0]

print("__RESULT__:")
print(json.dumps(result['average_rating']))"""

env_args = {'var_toolu_bdrk_015JmqXhPgiuNzJr24HwMktW': [], 'var_toolu_bdrk_01GsfdrFSYxnH6SSEggtJj9v': ['review', 'tip', 'user'], 'var_toolu_bdrk_01GaK5eQq5RWz1fGUSN9Pj4f': [{'average_rating': '4.333333333333333'}]}

exec(code, env_args)
