import pdfminer
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import copy
import json
import os
import re
from utils import clean_article
from utils import view
from utils.clean_article import RED, END



json_dir = '../LAYOUTS/'

def open_file(filename):
	return open(filename,'rb')


def filename2pages(filename= '', fin = None):
	if not fin: fin = open_file(filename)
	return list( PDFPage.get_pages(fin) )


def page2layout(page):
	resource_manager = PDFResourceManager()
	device = PDFPageAggregator(resource_manager,laparams=LAParams())
	interpreter = PDFPageInterpreter(resource_manager,device)
	interpreter.process_page(page)
	return device.get_result()


class Pdf:
	def __init__(self,filename):
		self.filename = filename
		self.fin = open_file(filename)
		self.miner_pages =filename2pages(fin = self.fin)
		self._make_pages()

	def __repr__(self):
		extra = '...' if len(self.filename) > 33 else ''
		return self.filename[:33]+extra + ' ' + str(self.npages)

	def _make_pages(self):
		self.pages = []
		for i,page in enumerate(self.miner_pages):
			self.pages.append(Page(page,i+1,self.filename))

	@property
	def npages(self):
		return len(self.miner_pages)

	def close(self):
		self.fin.close()

	@property
	def reference_pagenumber(self, verbose = False):
		if hasattr(self,'_reference_pagenumber'): 
			return self._reference_pagenumber
		numbers = []
		for page in self.pages:
			if page.reference:numbers.append(page.page_number)
		if len(numbers) == 0:
			if verbose:print('did not find reference pages')
			return None
		elif len(numbers) ==1: return numbers[0]
		else: 
			if verbose:print('found multiple numbers:',numbers,'returning last')
			return numbers[-1]

	def get_usable_objects(self):
		o = []
		for page in self.pages:
			rp = self.reference_pagenumber
			if rp and page.page_number > rp: break
			if rp and page.page_number == rp:
				o.extend(page.get_usable_objs(exclude_after_reference=True))
			else:o.extend(page.get_usable_objs())
		return o

	def text(self, add_pagenumber = False, add_object_index = False,
		add_missing_text = False):
		t = ''
		for page in self.pages:
			rp = self.reference_pagenumber
			if rp and page.page_number > rp: break
			if rp and page.page_number == rp:
				t += page.text(
					exclude_after_reference=True,
					add_pagenumber= add_pagenumber, 
					add_object_index =add_object_index,
					add_missing_text = add_missing_text)
			else:
				t += page.text(
					add_pagenumber = add_pagenumber,
					add_object_index = add_object_index,
					add_missing_text = add_missing_text)
	
		return t 

	def get_perc_usable_objects(self, threshold = 10):
		o = self.get_usable_objects()
		ok = []
		for x in o:
			if x.get_perc_overlap() < threshold:ok.append(ok)
		return round(len(ok) / len(o)*100,2)
			
			
		


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
		self.set_contains_objs()
		self.set_overlap_objs()

	def __repr__(self):
		b = [round(x,2) for x in self.bbox]
		return 'Page '+str(self.page_number) + ' ' + str(b)

	def _make_layout(self,page):
		l = page2layout(page)
		textbox = pdfminer.layout.LTTextBoxHorizontal
		p ={'page_number': self.page_number}
		self.objs = [Text_layout(x,**p) for x in l._objs if type(x) == textbox]
		self.bbox = l.bbox
		self.height= l.height
		self.width= l.width
		self.x0= l.x0
		self.x1= l.x1
		self.y0= l.y0
		self.y1= l.y1
		self.nobjs = len(self.objs)

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
		p ={'page_number': self.page_number}
		d['objs'] = [Text_layout(dict_object=x,**p) for x in d['objs']]
		self.__dict__ = d

	def text_areas(self):
		o = []
		for x in self.objs:
			o.append([round(x.area/self.area*100,2),x])
		return o

	def sort_texts_on_area(self):
		o = self.text_areas()
		o.sort(key=lambda x:x[0])
		return o

	@property
	def area(self):
		return self.height * self.width

	def check_for_size(self, threshold = 1.5, exclude_after_reference=False,
		exclude_all = False):
		objs = self.text_areas()
		ref =self.reference_object
		if ref and exclude_after_reference:
			ref_index = self.objs.index(ref)
		i = 0
		for perc, obj in objs:
			if perc < threshold:
				obj.set_alpha(0.1)
			else:obj.size_usable = True
			if (exclude_after_reference and ref and i>ref_index) or exclude_all:
				obj.set_alpha(0.2)
				obj.set_color('y')
				obj.size_usable = False
			i += 1

	def get_usable_objs(self, exclude_after_reference = False,exclude_all=False):
		self.check_for_size(exclude_after_reference =exclude_after_reference,
			exclude_all= exclude_all)
		i = 0
		o = []
		if exclude_all: return o
		ref =self.reference_object
		for x in self.objs:
			if exclude_after_reference and ref == x:break
			if x.size_usable: 
				x.index = str(i)
				i+=1
				o.append(x)
		return o

	def text(self, exclude_after_reference = False, exclude_all = False,
		add_pagenumber = False, add_object_index = False, 
		add_missing_text= False):
		o = self.get_usable_objs(exclude_after_reference,exclude_all)
		extra='- page - '+str(self.page_number)+'\n' if add_pagenumber else ''
		t = extra
		for i,x in enumerate(o):
			if add_object_index: t += '- obj index - ' + str(i) + '\n'
			t+= x.text
			if add_missing_text: 
				missing_text = x.get_text_from_contained_objs()
				if missing_text: 
					t += '\n-missing text:\n'+ RED + missing_text + END 
			if i != len(o) -1: t+='\n'
		return t

	def check_for_overlap(self):
		for i in self.objs:
			for j in self.objs:
				if i.color == 'r':continue
				if i.contained_by(j): i.set_color('r')
				elif i.overlap_strict(j):i.set_color('g')

	@property
	def nwords(self):
		if not hasattr(self,'_nwords'):
			self._nwords = 0
			for x in self.objs:
				self._nwords += x.nwords
		return self._nwords

	@property
	def center(self):
		return rectangle2center(self)

	@property
	def reference(self):
		for x in self.objs:
			if x.reference: return True
		return False

	@property
	def reference_object(self):
		for x in self.objs:
			if x.reference: return x
		return None

	def set_contains_objs(self):
		for x in self.objs:
			x.get_contained_objs(self.objs)

	def set_overlap_objs(self):
		for x in self.objs:
			x.get_overlap_objs(self.objs)
						

	
