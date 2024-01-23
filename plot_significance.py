# Plot parameter output values, then find parameter tolerances by slope
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Define fontsize
fontsize = 14

# Load dataset into pandas df
df = pd.read_csv('param_scan_output.csv')

# Baseline configuration
baseline_config = [10.0, 0.5, 4.0, 0.0005, -0.3, -0.1]

# Function to find unique values for each parameter
def get_unique_values(parameter_name):
	unique_values = df[parameter_name].unique()
	unique_values = [val for val in unique_values if val != baseline_config[df.columns.get_loc(parameter_name)]]
	return unique_values

# Manually input baseline output and error
baseline_output = 305187780	
baseline_output_err = 4241558.33860592

# Function to create individual plots for each parameter
def plot_variation(ax, parameter_vals_unique, parameter_name, parameter_unit):
	# Get parameter baseline index to avoid double showing baseline
	baseline_index = df.columns.get_loc(parameter_name)
	baseline_value = baseline_config[baseline_index]

	param_vals = []
	out_vals = []
	out_vals_err = []

	#print(parameter_name)
	for param_val in parameter_vals_unique:

		# Show output with no VB separately
		if param_val == 'no vb': 
			no_vb_line = df[df[parameter_name] == param_val]
			no_vb_val = float(no_vb_line['target sum'].values[0])
			no_vb_val_err = float(no_vb_line['target err'].values[0])	

		# If param_val is the baseline value, other runs will have duplicates. Show only the baseline value
		elif float(param_val) == float(baseline_value):
			baseline_line = df[df[parameter_name] == param_val]

			param_vals.append(float(param_val))
			out_vals.append(baseline_output)
			out_vals_err.append(baseline_output_err)

		# Find unique parameter values
		else:	 
			subset_df = df[df[parameter_name] == param_val]

			param_vals.append(float(param_val))
			out_vals.append(float(subset_df['target sum'].values[0]))
			out_vals_err.append(float(subset_df['target err'].values[0]))

	# Plot datapoints with error bars
	ax.errorbar(param_vals, out_vals, yerr=out_vals_err, 
			fmt=' ', marker='o', markersize=6, capsize=5, linewidth=3, 
			label='Data Points')
	
	# Plot horizontal line at no_vb_val
	ax.axhline(y=no_vb_val, 
			linestyle='--', color='red', label=f'No VB FoM = {no_vb_val:.2e} $n \cdot s^2$')
	ax.axhspan(ymin=no_vb_val - no_vb_val_err, ymax=no_vb_val + no_vb_val_err, 
			color='red', alpha=0.2)
	
	# Plot vertical line at param_val (baseline_value)
	ax.axvline(baseline_value,
			linestyle='--', color='black',
			label=f'Baseline configuration:\n{parameter_name}={float(baseline_value)}')

	ax.set_xlabel(f'{parameter_name} [{parameter_unit}]', fontsize=fontsize)
	ax.set_ylabel('Target Sum [$n \cdot s^2$]', fontsize=fontsize)
	ax.set_title(f'Variation of Target Sum with {parameter_name}', fontsize=fontsize)
	ax.legend(loc='lower right', fontsize=fontsize-4)

# Create a single figure with subplots
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.subplots_adjust(hspace=0.3, wspace=0.2)

# Get unique values for each parameter
VB_pos_vals_unique = get_unique_values('VB_pos')
VB_length_vals_unique = get_unique_values('VB_length')
VB_m_vals_unique = get_unique_values('VB_m')
VB_thickness_vals_unique = get_unique_values('VB_thickness')

# Create plots for each parameter
plot_variation(axs[0,0], VB_pos_vals_unique, 'VB_pos', 'm')
plot_variation(axs[0,1], VB_length_vals_unique, 'VB_length', 'm')
plot_variation(axs[1,0], VB_m_vals_unique, 'VB_m', '1')
plot_variation(axs[1,1], VB_thickness_vals_unique, 'VB_thickness', 'm')

#plt.tight_layout()
plt.show()
