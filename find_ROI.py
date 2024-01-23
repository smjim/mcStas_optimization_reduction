import numpy as np
import mcstasHelper as mc
import re
import argparse

parser = argparse.ArgumentParser(description='Process MCStas data and determine ROI.')
parser.add_argument('filename', type=str, help='MCStas data filename')
parser.add_argument('--center', nargs=2, type=float, metavar=('x0, y0'),
					help='Center of ROI')
parser.add_argument('--rect', nargs=4, type=float, metavar=('w0', 'w1', 'h0', 'h1'),
                    help='Create ROI in rectangular shape: initial width, final width, initial height, final height')
parser.add_argument('--circle', nargs=2, type=float, metavar=('r0', 'r1'),
                    help='Create ROI in circular shape: initial radius, final radius') 
parser.add_argument('--threshold', nargs=1, type=float, metavar=('threshold'),
					help='Threshold for ROI definition')
parser.add_argument('--n', nargs=1, type=float, metavar=('n'),
					help='Number of iterations to test')
parser.add_argument('--noshow', action='store_true', help='if true then dont display graph, only show count')

# Parse arguments
args = parser.parse_args()
inFile = args.filename

# Set threshold for ROI definition
if args.threshold:
	threshold = float(args.threshold[0])
else:
	threshold = 0.95

# Set initial position
if args.center:
	xc, yc = args.center
else:
	xc, yc = 0, 0

# Set number of iterations
if args.n:
	n = int(args.n[0])
else:
	n = 100

# Parse input file
I, sigI, N, dataHeader, L = mc.extractMcStasData(inFile)

# Find extent from file header
extent = np.array(dataHeader['xylimits'].split(),dtype=float) 

# Calculate the spacing between values in the array
dx = (extent[1] - extent[0]) / (I.shape[1] - 1)
dy = (extent[3] - extent[2]) / (I.shape[0] - 1)

# Create the mask for the ROI
mask = np.zeros_like(I, dtype=bool)

# Find counts within mask
def find_counts_in_ROI(mask):
	# Apply the mask and calculate the sum within the ROI
	roi_sum = np.sum(I[mask])
	sum_err = np.sqrt(np.sum(np.square(I[mask]))) 

	return roi_sum, sum_err

# Determine where counts reach threshold% of maximum
def find_ROI_lim(counts_data, threshold):
	# counts_data is in the form (x, y, yerr) columns

	# Find max y value
	max_y = counts_data[-1, 1]

	# Find the x value where y is threshold% of max y
	threshold_value = threshold * max_y
	roi_x = None

	# Iterate through the data to find the x value where y is above the threshold
	for i in range(len(counts_data)):
		if counts_data[i, 1] >= threshold_value:
			roi_x = counts_data[i, 0]
			break

	return roi_x

if args.rect:
	w0, w1, h0, h1 = args.rect	# initial/ final width and height

	def rect_counts(x0, x1, y0, y1):
		# Rectangular ROI defined by 2 corners
		x_indices = np.where((x0 <= extent[0] + np.arange(I.shape[1]) * dx) & (extent[0] + np.arange(I.shape[1]) * dx < x1))
		y_indices = np.where((-y1 <= extent[2] + np.arange(I.shape[0]) * dy) & (extent[2] + np.arange(I.shape[0]) * dy < -y0))
	
		# Set the corresponding elements in the mask to True
		mask[y_indices[0][:, np.newaxis], x_indices[0]] = True

		# Find counts within ROI
		counts, counts_err = find_counts_in_ROI(mask)

		return counts, counts_err

	# Vary width over whole detector image 
	width_counts = []
	for w in np.linspace(w0, w1, n):
		x0, x1, y0, y1 = xc-w/2, xc+w/2, yc-h0/2, yc+h0/2 
		counts, counts_err = rect_counts(x0, x1, y0, y1)
		width_counts.append([w, counts, counts_err])


	# Vary height over whole detector image 
	height_counts = []
	for h in np.linspace(h0, h1, n):
		x0, x1, y0, y1 = xc-w0/2, xc+w0/2, yc-h/2, yc+h/2 
		counts, counts_err = rect_counts(x0, x1, y0, y1)
		height_counts.append([h, counts, counts_err])
	
	width_counts = np.array(width_counts)
	height_counts = np.array(height_counts)

	# Determine value where threshold% of counts reached
	best_width = find_ROI_lim(width_counts, threshold)
	best_height = find_ROI_lim(height_counts, threshold)
	print(f'{threshold*100}% Counts width: {best_width}')
	print(f'{threshold*100}% Counts height: {best_height}')

	# Show width and height determination 
	if (args.noshow==0):
		import matplotlib.pyplot as plt
		# Create a figure and two subplots side by side
		fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
		
		# Plot width data with error bars and vertical line at best_width
		ax1.errorbar(width_counts[:, 0], width_counts[:, 1], yerr=width_counts[:, 2], 
			capsize=2, fmt='o', label=f'Counts within area (Width x {h0}cm)')
		ax1.axvline(x=best_width, color='r', linestyle='--', label=f'{threshold*100}% Counts Width')
		ax1.set_title('Varying ROI Width')
		ax1.set_xlabel('ROI Width [cm]')
		ax1.set_ylabel('Counts within ROI')
		ax1.legend()
		
		# Plot height data with error bars and vertical line at best_height
		ax2.errorbar(height_counts[:, 0], height_counts[:, 1], yerr=height_counts[:, 2], 
			capsize=2, fmt='o', label=f'Counts within area ({w0}cm x Height)')
		ax2.axvline(x=best_height, color='r', linestyle='--', label=f'{threshold*100}% Counts Height')
		ax2.set_title('Varying ROI Height')
		ax2.set_xlabel('ROI Height [cm]')
		ax2.set_ylabel('Counts within ROI')
		ax2.legend()

		# Show the plot
		plt.show()