class Text_layout:
	def __init__(self,obj = None, dict_object = None, page_number = None):
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
		self.page_number = page_number
		self.left= self.x0
		self.right= self.x1
		self.bottom= self.y0
		self.top= self.y1
		self.set_color()
		self.set_alpha()
		self.size_usable = None
		self.digit_usable = None
		self.eol_usable = None
		self.index=''

	def __repr__(self):
		b = [round(x,2) for x in self.bbox]
		return 'Text layout: ' + str(b)+' '+self.text.replace('\n',' ')


	
	@property
	def area(self):
		return self.height * self.width

	@property
	def nwords(self):
		return len([w for w in self.text.replace('\n',' ').split(' ')])
	
	@property
	def ratio_eol(self):
		return self.text.count('\n') / len(self.text)

	@property
	def ratio_digits(self):
		return len(re.findall('[0-9]',self.text)) / len(self.text)

	def set_color(self,color= 'b'):
		self.color = color

	def set_alpha(self,alpha=1.0):
		self.alpha = alpha

	def vertical_overlap(self,other):
		if self == other: return False
		if self.top > other.bottom and self.top < other.top: return True
		if self.bottom > other.bottom and self.bottom < other.top: return True
		if self.top >= other.top and self.bottom <= other.bottom: return True
		return False

	def horizontal_overlap(self,other):
		if self == other: return False
		if self.right > other.left and self.right < other.right: return True
		if self.left > other.left and self.left < other.right: return True
		if self.left <= other.left and self.right >= other.right: return True
		return False

	def overlap(self,other):
		return self.vertical_overlap(other) or self.horizontal_overlap(other)

	def overlap_strict(self,other):
		return self.vertical_overlap(other) and self.horizontal_overlap(other)

	def contained_by(self,other):
		if not self.overlap_strict(other): return False
		if self.left >= other.left and self.right <= other.right:
			if self.bottom >= other.bottom and self.top <= other.top: return True
		return False

	def contains(self,other):
		return other.contained_by(self)
		
	@property
	def center(self):
		return rectangle2center(self)
	
	@property
	def reference(self):
		ref = clean_article.ref
		for s in ref:
			if s in self.text.lower(): 
				self.alpha=.6
				self.color = 'm'
				return True
		return False
		
	def get_contained_objs(self, others = None):
		if hasattr(self,'_contained_objs'):return self._contained_objs
		if not others:
			print('please provide the other texlayout objects of the page')
			return None
		self._contained_objs = []
		for x in others:
			if self.contains(x): self._contained_objs.append(x)

	def get_overlap_objs(self,others = None):
		if hasattr(self,'_overlap_objs'):return self._overlap_objs
		if not others:
			print('please provide the other texlayout objects of the page')
			return None
		self._overlap_objs = []
		for x in others:
			if self.overlap_strict(x): self._overlap_objs.append(x)

	def get_perc_overlap(self, others = None):
		if not hasattr(self,'_overlap_objs') and not others:
			print('please provide others to compute perc overlap')
			return None
		else: self.get_overlap_objs(others)
		overlap_area = 0
		for other in self.get_overlap_objs():
			overlap_area += compute_overlap_area(self,other)
		return round(overlap_area / self.area*100,2)


	def get_text_from_contained_objs(self, include_object_index = False,
		others = None):
		o = self.get_contained_objs(others)
		t = ''
		for i,x in enumerate(o):
			if include_object_index: t+='- contained object index - '+str(i)+'\n'
			t+= x.text
			if i < len(o)-1:t+='\n'
		return t
			

		
		
			

		
		
			

