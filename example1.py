# -*- coding: utf-8 -*-
"""
Example from https://docs.python.org/3/howto/argparse.html

to compute x**y
"""

from argui import GUI

g = GUI('Example')
g.numeric_entry('the base', 0.0, id='x')
g.numeric_entry("the exponent", 0.0, id='y')
g.dropdown('verbosity', ['answer only','brief','full'], init='brief')
g.buttons('_', ['Go'])
g.on('Go', g.destroy)
    
args = g.run()
answer = args['x']**args['y']
if args['verbosity'] =='full':
    print(f"{args['x']} to the power {args['y']} equals {answer}")
elif args['verbosity'] =='brief':
    print(f"{args['x']}**{args['y']} == {answer}")
else:
    print(answer)