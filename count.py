import numpy as np
import mcstasHelper as mc
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import argparse

parser = argparse.ArgumentParser(description='Process MCStas data and extract ROI.')
parser.add_argument('filename', type=str, help='MCStas data filename')
parser.add_argument('--square', nargs=4, type=float, metavar=('x0', 'x1', 'y0', 'y1'),
					help='Square ROI limits: x0 x1 y0 y1')
parser.add_argument('--circle', nargs=3, type=float, metavar=('x0', 'y0', 'radius'),
					help='Circular ROI limits: x0 y0 radius')

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

if args.square:
	x0, x1, y0, y1 = args.square

	# Square ROI defined by 2 corners
	x_indices = np.where((x0 <= extent[0] + np.arange(I.shape[1]) * dx) & (extent[0] + np.arange(I.shape[1]) * dx < x1))
	y_indices = np.where((-y1 <= extent[2] + np.arange(I.shape[0]) * dy) & (extent[2] + np.arange(I.shape[0]) * dy < -y0))

	# Set the corresponding elements in the mask to True
	mask[y_indices[0][:, np.newaxis], x_indices[0]] = True

if args.circle:
	x0, y0, radius = args.circle

	# Circle ROI defined by center (x0, y0) and radius
	x_indices, y_indices = np.meshgrid(np.arange(I.shape[1]), np.arange(I.shape[0]))
	mask = ((extent[0] + x_indices * dx - x0) ** 2 + (extent[2] + y_indices * dy - y0) ** 2 <= radius ** 2)

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

# Apply the mask and calculate the sum within the ROI
roi_sum = np.sum(I[mask])
sum_err = np.sqrt(np.sum(np.square(I[mask]))) 

print("\nSum within ROI: ", "{:.2e}".format(roi_sum), " ± ", "{:.2e}".format(sum_err)) 

# Show data with mask outlined
fig, ax = plt.subplots()

img = ax.imshow(I, extent=extent, cmap='plasma')
ax.set_title(dataHeader['component'])
ax.set_xlabel(dataHeader['xlabel'])
ax.set_ylabel(dataHeader['ylabel'])
cbar = fig.colorbar(img, ax=ax)
cbar.set_label(dataHeader['zvar'])

# Add patch for ROI outline on plot
if args.square:
	square = Rectangle((x0, y0), (x1 - x0), (y1 - y0), fill=False, color='red', linewidth=2)
	ax.add_patch(square)
if args.circle:
	circle = Circle((x0, y0), radius, fill=False, color='red', linewidth=2)
	ax.add_patch(circle)

plt.show()
