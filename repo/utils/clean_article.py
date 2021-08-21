import re


BLUE = '\033[94m'
RED= '\033[93m'
GREEN = '\033[92m'
END = '\033[0m'
ref = 'references,reference,literature'.split(',')

class Cleaner:
	def __init__(self, article):
		self.article = article

def find_reference(text):
	indices = []
	for i,line in enumerate(text.split('\n')):
		if line.lower().strip() in ref:
			indices.append(i)
	return indices


def show_reference(text, extra = 5):
	text = remove_extra_eol(text)
	indices = find_reference(text)
	text = text.split('\n')
	for index in indices:
		start, end = index - extra, index + extra
		if start < 0: start = 0
		if end > len(text): end = len(text)
		print(RED+ '-'*9 + END)
		print('\n'.join(text[start:index]), index)
		print(BLUE + text[index] + END)
		print('\n'.join(text[index+1:end]))

def show_reference_articles(articles, verbose=True):
	no_references = []
	with_references = []
	multiple_reference_sections = 0
	for a in articles:
		indices = find_reference(a.pdftotext.text)
		if len(indices) > 1: multiple_reference_sections += 1
		if indices: with_references.append(a)
		else: no_references.append(a)
		if verbose:
			print(GREEN + a.__str__() + END)
			show_reference(a.pdftotext.text)
	print('no reference found:',len(no_references),
		'reference found:',len(with_references),
		'multiple_reference_sections:',multiple_reference_sections)
	return no_references, with_references

def remove_extra_eol(text):
	return re.sub('\n+','\n',text)


def alternative_reference_finder(text):
	for r in ref:
		pass

def collect_references(articles):
	no_ref,ref = show_reference_articles(articles, verbose = False)
	refs = []
	for article in ref:
		index = max(find_reference(article.pdftotext.text))
		refs.append(article.pdftotext.text[index:])
	return refs


	