def rectangle2center(r):
	x = (r.x0 + r.x1) / 2
	y = (r.y0 + r.y1) / 2
	return x,y

def compute_overlap_area(r1,r2, show=False):
	if r2.contained_by(r1): return r2.area
	if r2.left > r1.left and r2.right < r1.right:
		left,right = r2.left, r2.right
	elif r2.left < r1.right and r2.left > r1.left:
		left,right = r2.left, r1.right
	elif r2.left < r1.left and r2.right < r1.right:
		left, right = r1.left,r2.right
	else: left,right = r1.left, r1.right

	if r2.bottom > r1.bottom and r2.top < r1.top:
		bottom,top = r2.bottom, r2.top
	elif r2.bottom < r1.top and r2.bottom > r1.bottom:
		bottom,top= r2.bottom, r1.top
	elif r2.bottom< r1.bottom and r2.top< r1.top:
		bottom, top= r1.bottom,r2.top
	else: bottom,top= r1.bottom, r1.top

	height = top -bottom
	width = right - left
	area = height * width
	r3 = copy.copy(r2)
	r3.left,r3.right,r3.bottom,r3.top = left,right,bottom,top
	r3.x0,r3.x1,r3.y0,r3.y1= left,right,bottom,top
	r3.bbox = left,bottom,right,top
	r3.width = width
	r3.height= height
	if show:
		view.show_text_objects([r1,r2,r3],['b','r','g'])
	assert r3.contained_by(r1)
	return area
	
	

