# Example of Accessing Data Cubes via STAC

This repository contains a practical example of how to access and download geospatial data from a STAC (SpatioTemporal Asset Catalog) catalog using Python. The notebook (datacube_requirement.ipynb) demonstrates a robust workflow for downloading pairs of images (orthophotos and LiDAR data) for each cell of a vector grid, saving them as GeoTIFF files.

This project was developed to demonstrate how to access data cubes from the Cuborizonte platform (example URL: http://aqui.io/cuborizonte/catalogo/stac).

The UODC implementation can be found at https://github.com/DiegoHMM/cuborizonte.


## ⚙️ How It Works

The workflow is orchestrated by the notebook and uses functions defined in src/utils.py. The process can be divided into the following steps:

1.  **Configuration**: All parameters, such as file paths, the STAC catalog URL, collection names, bands, and time periods, are defined at the beginning of the notebook.

2.  **Bounding Box Generation (Optional)**: The create_bbox_list_from_shapefile function reads the grid/grid_bh.shp, calculates the centroid of each polygon (grid cell), and creates a small Bounding Box around each one. This ensures that the search in the STAC catalog is performed for a well-defined area of interest.

3.  **Checkpoint Loading**: Before starting, the script checks for the existence of the processing_checkpoint.json file. If it exists, the script loads the list of grids that have already been successfully processed or have failed, avoiding unnecessary reprocessing.

4.  **Processing Loop**: The script iterates over each BBox generated in step 2.
    - **Skips Completed Cells**: If the current cell ID is already in the completed list, it is skipped.
    - **Data Fetching (X and Y)**: For each cell, the get_datacube function is called twice:
        - Once to fetch the input data (Orthophoto, X_CONFIG).
        - Another to fetch the target data (LiDAR, Y_CONFIG).
        - The function uses pystac_client to search the catalog and odc.stac.load to load the found items as an xarray datacube.
    - **Processing and Saving**: The process_and_save_datacube function receives the xarray datacube, selects the first time slice, and saves it as a GeoTIFF file in the corresponding output directory (data/X/ or data/y/) using rioxarray.

5.  **Checkpoint Update**: At the end of each loop iteration, the state is updated:
    - If both the X and Y files were saved successfully, the cell ID is added to the completed list.
    - If either one failed, the ID is added to the failed list.
    - The processing_checkpoint.json file is saved immediately, ensuring that progress is not lost.

6.  **Final Report**: At the end of the process, a summary is displayed with the total number of successfully processed grids and the total number of failures.

## Parameters

- **GRID_SHAPEFILE**: Ensure the path to your shapefile is correct.
- **CATALOG_URL**: Enter the URL of the STAC catalog you want to access.
- **X_CONFIG e Y_CONFIG**: Adjust the product names (product_name), bands (bands), and time interval (time_interval) for the collections you wish to download.