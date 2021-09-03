import glob
ocr_dir = '../OCR_TEXT/'
from utils.clean_article import BLUE,RED,GREEN,END, ref
from utils import view_ocr
import numpy as np



class Pdf:
	def __init__(self,filename):
		self.filename = filename.split('/')[-1].strip('.pdf')
		self.make_pages()
		self.get_blocks()

	def make_pages(self):
		fn= glob.glob(ocr_dir + self.filename + '*')
		self.page_filenames = sort_filenames_on_pagenumber(fn) 
		self.pages = [Page(f,self) for f in self.page_filenames]

	def get_blocks(self):
		self.blocks = []
		for page in self.pages:
			self.blocks.extend(page.blocks)
			

	def __repr__(self):
		return self.filename

	def text(self, with_numbering = False, usable = True, check_width = True,
		return_non_usable_text =False, only_page_numbers =False):
		if usable: self.set_usable(check_width)
		if with_numbering: 
			m = BLUE + self.filename+'\n' +'-'*len(self.filename)+END+'\n'
		else: m= ''
		for page in self.pages:
			m += page.text(with_numbering, usable, return_non_usable_text,
				only_page_numbers)
		return m


	def show(self, usable = True, check_width = False, page =None):
		if usable: self.set_usable(check_width)
		if type(page) == int and page < len(self.pages): self.pages[page].show()
		else:
			for p in self.pages:
				p.show()
			
	@property
	def page_height(self):
		ph = [p.page_height for p in self.pages]
		if len(list(set(ph))) > 1: 
			print('pages of different dimensions:',ph, 'returning first')
		return ph[0]

	@property
	def page_width(self):
		pw = [p.page_width for p in self.pages]
		if len(list(set(pw))) > 1: 
			print('pages of different dimensions:',pw, 'returning first')
		return pw[0]

	@property
	def reference_pagenumber(self,verbose = False):
		numbers = []
		for page in self.pages:
			if page.reference: numbers.append(page.pagenumber)
		if len(numbers) == 0:
			if verbose:print('did not find reference pages')
			return None
		elif len(numbers) ==1: return numbers[0]
		else: 
			if verbose:print('found multiple numbers:',numbers,'returning last')
			return numbers[-1]

	def set_usable(self, check_width = False):
		reference_page = None
		pn = self.reference_pagenumber
		if pn:
			ref_page_index = self.reference_pagenumber -1
		for i,page in enumerate(self.pages):
			if pn and i == ref_page_index: 
				page.set_usable_blocks(check_reference= True)
			elif pn and i > ref_page_index:
				page.usable=False
				page.set_usable_blocks(set_all_false=True)
			else:
				page.set_usable_blocks()
		if check_width:
			blocks = self.get_usable_blocks(set_usable=False)
			x = [b.rectangle.width/b.page_width*100 for b in blocks]
			median_perc_width = np.median(x)
			for block in blocks:
				if block.page.pagenumber ==1: more =20
				else: more = 1
				perc_width = block.rectangle.width/block.page_width*100
				if perc_width > median_perc_width + more: block.usable = False
				if perc_width < median_perc_width - 1: block.usable = False
		for block in self.blocks:
			t = block.text().lower()
			if 'acknowledgements' in t:
				print(block.page,block, 'acknowledgements')
				block.usable = False
			if 'author contributions' in t:
				block.usable = False
				print(block.page,block, 'author contributions')
			if 'disclosures' in t:
				block.usable = False
				print(block.page,block, 'disclosures')
			if 'corresponding author' in t:
				block.usable = False
				print(block.page,block, 'corresponding author')
			

	def get_usable_blocks(self, check_width = False, set_usable = True):
		blocks = []
		if set_usable:self.set_usable()
		for page in self.pages:
			for block in page.blocks:
				if block.usable:blocks.append(block)
		return blocks


			
	


