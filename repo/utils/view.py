import matplotlib
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle


def page2xlim_ylim(page, extra = 58):
	xlim = (0,page.width + extra)
	ylim = (0,page.height + extra)
	return xlim,ylim
	
def make_figure(xlim = (0,670),ylim=(0,850)):
	plt.ion()
	plt.figure()
	current_axis = plt.gca(xlim=xlim,ylim=ylim)
	plt.show()
	return current_axis

def page2figure(page, extra = 58):
	xlim,ylim = page2xlim_ylim(page, extra)
	return make_figure(xlim, ylim)

def add_rectangle(figure, x, color = 'b', alpha= 1.0,fill = None):
	figure.add_patch(Rectangle((x.x0,x.y0),x.width,x.height, color=color, 
		fill=fill, alpha= alpha))

def show_page(page, exclude_after_reference=False, exclude_all=False):
	figure = page2figure(page)
	add_rectangle(figure,page)
	_ = page.get_usable_objs(exclude_after_reference=exclude_after_reference,
		exclude_all = exclude_all)
	for x in page.objs:
		ref = x.reference
		add_rectangle(figure,x,color=x.color, alpha=x.alpha)
		xcenter,ycenter = x.center
		if x.index: overlap = x.get_perc_overlap()
		else: overlap = ''
		plt.text(xcenter,ycenter,x.index + '   ' + str(overlap), alpha=0.5,
			color = x.color)
		if ref: plt.text(x.left,x.bottom,'reference',color = x.color)

def show_text_objects(objs, colors = None):
	figure = make_figure()
	for i,x in enumerate(objs):
		if not colors:color = 'b'
		elif type(colors) == str: color = colors
		elif i >= len(colors): color = 'b'
		else:color = colors[i]
		add_rectangle(figure,x,color=color, alpha = 1)
	


	

	
	
	
