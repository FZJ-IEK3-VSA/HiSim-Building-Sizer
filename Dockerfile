FROM python

WORKDIR /app

# Install HDF5, which is required to build h5py during the installation of the requirements
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install libhdf5-serial-dev -y

# Copy source code to image
COPY . .
# Install building sizer
RUN pip install .

# Create a folder for the input files
RUN mkdir /input
# Create a folder for the result files
RUN mkdir /results

ENTRYPOINT python3 building_sizer/building_sizer_algorithm.py
