# display evolution of beam profile through multiple time slices of instrument

import mcstasHelper as mc
import argparse
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image 
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import ScalarFormatter

def calculate_fwhm(x, y):
	max_index = np.argmax(y)
	x_max = x[max_index]
	y_max = y[max_index]

	half_max_y = y_max/2
	closest_index = np.argmin(np.abs(y - half_max_y))

	# Find left_idx where x is less than x_max
	filtered_y = y[:max_index]
	left_idx = np.argmin(np.abs(filtered_y - half_max_y))
	x_left = x[left_idx]
	#print(f'left: {x_left}')
	
	# Find right_idx where x is greater than x_max
	filtered_y = y[max_index:]
	right_idx = max_index + np.argmin(np.abs(filtered_y - half_max_y))
	x_right = x[right_idx]
	#print(f'right: {x_right}')

	fwhm = x_left - x_right
	return x_right, x_left, fwhm

def plot_data(filename, plot_type):
	I, sigI, N, dataHeader, L = mc.extractMcStasData(filename)

	# Call the mcstas2TIFF function to generate .tif files
	imN, imI, sigI = mc.mcstas2TIFF(filename, save=False)
	extent = np.array(dataHeader['xylimits'].split(),dtype=float)
	component = dataHeader['component']
		
	if dataHeader['type'][:8]=="array_2d":
		if plot_type == "full":
			# Set axis limits ax.set_xlim(extent[0], extent[1])
			ax.set_ylim(extent[2], extent[3])
		
			unit1 = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
			unit2 = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])
		
			# Calculate bin size
			dx = (extent[1] - extent[0]) / (np.array(imI).shape[1] - 1)
			dy = (extent[3] - extent[2]) / (np.array(imI).shape[0] - 1)
		
			plt.imshow(np.array(imI), extent=extent, cmap='plasma', vmin=overall_min, vmax=overall_max)
	
			cbar = plt.colorbar()
			cbar.set_label('Intensity [n/s]/ '+"{:.2e}".format(dx*dy)+' ['+unit1[0]+'*'+unit2[0]+']')
			formatter = ScalarFormatter(useMathText=True)
			formatter.set_powerlimits((-2,2))
			cbar.formatter = formatter
			cbar.update_ticks()
	
			plt.xlabel(dataHeader['xlabel'])
			plt.ylabel(dataHeader['ylabel'])
			plt.title(dataHeader['component']+"\npos=("+dataHeader['position']+")", pad=10)
		elif plot_type == "x":
			unit = re.findall(r"\[(.*?)\]", dataHeader['xlabel'])
			dx = (extent[1] - extent[0]) / np.array(imI).shape[1]
	
			# Generate X cross-section cross_section
			cross_section = np.sum(np.array(imI), axis=0)  # Sum along the horizontal axis
			err_cross_section = np.sqrt(np.sum(np.square(np.array(sigI)), axis=0))
	
			x = np.linspace(extent[0], extent[1], np.size(cross_section))
			plt.errorbar(x, cross_section, err_cross_section, capsize=2)

			# Calculate fwhm
			x_right, x_left, fwhm = calculate_fwhm(x, cross_section)
			print(f"{dataHeader['position']} {fwhm}")

			# Show fwhm
			plt.vlines(x=x_left, ymin=overall_min, ymax=overall_max, color='black', linestyle='--')
			plt.vlines(x=x_right, ymin=overall_min, ymax=overall_max, color='black', linestyle='--')

			plt.ylim(overall_min, overall_max)
			plt.xlabel(dataHeader['xlabel'])
			plt.ylabel('Intensity [n/s]/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
			plt.title("X Cross-Section: "+component+"\npos=("+dataHeader['position']+")", pad=10)
		elif plot_type == "y":
			unit = re.findall(r"\[(.*?)\]", dataHeader['ylabel'])
			dx = (extent[3] - extent[2]) / np.array(imI).shape[0]
	
			# Generate Y cross-section
			cross_section = np.sum(np.array(imI), axis=1)  # Sum along the horizontal axis
			err_cross_section = np.sqrt(np.sum(np.square(np.array(sigI)), axis=1))
	
			x = np.linspace(extent[3], extent[2], np.size(cross_section))
			plt.errorbar(x, cross_section, err_cross_section, capsize=2)

			# Calculate fwhm
			x_right, x_left, fwhm = calculate_fwhm(x, cross_section)
			print(f"{dataHeader['position']} {fwhm}")

			# Show fwhm
			plt.vlines(x=x_left, ymin=overall_min, ymax=overall_max, color='black', linestyle='--')
			plt.vlines(x=x_right, ymin=overall_min, ymax=overall_max, color='black', linestyle='--')

			plt.ylim(overall_min, overall_max)
			plt.xlim(extent[2], extent[3])
			plt.xlabel(dataHeader['ylabel'])
			plt.ylabel('Intensity [n/s]/ '+"{:.2e}".format(dx)+' ['+unit[0]+']')
			plt.title("Y Cross-Section: "+component+"\npos=("+dataHeader['position']+")", pad=10)
		else:
   			print("Invalid plot type. Please specify 'x', 'y', or 'full'.")

	else:
		print("Unknown Data Type.")

def update_image(frame, plot_type):
	# Clear the current plot
	plt.clf()

	# Get the filename corresponding to the current frame
	filename = filenames[frame]

	# Plot the data from the current file
	plot_data(filename, plot_type)

	# Pause the animation if the space bar is pressed
	if pause:
		animation.event_source.stop()

	# Convert the plot to an image
	fig.canvas.draw()
	frame_image = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())

	# Append the frame image to the list
	frames_list.append(frame_image)

