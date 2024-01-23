import numpy as np
import mcstasHelper as mc
import re
import argparse

parser = argparse.ArgumentParser(description='Process MCStas data and extract ROI.')
parser.add_argument('filename', type=str, help='MCStas data filename')
parser.add_argument('--square', nargs=4, type=float, metavar=('x0', 'x1', 'y0', 'y1'),
					help='Square ROI limits: x0 x1 y0 y1')
parser.add_argument('--circle', nargs=3, type=float, metavar=('x0', 'y0', 'radius'),
					help='Circular ROI limits: x0 y0 radius')
parser.add_argument('--noshow', action='store_true', help='if true then dont display graph, only show count')

args = parser.parse_args()
inFile = args.filename

I, sigI, N, dataHeader, L = mc.extractMcStasData(inFile)

# Find extent from file header
extent = np.array(dataHeader['xylimits'].split(),dtype=float) 

# Calculate the spacing between values in the array
dx = (extent[1] - extent[0]) / (I.shape[1] - 1)
dy = (extent[3] - extent[2]) / (I.shape[0] - 1)

# Create the mask for the ROI
mask = np.zeros_like(I, dtype=bool)

roi_area = 0
if args.square:
	x0, x1, y0, y1 = args.square

	# Square ROI defined by 2 corners
	x_indices = np.where((x0 <= extent[0] + np.arange(I.shape[1]) * dx) & (extent[0] + np.arange(I.shape[1]) * dx < x1))
	y_indices = np.where((-y1 <= extent[2] + np.arange(I.shape[0]) * dy) & (extent[2] + np.arange(I.shape[0]) * dy < -y0))

	# Set the corresponding elements in the mask to True
	mask[y_indices[0][:, np.newaxis], x_indices[0]] = True
	
	roi_area = (x1-x0)*(y1-y0) 

if args.circle:
	x0, y0, radius = args.circle

	# Circle ROI defined by center (x0, y0) and radius
	x_indices, y_indices = np.meshgrid(np.arange(I.shape[1]), np.arange(I.shape[0]))
	mask = ((extent[0] + x_indices * dx - x0) ** 2 + (extent[2] + y_indices * dy - y0) ** 2 <= radius ** 2)
	
	roi_area = np.pi*radius**2

# Apply the mask and calculate the sum within the ROI
roi_sum = np.sum(I[mask])
sum_err = np.sqrt(np.sum(np.square(I[mask]))) 

# Determine units
unit1 = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
unit2 = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])

roi_info = f"Sum within ROI: {roi_sum:.2e} ± {sum_err:.2e}\n"
#roi_info += f"Area within ROI: {roi_area:.2e} [{unit1[0]}$\cdot${unit2[0]}]" 
if args.circle:
	#roi_info += f"ROI: ({x0}, {y0}) [cm], r = {radius} [cm]" 
	roi_info += f"ROI: ({x0}, {y0}), r = {radius}" 
print(roi_info)

if (args.noshow==0):
	import matplotlib.pyplot as plt
	from matplotlib.patches import Rectangle, Circle

	## Show ROI mask
	#plt.imshow(mask, cmap='binary', extent=extent)
	#plt.colorbar()
	#plt.title('ROI')
	#plt.show()
	## Show data with mask applied
	#plt.imshow(mask*I, cmap='plasma', extent=extent)
	#plt.colorbar()
	#plt.title('Counts within ROI')
	#plt.show()

	# Show data with mask outlined
	fig, ax = plt.subplots()
	
	#img = ax.imshow(np.flipud(I), extent=extent, cmap='plasma', norm='log')
	img = ax.imshow(np.flipud(I), extent=extent, cmap='plasma', norm='log', vmin=10, vmax=5e6)
	ax.set_title(f"{dataHeader['component']}; ({dataHeader['position']})m")
	ax.set_xlabel(dataHeader['xlabel'])
	ax.set_ylabel(dataHeader['ylabel'])
	cbar = fig.colorbar(img, ax=ax)
	cbar.set_label(dataHeader['zvar']+'/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
	#cbar.set_label('$n \cdot s^2$'+'/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
	
	# Add patch for ROI outline on plot
	if args.square:
		square = Rectangle((x0, y0), (x1 - x0), (y1 - y0), fill=False, color='red', linewidth=2)
		ax.add_patch(square)
		
	if args.circle:
		circle = Circle((x0, y0), radius, fill=False, color='red', linewidth=2)
		ax.add_patch(circle)

	ax.annotate(roi_info,
            xy=(0.05, 0.95),
            xycoords='axes fraction',
            ha='left',
            va='top',
            fontsize=10,
            color='black',
            bbox=dict(facecolor='white', edgecolor='black', pad=3.5))
            #bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', alpha=0.7, pad=0.5))
	
	plt.show()

