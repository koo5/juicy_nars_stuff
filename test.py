# -*- coding: utf-8 -*-
from __future__ import unicode_literals
str = unicode

import glob, json

from java.lang import StringBuilder

import nars
import nars.core, nars.build
n=nars.core.NAR(nars.build.Default())
from nars.io.narsese import Narsese

from nars.logic.entity import Task, Sentence, Statement, Term, CompoundTerm, Variable
from nars.logic.entity import BudgetValue as Budget, TruthValue as Truth

from nars.logic import nal1, nal2, nal3, nal4, nal5
from nars.logic.nal5 import Implication
from nars.logic.nal8 import Operation

p = Narsese(n)



#stand-ins for rules of narsese bnf that dont translate to nars classes

class Copula(object):
	pass

class Tense(object):
	def __init__(s, something):
		pass



#bnf helpers

class sym(object):
	def __init__(s, **name_type):
		s.name, s.type = name_type.items()[0]
	def __repr__(s):
		return "sym" + str({'name':s.name, 'type':s.type})
	

class optional(object):
	def __init__(s, *seq):
		s.seq = list(seq)
#		print 'optional:'+str(s.seq)

class oneormore(object):
	def __init__(s, *vargs):
		s.seq = vargs


#future nengo widgets

class Node(object):
	def __init__(s):
		s.alternative = 0
	def changeAlternative(s, by):
		new = s.alternative + by
		if s.alternativeValid(new):
			s.alternative = new
	def alternativeValid(s, a):
		return False

class Syntaxed(Node):
	def __init__(s, rule, **kids):
		super(Syntaxed,s).__init__()
		s.rule = rule
		s.kids = kids
	def dump(s):
		return {'self':str(s),'rule':s.rule,'kids':s.kids}
	def alternativeValid(s, a):
		return 0 <= a < len(s.alts)
	@property
	def alts(s):
		return grammar[s.rule]
	def verbalize(s):
		#print "wtf",s.rule, s.alternative, grammar[s.rule][s.alternative]
		#print_grammar()
		for i in grammar[s.rule][s.alternative]:
			print "verbalizing "+repr(i)
			if type(i) == unicode:
				yield i
			elif type(i) == oneormore: pass#tbd
			elif i.name in s.kids:
				for j in s.kids[i.name].verbalize():
					yield j
			else: raise Exception(str(i) + " not in " + str(s.dump()))


class Word(Node):
	def __init__(s, value):
		super(Word, s).__init__()
		s.value = value
		assert type(value) == unicode,  value
	def verbalize(s):
		return [s.value]
		
	

class Number(Word):
	def __init__(s, value):
		super(Number, s).__init__(unicode(value))

class List(Node):
	pass





def n2l(inp):
	"""create gui widgets from nars.logic.entity terms"""

	cls = inp.__class__

	#print inp, cls


	if cls == Task:
		return Syntaxed(Task, budget=n2l(inp.budget), sentence=n2l(inp.sentence))

	elif cls == Sentence:
		return Syntaxed(Sentence, statement=n2l(inp.term),
						tense=n2l(Tense(inp.getTemporalOrder())),
						truth=n2l(inp.getTruth()))

	elif cls == Budget:
		return Syntaxed(Budget, priority=n2l(inp.getPriority()), durability=n2l(inp.getDurability()))
	elif cls == Truth:
		return Syntaxed(Truth , priority=n2l(inp.getFrequency()), durability=n2l(inp.getConfidence()))

	elif cls == Tense:
		r = Syntaxed(Tense)
		r.variant = 0#eternal, todo
		return r

	elif cls in compound_terms:
		r=Syntaxed(CompoundTerm, term=n2l(inp.term[0]))
		r.alternative = compound_terms.index(cls)
		return r

	#better use operator() and simplify it all
	elif cls in copuled:
		r = Syntaxed('copuled', 	subject=n2l(inp.getSubject()),
						copula=Syntaxed(Copula),
						predicate=n2l(inp.getPredicate()))
		r.kids['copula'].alternative = copuled.index(cls)
		return r



	elif cls == Implication:
		r=Syntaxed(Implication)
		#todo
		return r

	elif cls == Operation:
		r=Syntaxed(cls)#, word=inp)...
		return r


	elif cls == float:
		return Number(inp)

	elif cls == Term:
		return Word(inp.toString())

	elif inp == None:
		return "NONONO"
	
	else: raise Exception( "implement:"+str(cls))





# test

def main():
	print "hi, output:"
	for fn in glob.glob("/home/kook/opennars/nal/*/*.nal"):
		print fn
		f = open(fn, "r")
		for l in f:
			l = l.strip()
			print "input:" + l
		
			if len(l) == 0:
				continue
			if l.isdigit():
				continue

			if any([l.startswith(x) for x in ["***",  "'", "/"]]):
				continue
			if any([l.startswith(x) for x in ["Solved", 'Result', "Which"]]):
				break
	
			try:
				t=p.parseNarsese(StringBuilder(l))
			except nars.io.narsese.InvalidInputException:
				break
			
			if t == None:
				break

			print "nars:"+str(t)

			node = n2l(t)

			print "node:"+nice(node)
			print "back:"+"".join(node.verbalize())
			
			print
			print




