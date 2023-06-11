# display evolution of beam profile through multiple time slices of instrument

import mcstasHelper as mc

import argparse
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def plot_data(filename):
	I, sigI, N, dataHeader, L = mc.extractMcStasData(filename)

	if dataHeader['type'][:8]=="array_2d":
		extent = np.array(dataHeader['xylimits'].split(),dtype=float)
	
		# Call the mcstas2TIFF function to generate .tif files
		imN, imI, sigI = mc.mcstas2TIFF(filename, save=False)
	
		# Set axis limits
		ax.set_xlim(extent[0], extent[1])
		ax.set_ylim(extent[2], extent[3])
	
		unit1 = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
		unit2 = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])
	
		# Calculate bin size
		dx = (extent[1] - extent[0]) / (np.array(imI).shape[1] - 1)
		dy = (extent[3] - extent[2]) / (np.array(imI).shape[0] - 1)
	
		plt.imshow(np.array(imI), extent=extent, cmap='plasma', vmin=overall_min, vmax=overall_max)
		plt.colorbar().set_label('Intensity [n/s]/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
		plt.xlabel(dataHeader['xlabel'])
		plt.ylabel(dataHeader['ylabel'])
		plt.title(dataHeader['component']+"\npos="+dataHeader['position'], pad=10)

	else:
		print("Unknown Data Type.")

def animate(frame):
	# Clear the current plot
	plt.clf()

	# Get the filename corresponding to the current frame
	filename = filenames[frame]

	# Plot the data from the current file
	plot_data(filename)

	# Add any additional styling, labels, titles, etc.

	return

if __name__ == '__main__':
	# Argument parsing
	parser = argparse.ArgumentParser(description='Plot data from files as a video')
	parser.add_argument('filenames', nargs='+', help='Input filenames (supports wildcard patterns)')
	args = parser.parse_args()

	# Expand wildcard patterns and get the list of all matching filenames
	filenames = []
	for pattern in args.filenames:
		filenames.extend(glob.glob(pattern))

	# Sort the filenames alphabetically
	filenames = sorted(filenames)
	print('sequence:\n', filenames)

	# Create the figure and axis for plotting
	fig, ax = plt.subplots()

	# Additional customization of the figure and axis, if needed

	# Calculate the overall minimum and maximum values
	overall_min = np.inf
	overall_max = -np.inf

	for filename in filenames:
		I, sigI, N, dataHeader, L = mc.extractMcStasData(filename)

		dataset_min = np.min(I)
		dataset_max = np.max(I)

		overall_min = min(overall_min, dataset_min)
		overall_max = max(overall_max, dataset_max)
	
	# Plot the first dataset to initialize the colorbar
	plot_data(filenames[0])

	# Create the animation
	animation = FuncAnimation(fig, animate, frames=len(filenames), interval=600, repeat=True)

	# Display the animation
	plt.show()

