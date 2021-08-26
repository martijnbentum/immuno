from django.db import models
import glob
import numpy as np
import os
from utils import miner
import re


class ExtractionType(models.Model):
	name = models.CharField(max_length=100,default = '', unique =True)

	def __repr__(self):
		return self.name


class Text(models.Model):
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	filename = models.CharField(max_length=1000,default='')
	extraction_type = models.ForeignKey(ExtractionType, **dargs, 
		related_name = 'extraction_type')
	text = models.TextField(default='')
	error = models.BooleanField(default=False)

	def __repr__(self):
		return 'Text: ' + self.name + ' ' + str(self.error)

	@property
	def nwords(self):
		return len(self.text.replace('\n',' ').split(' '))

	@property
	def name(self):
		return self.filename.split('/')[-1][:10] + '...\t' + self.text[:20] + '...'


class Article(models.Model):
	dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
	filename = models.CharField(max_length=1000,default='', unique = True)
	ocr = models.ForeignKey(Text, **dargs, related_name = 'ocr')
	pdftotext = models.ForeignKey(Text, **dargs, related_name = 'pdftotext')
	pdfminer = models.ForeignKey(Text, **dargs, related_name = 'pdfminer')
	info = models.TextField(default='')
	error = models.BooleanField(default=False)
	npages = models.IntegerField(default=0)
	
	def __repr__(self):
		return 'Article: ' +self.name
	
	def __str__(self):
		return self.filename.split('/')[-1]

	@property
	def nwords(self):
		m = {}
		if self.ocr: m['ocr'] =self.ocr.nwords
		if self.pdftotext: m['pdftotext'] =self.pdftotext.nwords
		if self.pdfminer: m['pdfminer']= self.pdfminer.nwords
		return m

	@property
	def nwords_print(self):
		d = self.nwords
		m = []
		for key, value in d.items():
			m.append(key.ljust(12) + str(value))
		print('\n'.join(m))

	def nwords_difference(self, threshold = 1.5):
		values = list(self.nwords.values())
		median = np.median(values)
		for v in values:
			if v*threshold < median or v/threshold > median: return True
		return False

	@property
	def name(self):
		return self.filename.split('/')[-1][:33] + '...'
	
	def open(self):
		f = self.filename.split('/')[-1].replace(' ','\ ')
		os.system('open ../pdf/' + f)

	@property
	def layout(self):
		if not hasattr(self,'_layout'):
			f = self.filename.split('/')[-1].strip('.pdf')
			if [ff for ff in glob.glob('../LAYOUTS/*') if f in ff]:
				self._layout= miner.Pdf(self.filename)
			else: self._layout = False
		return self._layout

	@property
	def year(self):
		year = re.findall('(?<![0-9])[0-9]{4,4}(?![0-9])',self.filename)
		if len(year) != 1: print('found unexpected number 4 digit strings:',year)
		if len(year) ==1:return int(year[0])
		else: return 0


	

		
	



	
