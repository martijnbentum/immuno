from django.db import models

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
		m = []
		if self.ocr: m.append( 'ocr:'.ljust(12) + str(self.ocr.nwords))
		if self.pdftotext: 
			m.append( 'pdftotext:'.ljust(12) + str(self.pdftotext.nwords))
		if self.pdfminer: 
			m.append( 'pdfminer:'.ljust(12) + str(self.pdfminer.nwords))
		return '\n'.join(m)

	@property
	def name(self):
		return self.filename.split('/')[-1][:10] + '...'
	
	



	
