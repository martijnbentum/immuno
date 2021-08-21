import glob
import sys
import textract
from articles.models import ExtractionType, Article, Text
from PyPDF2 import PdfFileReader

pdf_dir = '/vol/tensusers/mbentum/immuno/pdf/'

def create_extraction_types():
	for name in 'pdfminer,pdftotext,ocr'.split(','):
		instance = ExtractionType(name = name)	
		try:instance.save()
		except:print('could not save extraction_type:',name)

def get_all_pdf_filenames():
	return glob.glob(pdf_dir + '*.pdf')


def get_pypdf(filename):
	fin = open(filename,'rb') 
	return PdfFileReader(fin)

def get_pdf_info(filename='', pdf = None):
	if not pdf: pdf = get_pypdf(filename)
	try: info = pdf.getDocumentInfo()
	except:info = {'error':str(sys.exc_info())}
	return info

def extract_text_from_pdf(filename, method = 'pdfminer'):
	if method == 'ocr':method='tesseract'
	return textract.process(filename,method=method).decode()

def make_text(filename,method = 'pdfminer', save = True):
	et = ExtractionType.objects.get(name=method)
	error = False
	try:t = extract_text_from_pdf(filename, method)
	except:
		t = str(sys.exc_info())
		error = True
	instance = Text(filename=filename, text = t, extraction_type = et, 
		error = error)
	if save:
		try: instance.save()
		except:print('could not save text:',filename,instance,sys.exc_info())
	return instance

def make_article(filename, save = True):
	pdf = get_pypdf(filename)
	info = get_pdf_info(pdf=pdf)
	npages = pdf.getNumPages()
	ocr = make_text(filename,method='ocr')
	pdftotext= make_text(filename,method='pdftotext')
	pdfminer= make_text(filename,method='pdfminer')
	error = 'error' in info.keys()
	instance = Article(filename=filename,ocr=ocr,pdftotext=pdftotext,
		pdfminer=pdfminer,info=info, error=error)
	if save:
		try: instance.save()
		except:print('could not save article:',filename,instance,sys.exc_info())
	return instance


def add_articles(start = 0):
	fn = get_all_pdf_filenames()
	for i,f in enumerate(fn[start:]):
		print(f,i,len(fn[start:]))
		make_article(f)

