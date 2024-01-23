// Program to convert MNO_GPSANS output to McStas-compatible PSD N counts Image
// James Rogers, 1-11-2024

#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <algorithm>
#include <cmath>

struct GPSANSData {
	// output data available from MNO file decoding 
	std::string gps_time;
	double time;
	int id;
	int value;
	double x, y, z;
};

struct DetIDMap {
	int id;
	double scaling;
	double x, z;
};

// Read DetIDmap.csv into a vector of DetIDMap structs
std::vector<DetIDMap> load_DetIDMap_data(std::string& detIDmap) {
	std::string line;

	std::ifstream detIDMapFile(detIDmap);
	if (!detIDMapFile.is_open()) {
		throw std::runtime_error("Error opening DetIDmap file.");
	}

	std::vector<DetIDMap> detIDMapData;
	while (std::getline(detIDMapFile, line)) {
		// Skip lines starting with '#'
		if (line.empty() || line[0] == '#') {
			continue;
		}

		std::istringstream iss(line);
		DetIDMap detIDMap;

		// Use comma as the delimiter
		char comma; 
		if (!(iss >> detIDMap.id >> comma >> detIDMap.scaling >> comma >> detIDMap.x >> comma >> detIDMap.z)) {
			throw std::runtime_error("Error reading DetIDmap line: " + line);
		}
		detIDMapData.push_back(detIDMap);
	}
	
	return detIDMapData;
} 

