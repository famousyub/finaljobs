import tika
from tika import parser
parsed = parser.from_file('./sample.pdf')
print(parsed["metadata"])
print(parsed["content"])