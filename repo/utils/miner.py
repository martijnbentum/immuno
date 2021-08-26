import pdfminer
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import copy
import json
import os

resource_manager = PDFResourceManager()
device = PDFPageAggregator(resource_manager,laparams=LAParams())
interpreter = PDFPageInterpreter(resource_manager,device)

json_dir = '../LAYOUTS/'

def open_file(filename):
	return open(filename,'rb')


def filename2pages(filename= '', fin = None):
	if not fin: fin = open_file(filename)
	return list( PDFPage.get_pages(fin) )


def page2layout(page):
	interpreter.process_page(page)
	return device.get_result()

class Pdf:
	def __init__(self,filename):
		self.filename = filename
		self.fin = open_file(filename)
		self.miner_pages =filename2pages(fin = self.fin)
		self._make_pages()

	def _make_pages(self):
		self.pages = []
		for i,page in enumerate(self.miner_pages):
			self.pages.append(Page(page,i+1,self.filename))
			

	@property
	def npages(self):
		return len(self.miner_pages)

	def close(self):
		self.fin.close()
		


class Page:
	def __init__(self, page=None, page_number = -1,filename='',
		json_filename = '', force_save = False):
		self.page_number = page_number
		self.filename = filename
		f = filename.split('/')[-1].strip('.pdf')
		self.identifier = f+ '_pagenumber_' + str(page_number)
		self.json_filename = json_dir + self.identifier
		self.json_file_present = os.path.isfile(self.json_filename)
		if self.json_file_present: self.load_json()
		elif page: self._make_layout(page)
		elif json_filename:
			self.json_filename = json_filename
			self.load_json()
		if not self.json_file_present or force_save:
			self.save_json()


	def _make_layout(self,page):
		l = page2layout(page)
		textbox = pdfminer.layout.LTTextBoxHorizontal
		self.objs = [Text_layout(x) for x in l._objs if type(x) == textbox]
		self.bbox = l.bbox
		self.height= l.height
		self.width= l.width
		self.x0= l.x0
		self.x1= l.x1
		self.y0= l.y0
		self.y1= l.y1


	def save_json(self):
		if self.page_number == -1 or not self.filename: 
			print('not saving file missing page number or filename:')
			print(self.page_number, self.filename)
			return
		self.json_file_present = True
		objs = [x.__dict__ for x in self.objs]
		d = copy.copy(self.__dict__)
		d['objs'] = objs
		with open(self.json_filename,'w') as fout:
			json.dump(d,fout)

	def load_json(self):
		d = json.load(open(self.json_filename))
		d['objs'] = [Text_layout(dict_object=x) for x in d['objs']]
		self.__dict__ = d
		

	def __repr__(self):
		b = [round(x,2) for x in self.bbox]
		return 'Page '+str(self.page_number) + ' ' + str(b)
		

class Text_layout:
	def __init__(self,obj = None, dict_object = None):
		if obj:
			self.text = obj.get_text()

			self.bbox = obj.bbox
			self.height= obj.height
			self.width= obj.width
			self.x0= obj.x0
			self.x1= obj.x1
			self.y0= obj.y0
			self.y1= obj.y1
		if dict_object:
			self.__dict__ = dict_object

	def __repr__(self):
		b = [round(x,2) for x in self.bbox]
		return 'Text layout: ' + str(b)+' '+self.text.replace('\n',' ')
	

'''
	def _get_layout(self):
		self.layout = page2layout(self.page)
		self.bbox = self.layout.bbox
		self.height= self.layout.height
		self.width= self.layout.width
		self.x0= self.layout.x0
		self.x1= self.layout.x1
		self.y0= self.layout.y0
		self.y1= self.layout.y1
		self.objects = self.layout._objs

	def purge_layout(self):
		if hasattr(self,'layout'):delattr(self,'layout')

	#def __iter__(self):
	#	return self.layout
'''

	