# Function to handle key presses 
def on_key_press(event):
	global pause
	if event.key == ' ':
		pause = not pause
		if not pause:
			animation.event_source.start()

if __name__ == '__main__':
	# Argument parsing
	parser = argparse.ArgumentParser(description='Plot data from files as a video')
	parser.add_argument("plot_type", nargs="?", default="full", choices=["x", "y", "full"],
				help="Plot type: 'x', 'y', or 'full'")
	parser.add_argument('filenames', nargs='+', help='Input filenames (supports wildcard patterns)')
	parser.add_argument("--start_string", default="file_", help="String to isolate the number")
	parser.add_argument("--extension", default=".dat", help="File extension")
	parser.add_argument('--save', metavar='outFile', help='if provided, save video as GIF with specified output file name')
	args = parser.parse_args()

	start_string = args.start_string
	extension = args.extension

	# Expand wildcard patterns and get the list of all matching filenames
	filenames = []
	for pattern in args.filenames:
		filenames.extend(glob.glob(pattern))
	print(args.plot_type)

	# Sort the filenames alphabetically
	sorted_filenames = sorted(filenames, key=lambda filename: float(filename[len(start_string):-len(extension)]))
	sorted_filenames = [filename[:-len(extension)] for filename in sorted_filenames]

	filenames = [filename + extension for filename in sorted_filenames]

	print('sequence:\n', filenames)

	# Create the figure and axis for plotting
	fig, ax = plt.subplots()

	# Additional customization of the figure and axis, if needed

	# Calculate the overall minimum and maximum values
	overall_min = np.inf
	overall_max = -np.inf

	for filename in filenames:
		I, sigI, N, dataHeader, L = mc.extractMcStasData(filename)

		# if plot_type == "full":
		dataset = np.copy(I)
		if args.plot_type == "x":
			dataset = np.sum(np.array(I), axis=0)  # Sum along the horizontal axis
		elif args.plot_type == "y":
			dataset = np.sum(np.array(I), axis=1)  # Sum along the vertical axis
		dataset_min = np.min(dataset)
		dataset_max = np.max(dataset)

		overall_min = min(overall_min, dataset_min)
		overall_max = max(overall_max, dataset_max)
	
	# Plot the first dataset to initialize the colorbar
	plot_data(filenames[0], args.plot_type)

	# Create the animation
	if args.save is not None:	# if saving gif, dont repeat
		repeat = False
	else:						# if not saving gif, repeat
		repeat = True

	#animation = FuncAnimation(fig, update_image, frames=len(filenames), interval=300, repeat=repeat)
	animation = FuncAnimation(fig, update_image, fargs=(args.plot_type,), frames=len(filenames), interval=300)#, repeat=repeat)

	# Create a list to store the individual frames
	frames_list = []

	# Pause flag to control animation state
	pause = False

	# Connect the key press event handler
	fig.canvas.mpl_connect('key_press_event', on_key_press)

	# Display the animation
	plt.show()

if args.save is not None: 
	outFile = args.save
	if outFile:
		frames_list[0].save(outFile, format='GIF', append_images=frames_list[1:], save_all=True, duration=100)
	else:
		print("Please provide an output file name when using the '--save' argument.")