class Page:
	def __init__(self,filename,pdf = None):
		self.filename = filename
		self.pdf = pdf
		self.data = open(filename).read()
		self.pagenumber = filename2pagenumber(self.filename)
		self.table = [l.split('\t') for l in self.data.split('\n')[1:] if l]
		self.header = self.data.split('\n')[0].split('\t')
		row2rectangle_values(self,self.table[0])
		self.rectangle=obj2rectangle(self)
		self.make_blocks()
		self.color = 'r'
		self.usable = True

	def __repr__(self):
		return self.filename

	def make_blocks(self):
		self.blocks ,self.excluded_blocks, self.excluded_rows = [],[], []
		block_number = '0'
		rows= []
		for i,row in enumerate(self.table):
			if block_number == row[2]:rows.append(row)
			if block_number != row[2] or i == len(self.table)-1:
				block = Block(rows,self)
				if block.ok:
					self.blocks.append(block)
				else:
					self.excluded_blocks.append(block)
					self.excluded_rows.extend(rows)
				rows= []
				block_number = row[2]

	def text(self, with_numbering = False, usable = True, 
		return_non_usable_text = False, only_page_numbers = False):
		if usable and not return_non_usable_text and not self.usable: return ''
		if with_numbering or only_page_numbers: 
			m = RED + '\n --- Page ' + str(self.pagenumber) + ' ---\n' +END
		else: m = ''
		for block in self.blocks:
			m += block.text(with_numbering = with_numbering, usable = usable,
				return_non_usable_text = return_non_usable_text)
		return m


	@property
	def page_height(self):
		return self.rectangle.height

	@property
	def page_width(self):
		return self.rectangle.width

	@property
	def page_area(self):
		return self.rectangle.area

	@property
	def area(self):
		return self.rectangle.area
	
	def show(self):
		view_ocr.show_page(self)

	@property
	def reference(self):
		for i,block in enumerate(self.blocks):
			if block.reference: 
				self._reference_block_index = i
				return True
		return False

	@property
	def reference_index(self):
		if self.reference:
			return self._reference_block_index
		return None

	def set_usable_blocks(self, set_all_false = False, check_reference = False):
		for b in self.blocks:
			b.set_usable()
		if not check_reference: return
		i =  self.reference_index
		if set_all_false: start =0
		else:
			if not i: return 
			if i < len(self.blocks) -1: start = i
			else: return
		for block in self.blocks[start:]:
			block.usable = False
	

class Block:
	def __init__(self,rows,page = None):
		self.rows= rows 
		self.page = page
		self.nrows= len(rows)
		self.nlines = 0
		self.block_number = 'unk'
		self.ok = False
		if rows:
			self.block_number = rows[0][2]
			self.make_lines()
			# self.ok = True if len(self.lines) > 0 else False
			self.ok = True
			lr = [l.rectangle for l in self.lines if l.area]
			self.rectangle= rectangles2bbox_rectangle(lr,obj = self)
		self.color = 'm'
		self.alpha = 1.0
		self.usable = True

	def __repr__(self):
		return BLUE +str(self.block_number) + END +' nlines:' + str(self.nlines)

	def set_usable(self):
		war =  self.words_area_ratio
		pa = self.perc_area
		whd = self.word_hdistance
		if not pa or pa < 2 or war > 0.1 or war < 0.04 or not whd or whd > 100:
			self.usable = False
		

	def make_lines(self):
		self.lines = []
		line_number = '0'
		rows= []
		for i,row in enumerate(self.rows):
			if line_number == row[4]: rows.append(row)
			if line_number != row[4] or i == len(self.rows)-1:
				line = Line(rows,self)
				if line.ok:
					self.lines.append(line)
				rows= []
				line_number = row[4]
		self.nlines = len(self.lines)

	def text(self,with_numbering = False, usable = False,
		return_non_usable_text = False):
		if usable and not return_non_usable_text and not self.usable: return ''
		if usable and return_non_usable_text and self.usable: return ''
		if with_numbering:
			m = GREEN +'\n --- Block ' + str(self.block_number) + ' ---\n'+END
		else: m = ''
		for line in self.lines:
			m += line.text(with_numbering = with_numbering)
		return m

	@property
	def page_height(self):
		return self.page.page_height

	@property
	def page_width(self):
		return self.page.page_width

	@property
	def page_area(self):
		return self.page.page_area

	@property
	def word_hdistance(self):
		whd = [l.word_hdistance for l in self.lines if l.word_hdistance]
		if not whd: return None
		return np.median(whd)

	@property
	def area(self):
		area = self.rectangle.area
		if area == self.page_area: return None
		return area

	@property
	def perc_area(self):
		if not self.area: return None
		return round(self.area / self.page_area *100, 2)

	@property
	def words_area_ratio(self):
		if not self.area: return None
		t = self.text()
		if not t: return None
		nwords = len(t.replace('\n',' ').split(' '))
		return round(self.area / nwords / self.page_area *100,2)

	@property
	def reference(self):
		for line in self.lines:
			if line.reference: return True
		return False
	