grammar = {
Task:[		[optional(Budget), Sentence]],
Sentence:[	[Statement, ".", optional(Tense), optional(Truth)],
		[Statement, "?", optional(Tense)],
		[Statement, "@", optional(Tense)],
		[Statement, "!", optional(Truth)]],
Statement:[	[sym(copuled='copuled')],[Term],[Operation]],
Term:[		[Word],[Variable],[CompoundTerm],[Statement]],
Operation:[	["(^", Word, oneormore([",",Term]), ")"]],
'copuled':[	["<", sym(subject=Term), Copula, sym(predicate=Term), ">"]],
Copula:[	["-->"],nal1.Inheritance,
		["<->"],nal2.Similarity,
		["{--"],0,
		["--]"],0,
		["{-]"],0,
		["==>"],0,
		["=/>"],0,
		["=|>"],0,
		["=\>"],0,
		["<=>"],nal5.Equivalence,
		["</>"],0,
		["<|>"],0
		],
CompoundTerm:[	#todo:ensure unique sym names in postprocessing, make oneormore equal with List or try something more complex?
		["{",   Term, oneormore(",", Term),"}"], nal3.SetExt,
		["[",   Term, oneormore(",", Term), "]"],nal3.SetInt,
		["(&,", Term, oneormore(",", Term), ")"],nal3.IntersectionExt,
		["(|,", Term, oneormore(",", Term), ")"],nal3.IntersectionInt,
		["(-,", Term, ",", Term, ")"],		nal3.DifferenceExt,
		["(~,", Term, ",", Term, ")"],		nal3.DifferenceInt,
		["(*,", Term, oneormore(",", Term), ")"],nal4.Product,
		["(/,", Term, oneormore(",", Term), ")"],nal4.ImageExt,
		["(\,", Term, oneormore(",", Term), ")"],nal4.ImageInt,
		["(--,",Term, ")"],			nal1.Negation,
		["(||,",Term, oneormore(",", Term), ")"],nal5.Disjunction,
		["(&&,",Term, oneormore(",", Term), ")"],nal5.Conjunction,
		["(&/,",Term, oneormore(",", Term), ")"],nal5.Conjunction,
		["(&|,",Term, oneormore(",", Term), ")"],nal5.Conjunction],
Implication:[	["=|>"],["=/>"]],
Variable:[	["$", Word],
		["#",optional(Word)],
		["?",optional(Word)]],
Tense:[		["eternal"],[":/:"],[":|:"],[":\:"]],
Truth:[		["%",sym(frequency=Number),optional(";",sym(confidence=Number)),"%"]],
Budget:[	["$",sym(priority=Number), optional(";",sym(durability=Number)),"$"]]}





# some ugly processing of the grammar above into something more machine friendly





def flatten_optionals(grammar):
	"""the goal is to find all optional()'s in the variants of rules of this grammar
	and replace each variant containing it with two nev variants, one with the optional 
	item and one without it"""
 	for v in grammar.values():
		print v
		explode_optionals_in_rule(v)

def explode_optionals_in_rule(rule):
	for seq in rule:
		o = find_optional_in_seq(seq)
		if o != -1:
			rule.append(seq[:o]+seq[o].seq+seq[1+o:])
			del seq[o]
			print rule
			explode_optionals_in_rule(rule)

def find_optional_in_seq(s):
	for i in s:
		if type(i) == optional:
			return s.index(i);
	return -1;






#extract Copula and CompoundTerm classess

compound_terms = grammar[CompoundTerm][1::2]
grammar[CompoundTerm]=grammar[CompoundTerm][::2]

copuled = grammar[Copula][1::2]
grammar[Copula] = grammar[Copula][::2]






flatten_optionals(grammar)



for v in grammar.values():
	for alt in v:
		for i,v in enumerate(alt):
			if type(v) not in [unicode, oneormore, sym]:
				name = v.__name__.lower()
				clashes_count = len([existing for existing in alt if type(existing) == sym and existing.name == name ])
				if clashes_count:
					name += str(clashes_count + 1)
				alt[i] = sym(**{name:v})
			




# json debug out

def nice(x):
	return json.dumps(x, indent=4, sort_keys = True, separators=(',', ': '), cls=ComplexEncoder)

class ComplexEncoder(json.JSONEncoder):
	def default(self, obj):
		try:
			return json.JSONEncoder.default(self, obj)
		except TypeError: #crap
			if isinstance(obj, Syntaxed):
				return obj.dump()
			else:
				return repr(obj)

def print_grammar():
	print "grammar:"
	for k,v in grammar.iteritems():
		print str(k)+": "+nice(v)
	#exit()






if __name__ == "__main__":
	main()
	