if args.circle:
	r0, r1 = args.circle	# initial/ final radius 

	def circle_counts(x0, x1, radius):
		# Circle ROI defined by center (x0, y0) and radius
		x_indices, y_indices = np.meshgrid(np.arange(I.shape[1]), np.arange(I.shape[0]))
		mask = ((extent[0] + x_indices * dx - x0) ** 2 + (extent[2] + y_indices * dy - y0) ** 2 <= radius ** 2)

		# Find counts within ROI
		counts, counts_err = find_counts_in_ROI(mask)

		return counts, counts_err

	# Vary radius over whole detector image 
	radius_counts = []
	for r in np.linspace(r0, r1, n):
		counts, counts_err = circle_counts(x0, x1, r)
		radius_counts.append([r, counts, counts_err])
	
	radius_counts = np.array(radius_counts)
	
	# Determine value where threshold% of counts reached
	best_radius = find_ROI_lim(radius_counts, threshold)
	print(f'{threshold*100}% Counts radius: {best_radius}')

	# Show radius determination
	if (args.noshow==0):
		import matplotlib.pyplot as plt
		# Create a figure and subplot 
		fig, ax = plt.subplots(1, 1, figsize=(6, 6))
		
		# Plot radius data with error bars and vertical line at best_radius
		ax.errorbar(radius_counts[:, 0], radius_counts[:, 1], yerr=radius_counts[:, 2], 
			capsize=2, fmt='o', label='Radius')
		ax.axvline(x=best_radius, color='r', linestyle='--', label=f'{threshold*100}% Counts Radius')
		ax.set_title('ROI Radius')
		ax.set_xlabel('ROI Radius [cm]')
		ax.set_ylabel('Counts within ROI')
		ax.legend()

		# Show the plot
		plt.show()

# Determine units
unit1 = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
unit2 = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])

if (args.noshow==0):
	import matplotlib.pyplot as plt
	from matplotlib.patches import Rectangle, Circle

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
	if args.rect:
		x0, x1, y0, y1 = xc-best_width/2, xc+best_width/2, yc-best_height/2, yc+best_height/2 
		square = Rectangle((x0, y0), (x1 - x0), (y1 - y0), fill=False, color='red', linewidth=2)
		ax.add_patch(square)
		roi_sum, sum_err = rect_counts(x0, x1, y0, y1)  
		roi_area = best_width*best_height 
		
	elif args.circle:
		circle = Circle((xc, yc), best_radius, fill=False, color='red', linewidth=2)
		ax.add_patch(circle)
		roi_sum, sum_err = circle_counts(xc, yc, best_radius)  
		roi_area = np.pi*best_radius**2

	else:	
		roi_sum, sum_err = 0
		roi_area = 0

	roi_info = f"Sum within ROI: {roi_sum:.2e} ± {sum_err:.2e}\n"
	roi_info += f"Area within ROI: {roi_area:.2e} [{unit1[0]}$\cdot${unit2[0]}]" 
	if args.circle:
		#roi_info += f"ROI: ({x0}, {y0}) [cm], r = {radius} [cm]" 
		roi_info += f"ROI: ({x0}, {y0}), r = {radius}" 
	print(roi_info)

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