class Line:
	def __init__(self, rows, block= None):
		self.rows=rows 
		self.block = block
		self.words = []
		self.ok = False
		self.line_number = 'unk'
		self.nwords = len(self.words)
		if rows:
			self.line_number = rows[0][4]
			self.make_words()
			# self.rectangle = obj2rectangle(self)
			self.ok = True
			wr = [w.rectangle for w in self.words if w.area]
			self.rectangle= rectangles2bbox_rectangle(wr,obj = self)
		self.color = 'g'
		self.alpha = 0.4

	def __repr__(self):
		return str(self.line_number) + ' nwords: ' + str(len(self.words))

	def make_words(self):
		self.words = []
		for row in self.rows:
			word = Word(row,self)
			if word.word: self.words.append(word)

	def text(self,with_numbering = False):
		if with_numbering:
			m = BLUE+ str(self.line_number) +END + ' '
		else: m = ''
		m += ' '.join([w.word for w in self.words]) + '\n'
		return m
			
	@property
	def page_height(self):
		return self.block.page_height

	@property
	def page_width(self):
		return self.block.page_width

	@property
	def page_area(self):
		return self.block.page_area
	
	@property
	def area(self):
		area = self.rectangle.area
		if area == self.page_area: return None
		return area

	@property
	def word_hdistance(self):
		whd = [w.word_hdistance for w in self.words if w.word_hdistance]
		if not whd: return None
		return np.median(whd)

	@property
	def reference(self):
		for word in self.words:
			if word.reference: return True
		return False
		

class Word:
	def __init__(self,row, line = None):
		self.row=row 
		self.line = line
		self.word_number = int(row[5])
		self.index = self.word_number -1
		row2rectangle_values(self,row)
		self.confidence= row[10]
		self.word= row[11]
		self.rectangle = obj2rectangle(self)
		self.color = 'b'
		self.alpha = 0.15

	def __repr__(self):
		return str(self.word_number) + ' ' + self.word

	@property
	def page_height(self):
		return self.line.page_height

	@property
	def page_width(self):
		return self.line.page_width

	@property
	def page_area(self):
		return self.line.page_area
	
	@property
	def area(self):
		area = self.rectangle.area
		if area == self.page_area: return None
		return area

	@property
	def prev_word(self):
		if self.index == 0: return None
		return self.line.words[self.index -1]


	@property
	def next_word(self):
		if self.index == len(self.line.words) -1: return None
		return self.line.words[self.index +1]

	@property
	def prev_word_hdistance(self):
		prev_word = self.prev_word
		if prev_word == None: return None
		return self.rectangle.left - prev_word.rectangle.right

	@property
	def next_word_hdistance(self):
		next_word = self.next_word
		if next_word == None: return None
		return next_word.rectangle.left - self.rectangle.right

	@property
	def word_hdistance(self):
		phd =self.prev_word_hdistance
		nhd = self.next_word_hdistance
		if phd and nhd: return (phd + nhd) / 2
		if phd: return phd
		if nhd: return nhd
		return None

	@property
	def reference(self):
		for r in ref:
			if r in self.word.lower(): return True


