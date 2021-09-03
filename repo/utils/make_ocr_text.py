import pytesseract
from pdf2image import convert_from_path
from articles.models import Article
from utils.clean_article import BLUE, GREEN, RED, END
from utils import tesseract
import os

ocr_dir = '../OCR_TEXT/'

filename_taken = 'filename_taken' 
filename_done = 'filename_done' 


def make_output_text(output_dir = '../articles/'):
	clean_dir = output_dir + 'clean/'
	junk_dir = output_dir + 'removed_texts/'
	if not os.path.isdir(output_dir):os.mkdir(output_dir)
	if not os.path.isdir(clean_dir):os.mkdir(clean_dir)
	if not os.path.isdir(junk_dir):os.mkdir(junk_dir)
	articles = Article.objects.all()
	make_year_file(articles, output_dir)
	for a in articles:
		pdf = tesseract.Pdf(a.filename)
		text = pdf.text()
		junk = pdf.text(only_page_numbers=True,return_non_usable_text=True)
		with open(clean_dir + pdf.filename + '.txt','w') as fout:
			fout.write(text)
		with open(junk_dir+ pdf.filename + '.txt','w') as fout:
			fout.write(junk)



def make_year_file(articles, output_dir):
	output = []
	for a in articles:
		output.append([a.filename.split('/')[-1],str(a.year)])
	with open(output_dir+'article_names_and_years.txt','w') as fout:
		fout.write('\n'.join(['\t'.join(l) for l in output]))
		
	
	

def get_info():
	filenames,last_pages = [], []
	a = Article.objects.all()
	for x in a:
		filenames.append(x.filename)
		if x.layout:
			last_pages.append(x.layout.reference_pagenumber)
		else: last_pages.append(None)
	assert len(filenames) == len(last_pages)
	return filenames, last_pages

		
def pdf2text(filename, last_page= None, dpi = 500,verbose = False, 
	force_save=False):
	if verbose:print(BLUE+'handling:'+END,filename)
	if not force_save and check_filename_done(filename):
		print(RED,'filename:',filename,'already processed, doing nothing',END)
		return
	if check_filename_available(filename): write_taken(filename)
	else: 
		print(RED,'filename:',filename,'is being processed, doing nothing',END)
		return
	pages = convert_from_path(filename,dpi,last_page=last_page)
	for i,page in enumerate(pages):
		f=ocr_dir+filename.split('/')[-1].strip('.pdf')+'_pagenumber_' + str(i+1) 
		if os.path.isfile(f) and not force_save: 
			if verbose:
				print(BLUE+'already saved:',END,f,GREEN,'doing nothing',END)
				continue
		if verbose:print(BLUE+'saving:'+END,GREEN+f+END)
		text = pytesseract.image_to_data(page)
		with open(f,'w') as fout:
			fout.write(text)
	write_done(filename)


def make_ocr(filenames = None, last_pages = None, dpi = 500, force_save=False):
	if filenames == None:
		filenames, last_pages = get_info()
	assert len(filenames) == len(last_pages)
	i = 0
	for filename, last_page in zip(filenames,last_pages):
		print(i,len(filenames))
		pdf2text(filename, last_page, dpi, verbose =True,force_save=force_save)
		i += 1
		

def check_filename_available(filename):
	t = open(filename_taken).read().split('\n')
	if filename in t: return False
	return True

def check_filename_done(filename):
	t = open(filename_done).read().split('\n')
	if filename in t: return True
	return False

def write_taken(filename):
	with open(filename_taken,'a') as fout:
		fout.write(filename+'\n')

def write_done(filename):
	with open(filename_done,'a') as fout:
		fout.write(filename+'\n')

