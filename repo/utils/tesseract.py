import glob
ocr_dir = '../OCR_TEXT/'

class Pdf:
	def __init__(self,filename):
		self.filename = filename.split('/')[-1].strip('.pdf')
		self.make_pages()

	def make_pages(self):
		fn= glob.glob(ocr_dir + self.filename + '*')
		self.page_filenames = sort_filenames_on_pagenumber(fn) 
		self.pages = [Page(f) for f in self.page_filenames]

	def __repr__(self):
		return self.filename
		

class Page:
	def __init__(self,filename):
		self.filename = filename
		self.data = open(filename).read()
		self.pagenumber = filename2pagenumber(self.filename)
		self.table = [line.split('\t') for line in self.data.split('\n')[1:]]
		self.header = self.data.split('\n')[0].split('\t')
		self.make_blocks()

	def __repr__(self):
		return self.filename

	def make_blocks(self):
		self.blocks = []
		block_number = 0
		rows= []
		for row in self.table:
			if not row or len(row) != 12: continue
			if block_number == row[2]:rows.append(row)
			if block_number != row[2]:
				block = Block(rows)
				if block.ok:
					self.blocks.append(Block(rows))
				rows= []
				block_number = row[2]
	

class Block:
	def __init__(self,rows):
		self.rows= rows 
		if rows:
			self.block_number = rows[0][2]
			self.nrows= len(rows)
			self.make_lines()
			self.ok = True if len(self.lines) > 0 else False
		else: self.ok = False

	def __repr__(self):
		return str(self.block_number) + ' ' + str(self.nrows)


	def make_lines(self):
		self.lines = []
		line_number = 0
		rows= []
		for row in self.rows:
			if line_number == row[4]: rows.append(row)
			if line_number != row[4]:
				line = Line(rows)
				if line.ok:
					self.lines.append(line)
				rows= []
				line_number = row[2]


class Line:
	def __init__(self, rows):
		self.rows=rows 
		if rows:
			self.line_number = rows[0][4]
			self.make_words()
			self.ok = True if len(self.words) > 0 else False
		else:self.ok = False

	def __repr__(self):
		return str(self.line_number) + ' nwords: ' + str(len(self.words))

	def make_words(self):
		self.words = []
		for row in self.rows:
			word = Word(row)
			if word.word: self.words.append(word)

			
		

class Word:
	def __init__(self,row):
		self.row=row 
		self.word_number = row[5]
		self.left = row[6]
		self.top = row[7]
		self.width= row[8]
		self.height= row[9]
		self.confidence= row[10]
		self.word= row[11]

	def __repr__(self):
		return str(self.word_number) + ' ' + self.word



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
