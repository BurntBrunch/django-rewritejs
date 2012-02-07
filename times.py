
from timeit import Timer

args = ["""import urllib2 """,
"""urllib2.urlopen('http://localhost:8000').read()"""]

timer1 = Timer(stmt=args[1], setup=args[0])

print "100 requests, 3 times:", timer1.repeat(repeat=3, number=100)