int main(int argc, char** argv) {
	// Parse arguments
	if (argc != 5) {
		std::cerr << "Usage: " << argv[0] << " <inFile> <detIDmap> <outFile> <duration>" << std::endl;
		return 1;
	}

	std::string inFile(argv[1]);		// Input file should be MNO_GPSANS_######.dat
	std::string detIDmap(argv[2]);		// Det ID Map informs significance of each detector ID 
	std::string durationStr(argv[4]);	// Duration of run [s] found with ONCAT summary
	double duration = std::stoi(durationStr);

	// GP-SANS Detector Constants 
	double xwidth = 0.52525*2;
	double ywidth = 256*0.004086;
	int numBinsX = 196; 
	int numBinsY = 256; 

	double xmax =  xwidth/2.;
	double xmin =  -xwidth/2.;
	double ymax =  ywidth/2;
	double ymin =  -ywidth/2;
	double xbinSize = xwidth/ numBinsX;		// x bin Size [m]
	double ybinSize = ywidth/ numBinsY;		// y bin Size [m]

	// Create Counts histogram for given data
	std::vector<std::vector<double>> I_histogram(numBinsY, std::vector<double>(numBinsX, 0));
	std::vector<std::vector<int>> N_histogram(numBinsY, std::vector<int>(numBinsX, 0));

	// Load mapping from DetIDmap.csv
	std::vector<DetIDMap> detIDMapData;
	try {
		detIDMapData = load_DetIDMap_data(detIDmap); 
	} catch (const std::exception& e) {
		std::cerr << e.what() << std::endl;
		return 1;
	}

	// Open input file
	std::ifstream inputFile(inFile);
	std::string line;
	GPSANSData data;

	if (!inputFile.is_open()) {
		std::cerr << "Error opening input file!" << std::endl;
		return 1;
	}

	// Read run number from header 
	std::string runNumString; 
	if (std::getline(inputFile, line)) {
		// Extract run number from the line
		size_t pos = line.find("#MIRROR NEUTRON EVENT DATA - RUNNUM ");
		if (pos != std::string::npos) {
			runNumString = line.substr(pos + 36);
		}
	}
	int run_num = std::stoi(runNumString);
	// TODO read from ONCAT summary for run_num
	// TODO output_title
	// TODO zpos
	// TODO duration

	// Read input title from header and use for output title
	std::string output_title; 
	// Loop through lines until "#Title: " is found
	while (std::getline(inputFile, line)) {
		if (line.find("#Title: ") != std::string::npos) {
			// Found the line with "#Title: "
			// Extract the title from the line
			output_title = line.substr(line.find("#Title: ") + 8);
			break;  // Stop reading lines after finding the title
		}
	}

	// Read neutron data from the input file
	while (std::getline(inputFile, line)) {
		// Skip lines starting with '#'
		if (line.empty() || line[0] == '#') {
			continue;
		}

		std::istringstream iss(line);

		// Read line to "GPS time, relative time, detector ID, value"
		// Use comma as the delimiter
		char comma;
		if (!(iss >> data.gps_time >> comma >> data.time >> comma >> data.id >> comma >> data.value)) {
			std::cerr << "Error reading line: " << line << std::endl;
			continue;
		}

		// If Detector ID is of first plane, give z=-, if of second plane, give z=+
		// Lookup DetIDmap information based on data.id
		auto it = std::find_if(detIDMapData.begin(), detIDMapData.end(),
							   [data](const DetIDMap &detIDMap) { return detIDMap.id == data.id; });

		if (it != detIDMapData.end() && data.id <= 195) {
			// Set z position based on DetIDmap 
			data.z = it->z; 

			// Set x position based on DetIDmap
			data.x = it->x;

			// Set y position based on scaling and value
			data.y = data.value * it->scaling;

			// Determine x and y bin for detector image
			int xBin = static_cast<int>((data.x - xmin) / xbinSize);
			int yBin = static_cast<int>((data.y - ymin) / ybinSize);
			//int yBin = data.value;

			// Increment N counter
			N_histogram[yBin][xBin] ++;

		} else if (data.id > 195) {		// Ignore events not associated with GP-SANS detector tubes
			//std::cerr << "Warning: Ignoring event with ID " << data.id << " as it is greater than 195." << std::endl;

		} else {
			std::cerr << "Error: DetIDmap information not found for ID " << data.id << std::endl;
			continue;

		}

	}

	inputFile.close();


	// Output data to file
	std::ofstream outFile(argv[3]);

	if (!outFile.is_open()) {
		std::cerr << "Error opening output file!" << std::endl;
		return 1;
	}

	outFile << "# Format: GP-SANS Data Summary with McStas format" << std::endl;
	outFile << "# Instrument: CG-2" << std::endl;
	outFile << "# type: array_2d(" << numBinsX << ", " << numBinsY << ")" << std::endl;
	outFile << "# component: Histogram" << std::endl;
	outFile << "# position: 0 0 ?" << std::endl;
	outFile << "# title: " << output_title << std::endl;
	outFile << "# xvar: X" << std::endl;
	outFile << "# yvar: Y" << std::endl;
	outFile << "# xlabel: X position [cm]" << std::endl;
	outFile << "# ylabel: Y position [cm]" << std::endl;
	outFile << "# zvar: N" << std::endl;
	outFile << "# xylimits: " << 100*xmin << " " << 100*xmax << " " << 100*ymin << " " << 100*ymax << std::endl;

	// output dummy I array
	outFile << "# Data [] I:" << std::endl;
	for (int yBin = 0; yBin < numBinsY; ++yBin) {
		for (int xBin = 0; xBin < numBinsX; ++xBin) {
			outFile << N_histogram[yBin][xBin]/ duration << " ";
			//outFile << I_histogram[yBin][xBin] << " ";
		}
		outFile << std::endl;
	}

	// output dummy Ierr array
	outFile << "# Errors [] I_err:" << std::endl;
	for (int yBin = 0; yBin < numBinsY; ++yBin) {
		for (int xBin = 0; xBin < numBinsX; ++xBin) {
			outFile << pow(N_histogram[yBin][xBin],0.5)/ duration << " ";
		}
		outFile << std::endl;
	}

	// output N array
	outFile << "# Events [] N:" << std::endl;
	for (int yBin = 0; yBin < numBinsY; ++yBin) {
		for (int xBin = 0; xBin < numBinsX; ++xBin) {
			outFile << N_histogram[yBin][xBin] << " ";
		}
		outFile << std::endl;
	}

	outFile.close();

	return 0;
}