class Rectangle:
	def __init__(self,x,y,height,width,xy_corner = 'top_left', obj = None):
		self.x = float(x)
		self.y = float(y)
		self.height = float(height)
		self.width = float(width)
		self.xy_corner = xy_corner
		self.ycorner, self.xcorner = self.xy_corner.split('_')
		self.obj = obj
		self._set_values()

	def __repr__(self):
		return ' '.join(map(str,self.bbox))

	def _set_values(self):
		if self.xcorner == 'left':
			self.x0 = self.x 
			self.x1 = self.x + self.width
		elif self.xcorner == 'right':
			self.x0 = self.x - self.width
			self.x1 = self.x
		else: raise ValueError(xcorner, 'should be left or right')
		if self.ycorner == 'top': 
			self.y0 = self.y - self.height
			self.y1 = self.y
		elif self.ycorner== 'bottom':
			self.y0 = self.y
			self.y1 = self.y + self.height
		else: raise ValueError(ycorner, 'should be top or bottom')
		self.left,self.right = self.x0,self.x1
		self.bottom,self.top = self.y0,self.y1
		self.bbox = [self.x0,self.y0,self.x1,self.y1]

	def get_corner(self,xy_corner):
		ycorner, xcorner = xy_corner.split('_')
		if xcorner == 'left': x = self.x0
		elif xcorner == 'right': x = self.x1
		else: raise ValueError(xcorner, 'should be left or right')
		if ycorner == 'bottom': y = self.y0
		elif ycorner == 'top':y =self.y1
		else: raise ValueError(ycorner, 'should be top or bottom')
		return x,y

	def convert_to_different_xy_corner(self, xy_corner):
		x, y = get_corner(xy_corner)
		return Rectangle(x,y,self.height,self.width,xy_corner)

	@property
	def page_height(self):
		return self.obj.page_height

	@property
	def center(self):
		x = (self.x0 + self.x1) / 2
		y = (self.y0 + self.y1) / 2
		return x,y

	@property
	def area(self):
		return self.height * self.width

	

def obj2rectangle(obj):
	return ocr2rectangle(obj.left,obj.top,obj.height,obj.width, obj = obj)


def ocr2rectangle(left,top,height,width,xy_corner = 'top_left', obj = None):
	return Rectangle(x = left,y = top, height = height, width = width,
		xy_corner = xy_corner, obj=obj)

		
def rectangles2bbox_rectangle(rectangles, obj = None):
	'''returns the smallest bounding box of a list of rectangles.'''
	if obj == None:height, width = 5500,4250
	else: height, width = obj.page_height, obj.page_width
	x0,x1,y0,y1 = width,0,height,0
	for r in rectangles:
		if r.x0 < x0: x0= r.x0
		if r.x1 > x1: x1= r.x1
		if r.y0 < y0: y0= r.y0
		if r.y1 > y1: y1= r.y1
	width = x1 - x0
	height = y1-y0
	return Rectangle(x0,y1,height,width, obj =obj)


def invert_y(y,page_height = 5500):
	return page_height - y
	
	
def row2rectangle_values(obj,row):
	obj.left = float(row[6])
	obj.top = invert_y(float(row[7]))
	obj.width= float(row[8])
	obj.height= float(row[9])
	obj.right = obj.left + obj.width
	obj.bottom = obj.top - obj.height

	

def filename2pagenumber(filename):
	try:return int(filename.split('_')[-1])
	except: 
		print('could not convert filename to page number, unexpected format:')
		print(filename)
		

def sort_filenames_on_pagenumber(fn):
	fn = [[f,filename2pagenumber(f)] for f in fn]
	fn.sort(key=lambda x: x[1])
	fn = [f[0] for f in fn]
	return fn

