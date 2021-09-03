import matplotlib
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle


def page2xlim_ylim(page, extra = 100):
	xlim = (0,page.page_width + extra)
	ylim = (0,page.page_height + extra)
	return xlim,ylim
	
def make_figure(xlim = (0,4250),ylim=(0,5500)):
	plt.ion()
	plt.figure()
	current_axis = plt.gca(xlim=xlim,ylim=ylim)
	plt.show()
	return current_axis

def page2figure(page, extra = 100):
	xlim,ylim = page2xlim_ylim(page, extra)
	return make_figure(xlim, ylim)

def add_rectangle(figure, x, color = 'b', alpha= 1.0,fill = None):
	figure.add_patch(Rectangle((x.x0,x.y0),x.width,x.height, color=color, 
		fill=fill, alpha= alpha))

def show_page(page, exclude_after_reference=False, exclude_all=False):
	figure = page2figure(page)
	add_rectangle(figure,page.rectangle, color = page.color)
	# _ = page.get_usable_objs(exclude_after_reference=exclude_after_reference,
	# exclude_all = exclude_all)
	for block in page.blocks:
		muted = False
		war =  block.words_area_ratio
		pa = block.perc_area
		whd = block.word_hdistance
		# if not pa or pa < 2 or war > 0.09 or not whd or whd > 100:
		if not block.usable:
			muted = True
			block.color = 'y'
			block.alpha = 0.1
		show_block(block,figure, muted = muted)
		# ref = x.reference
		x = block
		xcenter,ycenter = x.rectangle.center
		left = x.rectangle.left
		# if x.index: overlap = x.get_perc_overlap()
		# else: overlap = ''
		t = str(x.perc_area) 
		if x.word_hdistance:t+= ' | ' + str(x.word_hdistance)
		if war: t+= ' | ' + str(war)
		t += ' | w:' + str(x.rectangle.width)
		plt.text(left +10,ycenter,x.block_number+ '   ' + t, alpha=0.8,
			color = x.color)
		# if ref: plt.text(x.left,x.bottom,'reference',color = x.color)

def show_block(block,figure, muted =False):
	add_rectangle(figure,block.rectangle,color=block.color, alpha=block.alpha)
	for line in block.lines:
		show_line(line,figure, muted)

def show_line(line,figure, muted = False):
	if muted:
		line.color = 'y'
		line.alpha = 0.1
	add_rectangle(figure,line.rectangle,color=line.color, alpha=line.alpha)
	for word in line.words:
		show_word(word,figure, muted)

def show_word(word,figure, muted = False):
	if muted:
		word.color = 'y'
		word.alpha = 0.1
	add_rectangle(figure,word.rectangle,color=word.color, alpha=word.alpha)

def show_text_objects(objs, colors = None):
	figure = make_figure()
	for i,x in enumerate(objs):
		if not colors:color = 'b'
		elif type(colors) == str: color = colors
		elif i >= len(colors): color = 'b'
		else:color = colors[i]
		add_rectangle(figure,x,color=color, alpha = 1)
	
